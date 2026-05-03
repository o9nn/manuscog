"""
OpenCog Inferno AGI - Probabilistic Logic Networks (PLN) Engine
===============================================================

PLN is the primary reasoning system for the cognitive kernel.
It implements probabilistic inference over the AtomSpace hypergraph,
supporting various inference types:
- Deduction: A->B, B->C => A->C
- Induction: A->B, A->C => B->C  
- Abduction: A->B, C->B => A->C
- Modus Ponens: A, A->B => B
- Revision: Merge evidence from multiple sources

PLN operates as a kernel-level service, providing reasoning
capabilities to all cognitive processes.
"""

from __future__ import annotations
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
import threading
import time
import math
from collections import defaultdict
import heapq

from kernel.cognitive.types import (
    Atom, Node, Link, AtomHandle, AtomType,
    TruthValue, AttentionValue, InferenceType, InferenceResult,
    ReasoningService, CognitiveContext
)
from atomspace.hypergraph.atomspace import AtomSpace


# =============================================================================
# PLN CONFIGURATION
# =============================================================================

@dataclass
class PLNConfig:
    """Configuration for the PLN reasoning engine."""
    max_depth: int = 10
    timeout: float = 5.0
    confidence_threshold: float = 0.1
    strength_threshold: float = 0.1
    max_results: int = 100


# =============================================================================
# PLN FORMULAS
# =============================================================================

