"""
OpenCog Inferno AGI - Pattern Recognition System
================================================

This module implements pattern recognition and mining capabilities:
- Frequent subgraph mining
- Pattern abstraction and generalization
- Anomaly detection
- Concept formation

Pattern recognition is essential for learning and intelligence emergence.
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
from collections import defaultdict, Counter
import math
import hashlib

from kernel.cognitive.types import (
    Atom, Node, Link, AtomHandle, AtomType,
    TruthValue, AttentionValue, Pattern, BindingSet
)
from atomspace.hypergraph.atomspace import AtomSpace
from atomspace.query.pattern_matcher import PatternMatcher, VariableNode, PatternLink


# =============================================================================
# PATTERN TYPES
# =============================================================================

@dataclass
class DiscoveredPattern:
    """A pattern discovered through mining."""
    pattern_id: str
    structure: PatternLink
    support: int                    # Number of occurrences
    confidence: float               # Statistical confidence
    instances: List[Dict[str, AtomHandle]] = field(default_factory=list)
    abstraction_level: int = 0      # 0 = concrete, higher = more abstract
    parent_patterns: List[str] = field(default_factory=list)
    child_patterns: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    
    def get_hash(self) -> str:
        """Get content hash for pattern."""
        content = f"{self.structure.atom_type.name}:{len(self.structure.outgoing)}"
        return hashlib.md5(content.encode()).hexdigest()[:12]


@dataclass
class PatternStatistics:
    """Statistics about a pattern."""
    frequency: int = 0
    total_truth_strength: float = 0.0
    total_attention: float = 0.0
    co_occurrence: Dict[str, int] = field(default_factory=dict)
    temporal_distribution: List[float] = field(default_factory=list)
    
    @property
    def average_strength(self) -> float:
        if self.frequency == 0:
            return 0.0
        return self.total_truth_strength / self.frequency
    
    @property
    def average_attention(self) -> float:
        if self.frequency == 0:
            return 0.0
        return self.total_attention / self.frequency


# =============================================================================
# SUBGRAPH MINING
# =============================================================================

class SubgraphMiner:
    """
    Mines frequent subgraph patterns from the AtomSpace.
    
    Uses a simplified gSpan-like algorithm adapted for hypergraphs.
    """
    
    def __init__(
        self,
        atomspace: AtomSpace,
        min_support: int = 3,
        max_pattern_size: int = 5
    ):
        self.atomspace = atomspace
        self.min_support = min_support
        self.max_pattern_size = max_pattern_size
        
        # Pattern storage
        self._patterns: Dict[str, DiscoveredPattern] = {}
        self._pattern_index: Dict[AtomType, Set[str]] = defaultdict(set)
        
        # Statistics
        self.stats = {
            'patterns_discovered': 0,
            'mining_runs': 0,
            'atoms_processed': 0
        }
        
        self._lock = threading.Lock()
    
    def mine_patterns(
        self,
        focus_atoms: Optional[Set[AtomHandle]] = None,
        link_types: Optional[List[AtomType]] = None
    ) -> List[DiscoveredPattern]:
        """
        Mine frequent patterns from the AtomSpace.
        """
        self.stats['mining_runs'] += 1
        
        # Default link types to mine
        if link_types is None:
            link_types = [
                AtomType.INHERITANCE_LINK,
                AtomType.SIMILARITY_LINK,
                AtomType.EVALUATION_LINK,
                AtomType.IMPLICATION_LINK
            ]
        
        discovered = []
        
        # Mine single-edge patterns first
        single_patterns = self._mine_single_edge_patterns(link_types, focus_atoms)
        discovered.extend(single_patterns)
        
        # Extend patterns iteratively
        current_patterns = single_patterns
        for size in range(2, self.max_pattern_size + 1):
            extended = self._extend_patterns(current_patterns, focus_atoms)
            if not extended:
                break
            discovered.extend(extended)
            current_patterns = extended
        
        # Store discovered patterns
        with self._lock:
            for pattern in discovered:
                self._patterns[pattern.pattern_id] = pattern
                self._pattern_index[pattern.structure.atom_type].add(pattern.pattern_id)
        
        self.stats['patterns_discovered'] += len(discovered)
        return discovered
    
    def _mine_single_edge_patterns(
        self,
        link_types: List[AtomType],
        focus_atoms: Optional[Set[AtomHandle]]
    ) -> List[DiscoveredPattern]:
        """Mine single-edge (single link) patterns."""
        patterns = []
        
        for link_type in link_types:
            # Count link type occurrences
            type_counts: Dict[Tuple[AtomType, ...], List[Link]] = defaultdict(list)
            
            for link in self.atomspace.get_atoms_by_type(link_type):
                if not isinstance(link, Link):
                    continue
                
                self.stats['atoms_processed'] += 1
                
                # Skip if not in focus (when focus specified)
                if focus_atoms:
                    if not any(h in focus_atoms for h in link.outgoing):
                        continue
                
                # Get signature (types of outgoing atoms)
                signature = tuple(
                    self.atomspace.get_atom(h).atom_type 
                    for h in link.outgoing 
                    if self.atomspace.get_atom(h)
                )
                
                type_counts[signature].append(link)
            
            # Create patterns for frequent signatures
            for signature, links in type_counts.items():
                if len(links) >= self.min_support:
                    # Create pattern with variables
                    variables = [
                        VariableNode(f"X{i}", type_constraint=sig_type)
                        for i, sig_type in enumerate(signature)
                    ]
                    
                    pattern_link = PatternLink(
                        atom_type=link_type,
                        outgoing=variables
                    )
                    
                    pattern = DiscoveredPattern(
                        pattern_id=f"p_{link_type.name}_{len(patterns)}",
                        structure=pattern_link,
                        support=len(links),
                        confidence=len(links) / max(1, len(self.atomspace.get_atoms_by_type(link_type))),
                        instances=[{f"X{i}": l.outgoing[i] for i in range(len(l.outgoing))} for l in links],
                        abstraction_level=0
                    )
                    patterns.append(pattern)
        
        return patterns
    
    def _extend_patterns(
        self,
        base_patterns: List[DiscoveredPattern],
        focus_atoms: Optional[Set[AtomHandle]]
    ) -> List[DiscoveredPattern]:
        """Extend patterns by adding edges."""
        extended = []
        
        for base in base_patterns:
            # Find common extensions across instances
            extension_counts: Dict[str, List[Dict[str, AtomHandle]]] = defaultdict(list)
            
            for instance in base.instances:
                # Get atoms in this instance
                instance_atoms = set(instance.values())
                
                # Find links connecting to these atoms
                for handle in instance_atoms:
                    for link in self.atomspace.get_incoming(handle):
                        # Skip if already in pattern
                        if link.handle in instance_atoms:
                            continue
                        
                        # Create extension signature
                        ext_sig = f"{link.atom_type.name}_{len(link.outgoing)}"
                        
                        # Record extension
                        ext_instance = instance.copy()
                        for i, out_h in enumerate(link.outgoing):
                            if out_h not in instance_atoms:
                                ext_instance[f"Y{i}"] = out_h
                        
                        extension_counts[ext_sig].append(ext_instance)
            
            # Create extended patterns for frequent extensions
            for ext_sig, ext_instances in extension_counts.items():
                if len(ext_instances) >= self.min_support:
                    # Create extended pattern
                    # (simplified - full implementation would merge structures)
                    extended_pattern = DiscoveredPattern(
                        pattern_id=f"{base.pattern_id}_ext_{len(extended)}",
                        structure=base.structure,  # Would be extended in full impl
                        support=len(ext_instances),
                        confidence=len(ext_instances) / max(1, base.support),
                        instances=ext_instances,
                        abstraction_level=base.abstraction_level,
                        parent_patterns=[base.pattern_id]
                    )
                    extended.append(extended_pattern)
                    
                    # Update parent's children
                    base.child_patterns.append(extended_pattern.pattern_id)
        
        return extended
    
    def get_pattern(self, pattern_id: str) -> Optional[DiscoveredPattern]:
        """Get a pattern by ID."""
        return self._patterns.get(pattern_id)
    
    def get_patterns_by_type(self, atom_type: AtomType) -> List[DiscoveredPattern]:
        """Get patterns involving a specific atom type."""
        pattern_ids = self._pattern_index.get(atom_type, set())
        return [self._patterns[pid] for pid in pattern_ids if pid in self._patterns]


# =============================================================================
# CONCEPT FORMATION
# =============================================================================

class ConceptFormer:
    """
    Forms new concepts by abstracting over patterns.
    
    This implements a form of unsupervised concept learning.
    """
    
    def __init__(self, atomspace: AtomSpace, miner: SubgraphMiner):
        self.atomspace = atomspace
        self.miner = miner
        
        # Formed concepts
        self._concepts: Dict[str, AtomHandle] = {}
        
        self.stats = {
            'concepts_formed': 0,
            'abstractions_made': 0
        }
    
    def form_concept_from_pattern(
        self,
        pattern: DiscoveredPattern,
        concept_name: Optional[str] = None
    ) -> Optional[AtomHandle]:
        """
        Form a new concept from a discovered pattern.
        """
        if pattern.support < 2:
            return None
        
        # Generate concept name if not provided
        if concept_name is None:
            concept_name = f"Concept_{pattern.pattern_id}"
        
        # Check if concept already exists
        existing = self.atomspace.get_node(AtomType.CONCEPT_NODE, concept_name)
        if existing:
            return existing.handle
        
        # Create concept node
        tv = TruthValue(
            strength=pattern.confidence,
            confidence=min(0.9, pattern.support / 10),
            count=pattern.support
        )
        
        concept_handle = self.atomspace.add_node(
            AtomType.CONCEPT_NODE,
            concept_name,
            tv=tv,
            av=AttentionValue(sti=0.3, lti=0.5)
        )
        
        # Link instances to concept
        for instance in pattern.instances[:10]:  # Limit to avoid explosion
            for var_name, atom_handle in instance.items():
                self.atomspace.add_link(
                    AtomType.MEMBER_LINK,
                    [atom_handle, concept_handle],
                    tv=TruthValue(0.9, 0.8)
                )
        
        self._concepts[concept_name] = concept_handle
        self.stats['concepts_formed'] += 1
        
        return concept_handle
    
    def abstract_concepts(
        self,
        concepts: List[AtomHandle],
        abstraction_name: Optional[str] = None
    ) -> Optional[AtomHandle]:
        """
        Create an abstract concept from multiple concepts.
        """
        if len(concepts) < 2:
            return None
        
        # Find common properties
        common_parents = self._find_common_parents(concepts)
        
        if not common_parents:
            # Create new abstraction
            if abstraction_name is None:
                abstraction_name = f"Abstract_{len(self._concepts)}"
            
            abstract_handle = self.atomspace.add_node(
                AtomType.CONCEPT_NODE,
                abstraction_name,
                tv=TruthValue(0.8, 0.6),
                av=AttentionValue(sti=0.2, lti=0.6)
            )
            
            # Link concepts to abstraction
            for concept_handle in concepts:
                self.atomspace.add_link(
                    AtomType.INHERITANCE_LINK,
                    [concept_handle, abstract_handle],
                    tv=TruthValue(0.9, 0.7)
                )
            
            self.stats['abstractions_made'] += 1
            return abstract_handle
        
        # Use most specific common parent
        return common_parents[0]
    
    def _find_common_parents(
        self,
        concepts: List[AtomHandle]
    ) -> List[AtomHandle]:
        """Find common parent concepts."""
        if not concepts:
            return []
        
        # Get parents of first concept
        first_parents = set()
        for link in self.atomspace.get_incoming(concepts[0]):
            if link.atom_type == AtomType.INHERITANCE_LINK:
                if len(link.outgoing) >= 2 and link.outgoing[0] == concepts[0]:
                    first_parents.add(link.outgoing[1])
        
        # Intersect with parents of other concepts
        common = first_parents
        for concept in concepts[1:]:
            concept_parents = set()
            for link in self.atomspace.get_incoming(concept):
                if link.atom_type == AtomType.INHERITANCE_LINK:
                    if len(link.outgoing) >= 2 and link.outgoing[0] == concept:
                        concept_parents.add(link.outgoing[1])
            common = common.intersection(concept_parents)
        
        return list(common)


# =============================================================================
# ANOMALY DETECTION
# =============================================================================

class AnomalyDetector:
    """
    Detects anomalous patterns in the AtomSpace.
    
    Anomalies are atoms or patterns that deviate significantly
    from expected distributions.
    """
    
    def __init__(self, atomspace: AtomSpace):
        self.atomspace = atomspace
        
        # Baseline statistics
        self._type_distributions: Dict[AtomType, int] = defaultdict(int)
        self._link_arity_dist: Dict[AtomType, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
        self._truth_value_stats: Dict[AtomType, List[float]] = defaultdict(list)
        
        self._baseline_computed = False
    
    def compute_baseline(self):
        """Compute baseline statistics from current AtomSpace."""
        self._type_distributions.clear()
        self._link_arity_dist.clear()
        self._truth_value_stats.clear()
        
        for atom in self.atomspace:
            self._type_distributions[atom.atom_type] += 1
            self._truth_value_stats[atom.atom_type].append(atom.truth_value.strength)
            
            if isinstance(atom, Link):
                self._link_arity_dist[atom.atom_type][len(atom.outgoing)] += 1
        
        self._baseline_computed = True
    
    def detect_anomalies(
        self,
        threshold: float = 2.0  # Standard deviations
    ) -> List[Tuple[Atom, str, float]]:
        """
        Detect anomalous atoms.
        
        Returns list of (atom, reason, anomaly_score).
        """
        if not self._baseline_computed:
            self.compute_baseline()
        
        anomalies = []
        
        for atom in self.atomspace:
            # Check truth value anomaly
            tv_scores = self._truth_value_stats.get(atom.atom_type, [])
            if tv_scores:
                mean_tv = sum(tv_scores) / len(tv_scores)
                std_tv = math.sqrt(sum((x - mean_tv) ** 2 for x in tv_scores) / len(tv_scores)) + 0.001
                
                z_score = abs(atom.truth_value.strength - mean_tv) / std_tv
                if z_score > threshold:
                    anomalies.append((
                        atom,
                        f"Unusual truth value: {atom.truth_value.strength:.2f} (mean: {mean_tv:.2f})",
                        z_score
                    ))
            
            # Check arity anomaly for links
            if isinstance(atom, Link):
                arity_dist = self._link_arity_dist.get(atom.atom_type, {})
                if arity_dist:
                    total = sum(arity_dist.values())
                    expected_freq = arity_dist.get(len(atom.outgoing), 0) / total
                    
                    if expected_freq < 0.01:  # Very rare arity
                        anomalies.append((
                            atom,
                            f"Unusual arity: {len(atom.outgoing)}",
                            1.0 / (expected_freq + 0.001)
                        ))
        
        # Sort by anomaly score
        anomalies.sort(key=lambda x: -x[2])
        return anomalies
    
    def is_anomalous(self, atom: Atom, threshold: float = 2.0) -> bool:
        """Check if a specific atom is anomalous."""
        if not self._baseline_computed:
            self.compute_baseline()
        
        tv_scores = self._truth_value_stats.get(atom.atom_type, [])
        if tv_scores:
            mean_tv = sum(tv_scores) / len(tv_scores)
            std_tv = math.sqrt(sum((x - mean_tv) ** 2 for x in tv_scores) / len(tv_scores)) + 0.001
            z_score = abs(atom.truth_value.strength - mean_tv) / std_tv
            return z_score > threshold
        
        return False


# =============================================================================
# PATTERN RECOGNITION SERVICE
# =============================================================================

class PatternRecognitionService:
    """
    Main pattern recognition service for the cognitive kernel.
    
    Integrates mining, concept formation, and anomaly detection.
    """
    
    def __init__(self, atomspace: AtomSpace):
        self.atomspace = atomspace
        
        # Components
        self.miner = SubgraphMiner(atomspace)
        self.concept_former = ConceptFormer(atomspace, self.miner)
        self.anomaly_detector = AnomalyDetector(atomspace)
        
        # Service state
        self._running = False
        self._recognition_thread: Optional[threading.Thread] = None
        
        # Configuration
        self.mining_interval = 60.0  # seconds
        self.anomaly_check_interval = 30.0
        
        # Callbacks
        self._on_pattern_discovered: List[Callable[[DiscoveredPattern], None]] = []
        self._on_anomaly_detected: List[Callable[[Atom, str, float], None]] = []
    
    @property
    def service_name(self) -> str:
        return "pattern_recognition_service"
    
    def start(self) -> bool:
        """Start the pattern recognition service."""
        if self._running:
            return False
        
        self._running = True
        self._recognition_thread = threading.Thread(
            target=self._recognition_loop,
            daemon=True,
            name="pattern-recognition"
        )
        self._recognition_thread.start()
        return True
    
    def stop(self) -> bool:
        """Stop the service."""
        if not self._running:
            return False
        
        self._running = False
        if self._recognition_thread:
            self._recognition_thread.join(timeout=2.0)
        return True
    
    def status(self) -> Dict[str, Any]:
        """Get service status."""
        return {
            'running': self._running,
            'miner_stats': self.miner.stats.copy(),
            'concept_former_stats': self.concept_former.stats.copy(),
            'patterns_count': len(self.miner._patterns)
        }
    
    def _recognition_loop(self):
        """Background recognition loop."""
        last_mining = 0
        last_anomaly = 0
        
        while self._running:
            try:
                current_time = time.time()
                
                # Periodic mining
                if current_time - last_mining >= self.mining_interval:
                    patterns = self.miner.mine_patterns()
                    for pattern in patterns:
                        self._notify_pattern_discovered(pattern)
                    last_mining = current_time
                
                # Periodic anomaly detection
                if current_time - last_anomaly >= self.anomaly_check_interval:
                    anomalies = self.anomaly_detector.detect_anomalies()
                    for atom, reason, score in anomalies[:10]:
                        self._notify_anomaly_detected(atom, reason, score)
                    last_anomaly = current_time
                
            except Exception as e:
                pass  # Log in production
            
            time.sleep(1.0)
    
    def recognize_pattern(
        self,
        atoms: List[AtomHandle]
    ) -> Optional[DiscoveredPattern]:
        """
        Try to recognize a pattern in the given atoms.
        """
        # Get atoms
        atom_objs = [self.atomspace.get_atom(h) for h in atoms]
        atom_objs = [a for a in atom_objs if a is not None]
        
        if not atom_objs:
            return None
        
        # Check against known patterns
        for pattern in self.miner._patterns.values():
            if self._matches_pattern(atom_objs, pattern):
                return pattern
        
        return None
    
    def _matches_pattern(
        self,
        atoms: List[Atom],
        pattern: DiscoveredPattern
    ) -> bool:
        """Check if atoms match a pattern."""
        # Simplified matching - full implementation would use unification
        if len(atoms) != len(pattern.structure.outgoing):
            return False
        
        for atom, var in zip(atoms, pattern.structure.outgoing):
            if isinstance(var, VariableNode):
                if var.type_constraint and atom.atom_type != var.type_constraint:
                    return False
        
        return True
    
    def on_pattern_discovered(self, callback: Callable[[DiscoveredPattern], None]):
        """Register callback for pattern discovery."""
        self._on_pattern_discovered.append(callback)
    
    def on_anomaly_detected(self, callback: Callable[[Atom, str, float], None]):
        """Register callback for anomaly detection."""
        self._on_anomaly_detected.append(callback)
    
    def _notify_pattern_discovered(self, pattern: DiscoveredPattern):
        """Notify callbacks of pattern discovery."""
        for callback in self._on_pattern_discovered:
            try:
                callback(pattern)
            except:
                pass
    
    def _notify_anomaly_detected(self, atom: Atom, reason: str, score: float):
        """Notify callbacks of anomaly detection."""
        for callback in self._on_anomaly_detected:
            try:
                callback(atom, reason, score)
            except:
                pass


# Export
__all__ = [
    'DiscoveredPattern',
    'PatternStatistics',
    'SubgraphMiner',
    'ConceptFormer',
    'AnomalyDetector',
    'PatternRecognitionService',
]