class PLNFormulas:
    """
    Collection of PLN inference formulas.
    These implement the mathematical foundations of probabilistic reasoning.
    """
    
    # Default prior probability
    DEFAULT_PRIOR = 0.5
    
    # Confidence decay factor for multi-step inference
    CONFIDENCE_DECAY = 0.9
    
    @staticmethod
    def strength_to_count(strength: float, confidence: float, k: float = 1.0) -> float:
        """Convert strength and confidence to evidence count."""
        if confidence >= 1.0:
            return float('inf')
        return k * confidence / (1 - confidence)
    
    @staticmethod
    def count_to_confidence(count: float, k: float = 1.0) -> float:
        """Convert evidence count to confidence."""
        return count / (count + k)
    
    @staticmethod
    def revision(tv1: TruthValue, tv2: TruthValue) -> TruthValue:
        """
        Revision formula: Merge two truth values from independent sources.
        
        This is used when we have two pieces of evidence about the same
        proposition from independent sources.
        """
        # Convert to counts
        n1 = PLNFormulas.strength_to_count(tv1.strength, tv1.confidence)
        n2 = PLNFormulas.strength_to_count(tv2.strength, tv2.confidence)
        
        if n1 + n2 == 0:
            return TruthValue(0.5, 0.0, 0.0)
        
        # Weighted average
        new_strength = (tv1.strength * n1 + tv2.strength * n2) / (n1 + n2)
        new_count = n1 + n2
        new_confidence = PLNFormulas.count_to_confidence(new_count)
        
        return TruthValue(new_strength, new_confidence, new_count)
    
    @staticmethod
    def deduction(
        tv_ab: TruthValue,  # A -> B
        tv_bc: TruthValue,  # B -> C
        tv_b: TruthValue = None,  # B (optional prior)
        tv_c: TruthValue = None   # C (optional prior)
    ) -> TruthValue:
        """
        Deduction formula: A->B, B->C => A->C
        
        P(C|A) = P(C|B) * P(B|A) + P(C|~B) * P(~B|A)
        
        Simplified when we don't have P(C|~B):
        P(C|A) ≈ P(C|B) * P(B|A)
        """
        sAB, cAB = tv_ab.strength, tv_ab.confidence
        sBC, cBC = tv_bc.strength, tv_bc.confidence
        
        # Get priors or use defaults
        sB = tv_b.strength if tv_b else PLNFormulas.DEFAULT_PRIOR
        sC = tv_c.strength if tv_c else PLNFormulas.DEFAULT_PRIOR
        
        # Deduction formula
        # P(C|A) = P(C|B)*P(B|A) + P(C|~B)*P(~B|A)
        # Assuming independence: P(C|~B) ≈ P(C)
        sAC = sAB * sBC + (1 - sAB) * sC
        
        # Confidence is product of input confidences, decayed
        cAC = cAB * cBC * PLNFormulas.CONFIDENCE_DECAY
        
        # Adjust confidence based on strength (low strength = less certain)
        cAC *= min(sAB, sBC, 1.0)
        
        return TruthValue(sAC, cAC, min(tv_ab.count, tv_bc.count))
    
    @staticmethod
    def induction(
        tv_ab: TruthValue,  # A -> B
        tv_ac: TruthValue,  # A -> C
        tv_a: TruthValue = None,  # A (optional prior)
        tv_b: TruthValue = None,  # B (optional prior)
        tv_c: TruthValue = None   # C (optional prior)
    ) -> TruthValue:
        """
        Induction formula: A->B, A->C => B->C
        
        This infers a relationship between B and C based on their
        common relationship with A.
        """
        sAB, cAB = tv_ab.strength, tv_ab.confidence
        sAC, cAC = tv_ac.strength, tv_ac.confidence
        
        # Get priors
        sA = tv_a.strength if tv_a else PLNFormulas.DEFAULT_PRIOR
        sB = tv_b.strength if tv_b else PLNFormulas.DEFAULT_PRIOR
        sC = tv_c.strength if tv_c else PLNFormulas.DEFAULT_PRIOR
        
        # Induction formula (simplified)
        # P(C|B) = P(C|A)*P(A|B) + P(C|~A)*P(~A|B)
        # Using Bayes: P(A|B) = P(B|A)*P(A)/P(B)
        
        if sB < 0.0001:
            return TruthValue(sC, 0.0, 0.0)
        
        sAgivenB = sAB * sA / sB  # Approximate P(A|B)
        sAgivenB = min(1.0, sAgivenB)
        
        sBC = sAC * sAgivenB + sC * (1 - sAgivenB)
        
        # Confidence is lower for induction (less certain)
        cBC = cAB * cAC * sA * PLNFormulas.CONFIDENCE_DECAY * 0.8
        
        return TruthValue(sBC, cBC, min(tv_ab.count, tv_ac.count))
    
    @staticmethod
    def abduction(
        tv_ab: TruthValue,  # A -> B
        tv_cb: TruthValue,  # C -> B
        tv_a: TruthValue = None,
        tv_b: TruthValue = None,
        tv_c: TruthValue = None
    ) -> TruthValue:
        """
        Abduction formula: A->B, C->B => A->C
        
        This infers a relationship between A and C based on their
        common consequence B.
        """
        sAB, cAB = tv_ab.strength, tv_ab.confidence
        sCB, cCB = tv_cb.strength, tv_cb.confidence
        
        # Get priors
        sA = tv_a.strength if tv_a else PLNFormulas.DEFAULT_PRIOR
        sB = tv_b.strength if tv_b else PLNFormulas.DEFAULT_PRIOR
        sC = tv_c.strength if tv_c else PLNFormulas.DEFAULT_PRIOR
        
        # Abduction formula (simplified)
        # P(C|A) based on common effect B
        
        if sB < 0.0001:
            return TruthValue(sC, 0.0, 0.0)
        
        # Both A and C lead to B, so they might be related
        sAC = (sAB * sCB) / sB + sC * (1 - sAB)
        sAC = min(1.0, sAC)
        
        # Abduction has lowest confidence
        cAC = cAB * cCB * sB * PLNFormulas.CONFIDENCE_DECAY * 0.6
        
        return TruthValue(sAC, cAC, min(tv_ab.count, tv_cb.count))
    
    @staticmethod
    def modus_ponens(
        tv_a: TruthValue,   # A
        tv_ab: TruthValue   # A -> B
    ) -> TruthValue:
        """
        Modus Ponens: A, A->B => B
        
        If A is true and A implies B, then B is true.
        """
        sA, cA = tv_a.strength, tv_a.confidence
        sAB, cAB = tv_ab.strength, tv_ab.confidence
        
        # P(B) = P(B|A)*P(A) + P(B|~A)*P(~A)
        # Assuming P(B|~A) is low:
        sB = sA * sAB
        
        cB = cA * cAB * PLNFormulas.CONFIDENCE_DECAY
        
        return TruthValue(sB, cB, min(tv_a.count, tv_ab.count))
    
    @staticmethod
    def negation(tv: TruthValue) -> TruthValue:
        """Negation: NOT A"""
        return TruthValue(
            1.0 - tv.strength,
            tv.confidence,
            tv.count
        )
    
    @staticmethod
    def conjunction(tv1: TruthValue, tv2: TruthValue) -> TruthValue:
        """Conjunction: A AND B (assuming independence)"""
        s = tv1.strength * tv2.strength
        c = tv1.confidence * tv2.confidence
        return TruthValue(s, c, min(tv1.count, tv2.count))
    
    @staticmethod
    def disjunction(tv1: TruthValue, tv2: TruthValue) -> TruthValue:
        """Disjunction: A OR B (assuming independence)"""
        s = tv1.strength + tv2.strength - tv1.strength * tv2.strength
        c = tv1.confidence * tv2.confidence
        return TruthValue(s, c, min(tv1.count, tv2.count))
    
    @staticmethod
    def similarity_to_inheritance(tv_sim: TruthValue) -> TruthValue:
        """Convert similarity to inheritance."""
        # Similarity is symmetric, inheritance is not
        # P(B|A) from Sim(A,B) - use geometric mean approximation
        s = math.sqrt(tv_sim.strength)
        c = tv_sim.confidence * 0.9
        return TruthValue(s, c, tv_sim.count)


# =============================================================================
# INFERENCE RULES
# =============================================================================

@dataclass
class InferenceRule:
    """Definition of an inference rule."""
    name: str
    inference_type: InferenceType
    input_types: List[AtomType]  # Required input link types
    output_type: AtomType        # Output link type
    formula: Callable[..., TruthValue]
    priority: float = 1.0
    
    def __hash__(self):
        return hash(self.name)


class InferenceRuleSet:
    """Collection of inference rules."""
    
    def __init__(self):
        self.rules: Dict[str, InferenceRule] = {}
        self._setup_default_rules()
    
    def _setup_default_rules(self):
        """Setup default PLN inference rules."""
        
        # Deduction rule
        self.add_rule(InferenceRule(
            name="deduction",
            inference_type=InferenceType.DEDUCTION,
            input_types=[AtomType.INHERITANCE_LINK, AtomType.INHERITANCE_LINK],
            output_type=AtomType.INHERITANCE_LINK,
            formula=PLNFormulas.deduction,
            priority=1.0
        ))
        
        # Induction rule
        self.add_rule(InferenceRule(
            name="induction",
            inference_type=InferenceType.INDUCTION,
            input_types=[AtomType.INHERITANCE_LINK, AtomType.INHERITANCE_LINK],
            output_type=AtomType.INHERITANCE_LINK,
            formula=PLNFormulas.induction,
            priority=0.8
        ))
        
        # Abduction rule
        self.add_rule(InferenceRule(
            name="abduction",
            inference_type=InferenceType.ABDUCTION,
            input_types=[AtomType.INHERITANCE_LINK, AtomType.INHERITANCE_LINK],
            output_type=AtomType.INHERITANCE_LINK,
            formula=PLNFormulas.abduction,
            priority=0.6
        ))
        
        # Modus Ponens rule
        self.add_rule(InferenceRule(
            name="modus_ponens",
            inference_type=InferenceType.MODUS_PONENS,
            input_types=[AtomType.CONCEPT_NODE, AtomType.IMPLICATION_LINK],
            output_type=AtomType.CONCEPT_NODE,
            formula=PLNFormulas.modus_ponens,
            priority=1.0
        ))
        
        # Revision rule
        self.add_rule(InferenceRule(
            name="revision",
            inference_type=InferenceType.REVISION,
            input_types=[],  # Any matching atoms
            output_type=None,  # Same as input
            formula=PLNFormulas.revision,
            priority=1.0
        ))
    
    def add_rule(self, rule: InferenceRule):
        """Add an inference rule."""
        self.rules[rule.name] = rule
    
    def get_rule(self, name: str) -> Optional[InferenceRule]:
        """Get a rule by name."""
        return self.rules.get(name)
    
    def get_applicable_rules(
        self,
        input_types: List[AtomType]
    ) -> List[InferenceRule]:
        """Get rules applicable to given input types."""
        applicable = []
        for rule in self.rules.values():
            if self._types_match(rule.input_types, input_types):
                applicable.append(rule)
        return sorted(applicable, key=lambda r: -r.priority)
    
    def _types_match(
        self,
        rule_types: List[AtomType],
        input_types: List[AtomType]
    ) -> bool:
        """Check if input types match rule requirements."""
        if not rule_types:  # Empty means any
            return True
        if len(rule_types) != len(input_types):
            return False
        return all(rt == it for rt, it in zip(rule_types, input_types))


# =============================================================================
# INFERENCE CONTROL
# =============================================================================

@dataclass
class InferenceTask:
    """A task in the inference queue."""
    premises: List[AtomHandle]
    rule: InferenceRule
    priority: float
    created_at: float = field(default_factory=time.time)
    attempts: int = 0
    
    def __lt__(self, other):
        return self.priority > other.priority  # Higher priority first


class InferenceController:
    """
    Controls the inference process using attention-based selection.
    
    The controller manages:
    - Selection of premises for inference
    - Application of inference rules
    - Resource allocation for reasoning
    """
    
    def __init__(
        self,
        atomspace: AtomSpace,
        rule_set: InferenceRuleSet,
        max_queue_size: int = 10000
    ):
        self.atomspace = atomspace
        self.rule_set = rule_set
        self.max_queue_size = max_queue_size
        
        # Inference queue (priority queue)
        self._queue: List[InferenceTask] = []
        self._lock = threading.Lock()
        
        # Statistics
        self.stats = {
            'inferences_attempted': 0,
            'inferences_successful': 0,
            'inferences_failed': 0,
            'rules_applied': defaultdict(int)
        }
    
    def add_task(self, task: InferenceTask):
        """Add an inference task to the queue."""
        with self._lock:
            if len(self._queue) < self.max_queue_size:
                heapq.heappush(self._queue, task)
    
    def get_next_task(self) -> Optional[InferenceTask]:
        """Get the next inference task."""
        with self._lock:
            if self._queue:
                return heapq.heappop(self._queue)
            return None
    
    def find_deduction_premises(self) -> List[Tuple[Link, Link]]:
        """Find pairs of inheritance links suitable for deduction."""
        premises = []
        
        # Get all inheritance links
        inheritance_links = self.atomspace.get_atoms_by_type(
            AtomType.INHERITANCE_LINK
        )
        
        # Build index: target -> links
        target_index: Dict[AtomHandle, List[Link]] = defaultdict(list)
        for link in inheritance_links:
            if isinstance(link, Link) and len(link.outgoing) >= 2:
                target = link.outgoing[1]  # B in A->B
                target_index[target].append(link)
        
        # Find chains: A->B, B->C
        for link_ab in inheritance_links:
            if not isinstance(link_ab, Link) or len(link_ab.outgoing) < 2:
                continue
            
            b_handle = link_ab.outgoing[1]  # B
            
            # Find links where B is the source
            for link_bc in self.atomspace.get_incoming(b_handle):
                if (isinstance(link_bc, Link) and 
                    link_bc.atom_type == AtomType.INHERITANCE_LINK and
                    len(link_bc.outgoing) >= 2 and
                    link_bc.outgoing[0] == b_handle):
                    premises.append((link_ab, link_bc))
        
        return premises
    
    def find_induction_premises(self) -> List[Tuple[Link, Link]]:
        """Find pairs of inheritance links suitable for induction."""
        premises = []
        
        inheritance_links = self.atomspace.get_atoms_by_type(
            AtomType.INHERITANCE_LINK
        )
        
        # Build index: source -> links
        source_index: Dict[AtomHandle, List[Link]] = defaultdict(list)
        for link in inheritance_links:
            if isinstance(link, Link) and len(link.outgoing) >= 2:
                source = link.outgoing[0]  # A in A->B
                source_index[source].append(link)
        
        # Find pairs with common source: A->B, A->C
        for source, links in source_index.items():
            if len(links) >= 2:
                for i, link_ab in enumerate(links):
                    for link_ac in links[i+1:]:
                        premises.append((link_ab, link_ac))
        
        return premises
    
    def select_premises_by_attention(
        self,
        candidates: List[Tuple[Link, Link]],
        limit: int = 10
    ) -> List[Tuple[Link, Link]]:
        """Select premises based on attention values."""
        if not candidates:
            return []
        
        # Score each pair by combined attention
        scored = []
        for link1, link2 in candidates:
            score = (link1.attention_value.sti + link2.attention_value.sti +
                    link1.truth_value.confidence + link2.truth_value.confidence)
            scored.append((score, link1, link2))
        
        # Sort by score and return top candidates
        scored.sort(reverse=True, key=lambda x: x[0])
        return [(link1, link2) for _, link1, link2 in scored[:limit]]


# =============================================================================
# PLN REASONING ENGINE
# =============================================================================

class PLNEngine(ReasoningService):
    """
    Probabilistic Logic Networks reasoning engine.
    
    This is the main reasoning service for the cognitive kernel,
    implementing probabilistic inference over the AtomSpace.
    """
    
    def __init__(
        self,
        atomspace: AtomSpace,
        config_or_depth = None,
        min_confidence_threshold: float = 0.01
    ):
        self.atomspace = atomspace
        
        # Handle both PLNConfig and int for backwards compatibility
        if isinstance(config_or_depth, PLNConfig):
            self.config = config_or_depth
            self.max_inference_depth = config_or_depth.max_depth
            self.min_confidence_threshold = config_or_depth.confidence_threshold
        else:
            self.max_inference_depth = config_or_depth if config_or_depth is not None else 5
            self.min_confidence_threshold = min_confidence_threshold
            self.config = PLNConfig(max_depth=self.max_inference_depth)
        
        # Rule set
        self.rule_set = InferenceRuleSet()
        
        # Inference controller
        self.controller = InferenceController(atomspace, self.rule_set)
        
        # Service state
        self._running = False
        self._inference_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        
        # Inference history (for avoiding redundant inferences)
        self._inference_history: Set[str] = set()
        self._history_max_size = 100000
        
        # Statistics
        self.stats = {
            'total_inferences': 0,
            'successful_inferences': 0,
            'new_atoms_created': 0,
            'atoms_strengthened': 0
        }
    
    # =========================================================================
    # SERVICE INTERFACE
    # =========================================================================
    
    @property
    def service_name(self) -> str:
        return "pln_reasoning_engine"
    
    def start(self) -> bool:
        """Start the reasoning service."""
        if self._running:
            return False
        
        self._running = True
        self._inference_thread = threading.Thread(
            target=self._inference_loop,
            daemon=True,
            name="pln-inference"
        )
        self._inference_thread.start()
        return True
    
    def stop(self) -> bool:
        """Stop the reasoning service."""
        if not self._running:
            return False
        
        self._running = False
        if self._inference_thread:
            self._inference_thread.join(timeout=2.0)
        return True
    
    def status(self) -> Dict[str, Any]:
        """Get service status."""
        return {
            'running': self._running,
            'stats': self.stats.copy(),
            'queue_size': len(self.controller._queue),
            'history_size': len(self._inference_history)
        }
    
    # =========================================================================
    # REASONING SERVICE INTERFACE
    # =========================================================================
    
    def infer(
        self,
        premises: List[AtomHandle],
        inference_type: InferenceType
    ) -> Optional[InferenceResult]:
        """Perform a single inference step."""
        if len(premises) < 1:
            return None
        
        # Get atoms
        atoms = [self.atomspace.get_atom(h) for h in premises]
        if None in atoms:
            return None
        
        # Select appropriate rule
        input_types = [a.atom_type for a in atoms]
        rules = self.rule_set.get_applicable_rules(input_types)
        
        if not rules:
            return None
        
        rule = rules[0]  # Use highest priority rule
        
        # Apply inference
        return self._apply_inference(atoms, rule, inference_type)
    
    def query(self, pattern: Atom) -> List[Dict[str, AtomHandle]]:
        """Query the knowledge base with a pattern."""
        # Delegate to pattern matcher (implemented separately)
        return []
    
    # =========================================================================
    # INFERENCE OPERATIONS
    # =========================================================================
    
    def deduction(
        self,
        link_ab: Link,
        link_bc: Link
    ) -> Optional[InferenceResult]:
        """
        Perform deduction: A->B, B->C => A->C
        """
        if not self._validate_chain(link_ab, link_bc):
            return None
        
        # Check inference history
        history_key = f"ded:{link_ab.handle.uuid}:{link_bc.handle.uuid}"
        if history_key in self._inference_history:
            return None
        
        # Get A, B, C
        a_handle = link_ab.outgoing[0]
        b_handle = link_ab.outgoing[1]
        c_handle = link_bc.outgoing[1]
        
        # Skip if A == C (trivial)
        if a_handle == c_handle:
            return None
        
        # Apply deduction formula
        tv_ac = PLNFormulas.deduction(link_ab.truth_value, link_bc.truth_value)
        
        # Check confidence threshold
        if tv_ac.confidence < self.min_confidence_threshold:
            return None
        
        # Create or update A->C link
        existing = self.atomspace.match_pattern(
            AtomType.INHERITANCE_LINK,
            [a_handle, c_handle]
        )
        
        if existing:
            # Merge with existing
            self.atomspace.merge_truth_value(existing[0].handle, tv_ac)
            self.stats['atoms_strengthened'] += 1
            conclusion = existing[0]
        else:
            # Create new link
            new_handle = self.atomspace.add_link(
                AtomType.INHERITANCE_LINK,
                [a_handle, c_handle],
                tv=tv_ac
            )
            if new_handle:
                self.stats['new_atoms_created'] += 1
                conclusion = self.atomspace.get_atom(new_handle)
            else:
                return None
        
        # Record in history
        self._add_to_history(history_key)
        
        self.stats['total_inferences'] += 1
        self.stats['successful_inferences'] += 1
        
        return InferenceResult(
            inference_type=InferenceType.DEDUCTION,
            premises=[link_ab.handle, link_bc.handle],
            conclusion=conclusion,
            truth_value=tv_ac,
            confidence=tv_ac.confidence,
            computation_cost=1.0
        )
    
    def induction(
        self,
        link_ab: Link,
        link_ac: Link
    ) -> Optional[InferenceResult]:
        """
        Perform induction: A->B, A->C => B->C
        """
        if not isinstance(link_ab, Link) or not isinstance(link_ac, Link):
            return None
        
        if len(link_ab.outgoing) < 2 or len(link_ac.outgoing) < 2:
            return None
        
        # Check common source
        if link_ab.outgoing[0] != link_ac.outgoing[0]:
            return None
        
        history_key = f"ind:{link_ab.handle.uuid}:{link_ac.handle.uuid}"
        if history_key in self._inference_history:
            return None
        
        # Get B and C
        b_handle = link_ab.outgoing[1]
        c_handle = link_ac.outgoing[1]
        
        if b_handle == c_handle:
            return None
        
        # Apply induction formula
        tv_bc = PLNFormulas.induction(link_ab.truth_value, link_ac.truth_value)
        
        if tv_bc.confidence < self.min_confidence_threshold:
            return None
        
        # Create or update B->C link
        existing = self.atomspace.match_pattern(
            AtomType.INHERITANCE_LINK,
            [b_handle, c_handle]
        )
        
        if existing:
            self.atomspace.merge_truth_value(existing[0].handle, tv_bc)
            self.stats['atoms_strengthened'] += 1
            conclusion = existing[0]
        else:
            new_handle = self.atomspace.add_link(
                AtomType.INHERITANCE_LINK,
                [b_handle, c_handle],
                tv=tv_bc
            )
            if new_handle:
                self.stats['new_atoms_created'] += 1
                conclusion = self.atomspace.get_atom(new_handle)
            else:
                return None
        
        self._add_to_history(history_key)
        
        self.stats['total_inferences'] += 1
        self.stats['successful_inferences'] += 1
        
        return InferenceResult(
            inference_type=InferenceType.INDUCTION,
            premises=[link_ab.handle, link_ac.handle],
            conclusion=conclusion,
            truth_value=tv_bc,
            confidence=tv_bc.confidence,
            computation_cost=1.0
        )
    
    def abduction(
        self,
        link_ab: Link,
        link_cb: Link
    ) -> Optional[InferenceResult]:
        """
        Perform abduction: A->B, C->B => A->C
        """
        if not isinstance(link_ab, Link) or not isinstance(link_cb, Link):
            return None
        
        if len(link_ab.outgoing) < 2 or len(link_cb.outgoing) < 2:
            return None
        
        # Check common target
        if link_ab.outgoing[1] != link_cb.outgoing[1]:
            return None
        
        history_key = f"abd:{link_ab.handle.uuid}:{link_cb.handle.uuid}"
        if history_key in self._inference_history:
            return None
        
        # Get A and C
        a_handle = link_ab.outgoing[0]
        c_handle = link_cb.outgoing[0]
        
        if a_handle == c_handle:
            return None
        
        # Apply abduction formula
        tv_ac = PLNFormulas.abduction(link_ab.truth_value, link_cb.truth_value)
        
        if tv_ac.confidence < self.min_confidence_threshold:
            return None
        
        # Create or update A->C link
        existing = self.atomspace.match_pattern(
            AtomType.INHERITANCE_LINK,
            [a_handle, c_handle]
        )
        
        if existing:
            self.atomspace.merge_truth_value(existing[0].handle, tv_ac)
            self.stats['atoms_strengthened'] += 1
            conclusion = existing[0]
        else:
            new_handle = self.atomspace.add_link(
                AtomType.INHERITANCE_LINK,
                [a_handle, c_handle],
                tv=tv_ac
            )
            if new_handle:
                self.stats['new_atoms_created'] += 1
                conclusion = self.atomspace.get_atom(new_handle)
            else:
                return None
        
        self._add_to_history(history_key)
        
        self.stats['total_inferences'] += 1
        self.stats['successful_inferences'] += 1
        
        return InferenceResult(
            inference_type=InferenceType.ABDUCTION,
            premises=[link_ab.handle, link_cb.handle],
            conclusion=conclusion,
            truth_value=tv_ac,
            confidence=tv_ac.confidence,
            computation_cost=1.0
        )
    
    def modus_ponens(
        self,
        atom_a: Atom,
        link_ab: Link
    ) -> Optional[InferenceResult]:
        """
        Perform modus ponens: A, A->B => B
        """
        if not isinstance(link_ab, Link) or len(link_ab.outgoing) < 2:
            return None
        
        if link_ab.atom_type != AtomType.IMPLICATION_LINK:
            return None
        
        # Check that A matches the antecedent
        if atom_a.handle != link_ab.outgoing[0]:
            return None
        
        history_key = f"mp:{atom_a.handle.uuid}:{link_ab.handle.uuid}"
        if history_key in self._inference_history:
            return None
        
        # Get B
        b_handle = link_ab.outgoing[1]
        b_atom = self.atomspace.get_atom(b_handle)
        
        if not b_atom:
            return None
        
        # Apply modus ponens formula
        tv_b = PLNFormulas.modus_ponens(atom_a.truth_value, link_ab.truth_value)
        
        if tv_b.confidence < self.min_confidence_threshold:
            return None
        
        # Update B's truth value
        self.atomspace.merge_truth_value(b_handle, tv_b)
        self.stats['atoms_strengthened'] += 1
        
        self._add_to_history(history_key)
        
        self.stats['total_inferences'] += 1
        self.stats['successful_inferences'] += 1
        
        return InferenceResult(
            inference_type=InferenceType.MODUS_PONENS,
            premises=[atom_a.handle, link_ab.handle],
            conclusion=b_atom,
            truth_value=tv_b,
            confidence=tv_b.confidence,
            computation_cost=1.0
        )
    
    # =========================================================================
    # FORWARD CHAINING
    # =========================================================================
    
    def forward_chain(
        self,
        max_steps: int = 100,
        focus_atoms: Optional[Set[AtomHandle]] = None
    ) -> List[InferenceResult]:
        """
        Perform forward chaining inference.
        
        Starting from the current knowledge, apply inference rules
        to derive new knowledge.
        """
        results = []
        steps = 0
        
        while steps < max_steps:
            # Find deduction premises
            deduction_premises = self.controller.find_deduction_premises()
            if focus_atoms:
                deduction_premises = [
                    (l1, l2) for l1, l2 in deduction_premises
                    if l1.handle in focus_atoms or l2.handle in focus_atoms
                ]
            
            # Select by attention
            selected = self.controller.select_premises_by_attention(
                deduction_premises, limit=5
            )
            
            # Apply deduction
            for link_ab, link_bc in selected:
                result = self.deduction(link_ab, link_bc)
                if result:
                    results.append(result)
                    steps += 1
                    if steps >= max_steps:
                        break
            
            # Find induction premises
            if steps < max_steps:
                induction_premises = self.controller.find_induction_premises()
                if focus_atoms:
                    induction_premises = [
                        (l1, l2) for l1, l2 in induction_premises
                        if l1.handle in focus_atoms or l2.handle in focus_atoms
                    ]
                
                selected = self.controller.select_premises_by_attention(
                    induction_premises, limit=3
                )
                
                for link_ab, link_ac in selected:
                    result = self.induction(link_ab, link_ac)
                    if result:
                        results.append(result)
                        steps += 1
                        if steps >= max_steps:
                            break
            
            # Break if no progress
            if not results or steps == 0:
                break
        
        return results
    
    # =========================================================================
    # BACKWARD CHAINING
    # =========================================================================
    
    def backward_chain(
        self,
        goal: AtomHandle,
        max_depth: int = None
    ) -> Optional[List[InferenceResult]]:
        """
        Perform backward chaining to prove a goal.
        
        Starting from a goal, work backwards to find supporting evidence.
        """
        if max_depth is None:
            max_depth = self.max_inference_depth
        
        return self._backward_chain_recursive(goal, max_depth, set())
    
    def _backward_chain_recursive(
        self,
        goal: AtomHandle,
        depth: int,
        visited: Set[AtomHandle]
    ) -> Optional[List[InferenceResult]]:
        """Recursive backward chaining."""
        if depth <= 0 or goal in visited:
            return None
        
        visited.add(goal)
        
        goal_atom = self.atomspace.get_atom(goal)
        if not goal_atom:
            return None
        
        # If goal has high confidence, it's already proven
        if goal_atom.truth_value.confidence > 0.8:
            return []
        
        results = []
        
        # Find links that could prove this goal
        incoming = self.atomspace.get_incoming(goal)
        
        for link in incoming:
            if link.atom_type == AtomType.INHERITANCE_LINK:
                # Goal is the consequent, find antecedent
                if len(link.outgoing) >= 2 and link.outgoing[1] == goal:
                    antecedent = link.outgoing[0]
                    
                    # Recursively prove antecedent
                    sub_results = self._backward_chain_recursive(
                        antecedent, depth - 1, visited
                    )
                    
                    if sub_results is not None:
                        results.extend(sub_results)
                        
                        # Apply deduction if we found a chain
                        antecedent_atom = self.atomspace.get_atom(antecedent)
                        if antecedent_atom:
                            # Look for links from antecedent
                            for ante_link in self.atomspace.get_incoming(antecedent):
                                if (ante_link.atom_type == AtomType.INHERITANCE_LINK and
                                    len(ante_link.outgoing) >= 2 and
                                    ante_link.outgoing[1] == antecedent):
                                    result = self.deduction(ante_link, link)
                                    if result:
                                        results.append(result)
        
        return results if results else None
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _validate_chain(self, link_ab: Link, link_bc: Link) -> bool:
        """Validate that two links form a valid chain for deduction."""
        if not isinstance(link_ab, Link) or not isinstance(link_bc, Link):
            return False
        
        if len(link_ab.outgoing) < 2 or len(link_bc.outgoing) < 2:
            return False
        
        # B in A->B should equal B in B->C
        return link_ab.outgoing[1] == link_bc.outgoing[0]
    
    def _apply_inference(
        self,
        atoms: List[Atom],
        rule: InferenceRule,
        inference_type: InferenceType
    ) -> Optional[InferenceResult]:
        """Apply an inference rule to atoms."""
        if inference_type == InferenceType.DEDUCTION:
            if len(atoms) >= 2 and isinstance(atoms[0], Link) and isinstance(atoms[1], Link):
                return self.deduction(atoms[0], atoms[1])
        elif inference_type == InferenceType.INDUCTION:
            if len(atoms) >= 2 and isinstance(atoms[0], Link) and isinstance(atoms[1], Link):
                return self.induction(atoms[0], atoms[1])
        elif inference_type == InferenceType.ABDUCTION:
            if len(atoms) >= 2 and isinstance(atoms[0], Link) and isinstance(atoms[1], Link):
                return self.abduction(atoms[0], atoms[1])
        elif inference_type == InferenceType.MODUS_PONENS:
            if len(atoms) >= 2 and isinstance(atoms[1], Link):
                return self.modus_ponens(atoms[0], atoms[1])
        
        return None
    
    def _add_to_history(self, key: str):
        """Add inference to history, managing size."""
        if len(self._inference_history) >= self._history_max_size:
            # Remove oldest entries (approximate)
            to_remove = list(self._inference_history)[:self._history_max_size // 2]
            for k in to_remove:
                self._inference_history.discard(k)
        
        self._inference_history.add(key)
    
    def _inference_loop(self):
        """Background inference loop."""
        while self._running:
            try:
                # Get atoms in attentional focus
                focus = self.atomspace.get_attentional_focus(limit=50)
                focus_handles = {a.handle for a in focus}
                
                # Perform forward chaining on focus
                if focus_handles:
                    self.forward_chain(max_steps=10, focus_atoms=focus_handles)
                
            except Exception as e:
                pass  # Log in production
            
            time.sleep(0.1)  # Inference cycle interval


# Export
__all__ = [
    'PLNConfig',
    'PLNFormulas',
    'InferenceRule',
    'InferenceRuleSet',
    'InferenceController',
    'InferenceTask',
    'PLNEngine',
]
