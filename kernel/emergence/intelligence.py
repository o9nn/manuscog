"""
OpenCog Inferno AGI - Emergent Intelligence System
=================================================

This module implements the emergent intelligence layer that
integrates all cognitive subsystems into a unified whole:

- Cognitive Synergy: Coordinated interaction between subsystems
- Goal-Directed Behavior: Autonomous goal pursuit
- Self-Reflection: Introspection and self-modification
- Creativity: Novel idea generation
- Consciousness Model: Integrated information processing

Intelligence emerges from the dynamic interaction of these
components, not from any single algorithm.
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
import random
import math
from collections import defaultdict

from kernel.cognitive.types import (
    Atom, Node, Link, AtomHandle, AtomType,
    TruthValue, AttentionValue, CognitiveContext,
    CognitiveGoal, GoalState, CognitiveProcessState
)
from atomspace.hypergraph.atomspace import AtomSpace


# =============================================================================
# COGNITIVE SYNERGY
# =============================================================================

class CognitiveSubsystem(Enum):
    """The main cognitive subsystems."""
    PLN = auto()            # Probabilistic Logic Networks
    MOSES = auto()          # Program learning
    ECAN = auto()           # Attention allocation
    PATTERN = auto()        # Pattern recognition
    MEMORY = auto()         # Memory management
    PERCEPTION = auto()     # Sensory processing
    ACTION = auto()         # Action execution


@dataclass
class SubsystemState:
    """State of a cognitive subsystem."""
    subsystem: CognitiveSubsystem
    active: bool = False
    load: float = 0.0
    last_activity: float = field(default_factory=time.time)
    pending_requests: int = 0
    completed_tasks: int = 0
    
    # Performance metrics
    avg_response_time: float = 0.0
    success_rate: float = 1.0


@dataclass
class SynergyRequest:
    """A request for cognitive synergy between subsystems."""
    request_id: str = field(default_factory=lambda: f"syn_{int(time.time() * 1000)}")
    source: CognitiveSubsystem = CognitiveSubsystem.PLN
    target: CognitiveSubsystem = CognitiveSubsystem.PATTERN
    request_type: str = "query"
    payload: Dict[str, Any] = field(default_factory=dict)
    priority: float = 0.5
    timestamp: float = field(default_factory=time.time)
    response: Any = None
    completed: bool = False


class CognitiveSynergy:
    """
    Manages synergistic interaction between cognitive subsystems.
    
    Cognitive synergy is the key to AGI - different algorithms
    working together achieve more than any could alone.
    """
    
    def __init__(self, atomspace: AtomSpace):
        self.atomspace = atomspace
        
        # Subsystem states
        self._subsystems: Dict[CognitiveSubsystem, SubsystemState] = {
            s: SubsystemState(subsystem=s) for s in CognitiveSubsystem
        }
        
        # Request queue
        self._requests: List[SynergyRequest] = []
        
        # Synergy patterns (which subsystems help each other)
        self._synergy_matrix: Dict[Tuple[CognitiveSubsystem, CognitiveSubsystem], float] = {}
        self._initialize_synergy_matrix()
        
        # Callbacks for subsystem handlers
        self._handlers: Dict[CognitiveSubsystem, Callable[[SynergyRequest], Any]] = {}
        
        self._lock = threading.RLock()
    
    def _initialize_synergy_matrix(self):
        """Initialize synergy weights between subsystems."""
        # PLN + MOSES: Learning guides reasoning, reasoning validates learning
        self._synergy_matrix[(CognitiveSubsystem.PLN, CognitiveSubsystem.MOSES)] = 0.8
        self._synergy_matrix[(CognitiveSubsystem.MOSES, CognitiveSubsystem.PLN)] = 0.8
        
        # PLN + PATTERN: Patterns inform reasoning, reasoning explains patterns
        self._synergy_matrix[(CognitiveSubsystem.PLN, CognitiveSubsystem.PATTERN)] = 0.9
        self._synergy_matrix[(CognitiveSubsystem.PATTERN, CognitiveSubsystem.PLN)] = 0.7
        
        # ECAN + all: Attention guides all subsystems
        for s in CognitiveSubsystem:
            if s != CognitiveSubsystem.ECAN:
                self._synergy_matrix[(CognitiveSubsystem.ECAN, s)] = 0.6
                self._synergy_matrix[(s, CognitiveSubsystem.ECAN)] = 0.5
        
        # PATTERN + MOSES: Patterns seed learning, learning finds patterns
        self._synergy_matrix[(CognitiveSubsystem.PATTERN, CognitiveSubsystem.MOSES)] = 0.7
        self._synergy_matrix[(CognitiveSubsystem.MOSES, CognitiveSubsystem.PATTERN)] = 0.6
    
    def register_handler(
        self,
        subsystem: CognitiveSubsystem,
        handler: Callable[[SynergyRequest], Any]
    ):
        """Register a handler for a subsystem."""
        self._handlers[subsystem] = handler
        self._subsystems[subsystem].active = True
    
    def request_synergy(
        self,
        source: CognitiveSubsystem,
        target: CognitiveSubsystem,
        request_type: str,
        payload: Dict[str, Any],
        priority: float = 0.5
    ) -> SynergyRequest:
        """Request synergistic assistance from another subsystem."""
        request = SynergyRequest(
            source=source,
            target=target,
            request_type=request_type,
            payload=payload,
            priority=priority
        )
        
        with self._lock:
            self._requests.append(request)
            self._subsystems[target].pending_requests += 1
        
        return request
    
    def process_requests(self):
        """Process pending synergy requests."""
        with self._lock:
            # Sort by priority
            self._requests.sort(key=lambda r: -r.priority)
            
            processed = []
            for request in self._requests:
                if request.completed:
                    continue
                
                handler = self._handlers.get(request.target)
                if handler:
                    try:
                        start_time = time.time()
                        request.response = handler(request)
                        request.completed = True
                        
                        # Update metrics
                        state = self._subsystems[request.target]
                        state.completed_tasks += 1
                        state.pending_requests -= 1
                        state.last_activity = time.time()
                        
                        response_time = time.time() - start_time
                        state.avg_response_time = (
                            state.avg_response_time * 0.9 + response_time * 0.1
                        )
                        
                        processed.append(request)
                    except Exception as e:
                        state = self._subsystems[request.target]
                        state.success_rate *= 0.99  # Decay on failure
            
            # Remove completed requests
            self._requests = [r for r in self._requests if not r.completed]
    
    def get_synergy_strength(
        self,
        source: CognitiveSubsystem,
        target: CognitiveSubsystem
    ) -> float:
        """Get the synergy strength between two subsystems."""
        return self._synergy_matrix.get((source, target), 0.0)
    
    def suggest_synergy(
        self,
        current_subsystem: CognitiveSubsystem,
        context: CognitiveContext
    ) -> List[Tuple[CognitiveSubsystem, float]]:
        """Suggest which subsystems could help with current task."""
        suggestions = []
        
        for target in CognitiveSubsystem:
            if target == current_subsystem:
                continue
            
            state = self._subsystems[target]
            if not state.active:
                continue
            
            # Calculate suggestion score
            synergy = self.get_synergy_strength(current_subsystem, target)
            availability = 1.0 / (1.0 + state.pending_requests)
            performance = state.success_rate
            
            score = synergy * availability * performance
            
            if score > 0.1:
                suggestions.append((target, score))
        
        suggestions.sort(key=lambda x: -x[1])
        return suggestions


# =============================================================================
# GOAL-DIRECTED BEHAVIOR
# =============================================================================

@dataclass
class GoalNode:
    """A node in the goal hierarchy."""
    goal: CognitiveGoal
    parent: Optional['GoalNode'] = None
    children: List['GoalNode'] = field(default_factory=list)
    
    # Execution state
    assigned_processes: List[str] = field(default_factory=list)
    progress: float = 0.0
    
    def is_leaf(self) -> bool:
        return len(self.children) == 0
    
    def is_root(self) -> bool:
        return self.parent is None


class GoalManager:
    """
    Manages goal-directed behavior for the AGI system.
    
    Goals form a hierarchy where high-level goals decompose
    into subgoals that can be pursued in parallel.
    """
    
    def __init__(self, atomspace: AtomSpace):
        self.atomspace = atomspace
        
        # Goal hierarchy
        self._goals: Dict[str, GoalNode] = {}
        self._root_goals: List[str] = []
        
        # Active goals
        self._active_goals: Set[str] = set()
        
        # Goal achievement history
        self._history: List[Tuple[str, float, bool]] = []  # (goal_id, time, success)
        
        self._lock = threading.RLock()
    
    def add_goal(
        self,
        goal: CognitiveGoal,
        parent_id: Optional[str] = None
    ) -> str:
        """Add a goal to the hierarchy."""
        with self._lock:
            node = GoalNode(goal=goal)
            
            if parent_id and parent_id in self._goals:
                parent = self._goals[parent_id]
                node.parent = parent
                parent.children.append(node)
            else:
                self._root_goals.append(goal.goal_id)
            
            self._goals[goal.goal_id] = node
            
            # Create goal atom
            goal_handle = self.atomspace.add_node(
                AtomType.CONCEPT_NODE,
                f"Goal:{goal.name}",
                tv=TruthValue(goal.priority, 0.9),
                av=AttentionValue(sti=goal.priority, lti=0.5)
            )
            goal.handle = goal_handle
            
            return goal.goal_id
    
    def activate_goal(self, goal_id: str) -> bool:
        """Activate a goal for pursuit."""
        with self._lock:
            if goal_id not in self._goals:
                return False
            
            node = self._goals[goal_id]
            node.goal.state = GoalState.ACTIVE
            self._active_goals.add(goal_id)
            
            return True
    
    def complete_goal(self, goal_id: str, success: bool = True):
        """Mark a goal as completed."""
        with self._lock:
            if goal_id not in self._goals:
                return
            
            node = self._goals[goal_id]
            node.goal.state = GoalState.ACHIEVED if success else GoalState.FAILED
            self._active_goals.discard(goal_id)
            
            self._history.append((goal_id, time.time(), success))
            
            # Update parent progress
            if node.parent:
                self._update_parent_progress(node.parent)
    
    def _update_parent_progress(self, node: GoalNode):
        """Update parent goal progress based on children."""
        if not node.children:
            return
        
        completed = sum(1 for c in node.children if c.goal.state in [GoalState.ACHIEVED, GoalState.FAILED])
        successful = sum(1 for c in node.children if c.goal.state == GoalState.ACHIEVED)
        
        node.progress = completed / len(node.children)
        
        # Check if parent is complete
        if completed == len(node.children):
            success = successful == len(node.children)
            self.complete_goal(node.goal.goal_id, success)
    
    def get_active_goals(self) -> List[CognitiveGoal]:
        """Get all active goals."""
        return [self._goals[gid].goal for gid in self._active_goals]
    
    def get_next_goal(self) -> Optional[CognitiveGoal]:
        """Get the highest priority active goal."""
        active = self.get_active_goals()
        if not active:
            return None
        
        return max(active, key=lambda g: g.priority)
    
    def decompose_goal(
        self,
        goal_id: str,
        subgoals: List[CognitiveGoal]
    ) -> List[str]:
        """Decompose a goal into subgoals."""
        subgoal_ids = []
        for subgoal in subgoals:
            sid = self.add_goal(subgoal, parent_id=goal_id)
            subgoal_ids.append(sid)
        return subgoal_ids
    
    def get_goal_tree(self, goal_id: str) -> Dict[str, Any]:
        """Get the goal tree rooted at a goal."""
        if goal_id not in self._goals:
            return {}
        
        node = self._goals[goal_id]
        return self._node_to_dict(node)
    
    def _node_to_dict(self, node: GoalNode) -> Dict[str, Any]:
        """Convert a goal node to dictionary."""
        return {
            'goal_id': node.goal.goal_id,
            'name': node.goal.name,
            'state': node.goal.state.name,
            'priority': node.goal.priority,
            'progress': node.progress,
            'children': [self._node_to_dict(c) for c in node.children]
        }


# =============================================================================
# SELF-REFLECTION
# =============================================================================

@dataclass
class IntrospectionResult:
    """Result of an introspection operation."""
    aspect: str
    observations: List[str]
    metrics: Dict[str, float]
    recommendations: List[str]
    timestamp: float = field(default_factory=time.time)


class SelfReflection:
    """
    Implements self-reflection and introspection capabilities.
    
    The system can observe and reason about its own cognitive processes,
    enabling self-improvement and adaptation.
    """
    
    def __init__(self, atomspace: AtomSpace, synergy: CognitiveSynergy):
        self.atomspace = atomspace
        self.synergy = synergy
        
        # Introspection history
        self._introspection_log: List[IntrospectionResult] = []
        
        # Self-model
        self._self_model: Dict[str, Any] = {}
        
        self._lock = threading.Lock()
    
    def introspect_attention(self) -> IntrospectionResult:
        """Introspect the attention system."""
        observations = []
        metrics = {}
        recommendations = []
        
        # Analyze attention distribution
        atoms = list(self.atomspace)
        if atoms:
            stis = [a.attention_value.sti for a in atoms]
            avg_sti = sum(stis) / len(stis)
            max_sti = max(stis)
            
            metrics['avg_sti'] = avg_sti
            metrics['max_sti'] = max_sti
            metrics['focus_ratio'] = len([s for s in stis if s > 0.5]) / len(stis)
            
            observations.append(f"Average STI: {avg_sti:.3f}")
            observations.append(f"Focus ratio: {metrics['focus_ratio']:.2%}")
            
            if metrics['focus_ratio'] < 0.01:
                recommendations.append("Attention too diffuse - increase focus")
            elif metrics['focus_ratio'] > 0.5:
                recommendations.append("Attention too narrow - broaden scope")
        
        result = IntrospectionResult(
            aspect="attention",
            observations=observations,
            metrics=metrics,
            recommendations=recommendations
        )
        
        self._introspection_log.append(result)
        return result
    
    def introspect_knowledge(self) -> IntrospectionResult:
        """Introspect the knowledge base."""
        observations = []
        metrics = {}
        recommendations = []
        
        # Analyze knowledge structure
        stats = self.atomspace.get_stats()
        
        metrics['total_atoms'] = stats.get('total_atoms', 0)
        metrics['node_count'] = stats.get('node_count', 0)
        metrics['link_count'] = stats.get('link_count', 0)
        
        if metrics['total_atoms'] > 0:
            link_ratio = metrics['link_count'] / metrics['total_atoms']
            metrics['link_ratio'] = link_ratio
            
            observations.append(f"Total atoms: {metrics['total_atoms']}")
            observations.append(f"Link ratio: {link_ratio:.2f}")
            
            if link_ratio < 0.3:
                recommendations.append("Knowledge is sparse - need more connections")
            elif link_ratio > 0.8:
                recommendations.append("Knowledge is dense - may need pruning")
        
        result = IntrospectionResult(
            aspect="knowledge",
            observations=observations,
            metrics=metrics,
            recommendations=recommendations
        )
        
        self._introspection_log.append(result)
        return result
    
    def introspect_performance(self) -> IntrospectionResult:
        """Introspect system performance."""
        observations = []
        metrics = {}
        recommendations = []
        
        # Analyze subsystem performance
        for subsystem, state in self.synergy._subsystems.items():
            if state.active:
                metrics[f"{subsystem.name}_success_rate"] = state.success_rate
                metrics[f"{subsystem.name}_response_time"] = state.avg_response_time
                
                if state.success_rate < 0.8:
                    recommendations.append(f"{subsystem.name} has low success rate")
                if state.avg_response_time > 1.0:
                    recommendations.append(f"{subsystem.name} is slow")
        
        observations.append(f"Active subsystems: {sum(1 for s in self.synergy._subsystems.values() if s.active)}")
        
        result = IntrospectionResult(
            aspect="performance",
            observations=observations,
            metrics=metrics,
            recommendations=recommendations
        )
        
        self._introspection_log.append(result)
        return result
    
    def update_self_model(self):
        """Update the internal self-model."""
        with self._lock:
            # Aggregate recent introspections
            recent = self._introspection_log[-10:]
            
            for result in recent:
                self._self_model[result.aspect] = {
                    'metrics': result.metrics,
                    'last_update': result.timestamp
                }
    
    def get_self_assessment(self) -> Dict[str, Any]:
        """Get overall self-assessment."""
        self.update_self_model()
        
        assessment = {
            'timestamp': time.time(),
            'aspects': self._self_model.copy(),
            'overall_health': self._calculate_health_score()
        }
        
        return assessment
    
    def _calculate_health_score(self) -> float:
        """Calculate overall system health score."""
        scores = []
        
        if 'attention' in self._self_model:
            focus = self._self_model['attention']['metrics'].get('focus_ratio', 0.1)
            scores.append(min(1.0, focus * 10))  # Normalize
        
        if 'knowledge' in self._self_model:
            atoms = self._self_model['knowledge']['metrics'].get('total_atoms', 0)
            scores.append(min(1.0, atoms / 1000))  # Normalize
        
        if 'performance' in self._self_model:
            for key, value in self._self_model['performance']['metrics'].items():
                if 'success_rate' in key:
                    scores.append(value)
        
        return sum(scores) / len(scores) if scores else 0.5


# =============================================================================
# CREATIVITY ENGINE
# =============================================================================

class CreativityMode(Enum):
    """Modes of creative generation."""
    COMBINATION = auto()    # Combine existing concepts
    ANALOGY = auto()        # Draw analogies
    MUTATION = auto()       # Mutate existing ideas
    ABSTRACTION = auto()    # Abstract from examples
    EXPLORATION = auto()    # Random exploration


class CreativityEngine:
    """
    Generates novel ideas and concepts.
    
    Creativity emerges from:
    - Combining disparate concepts
    - Drawing analogies across domains
    - Mutating existing knowledge
    - Abstracting patterns
    """
    
    def __init__(self, atomspace: AtomSpace):
        self.atomspace = atomspace
        
        # Generated ideas
        self._ideas: List[Tuple[AtomHandle, CreativityMode, float]] = []
        
        # Creativity parameters
        self.novelty_threshold = 0.3
        self.combination_depth = 2
        
        self._lock = threading.Lock()
    
    def generate_idea(
        self,
        mode: CreativityMode = None,
        seed_atoms: List[AtomHandle] = None
    ) -> Optional[AtomHandle]:
        """Generate a novel idea."""
        if mode is None:
            mode = random.choice(list(CreativityMode))
        
        if mode == CreativityMode.COMBINATION:
            return self._generate_combination(seed_atoms)
        elif mode == CreativityMode.ANALOGY:
            return self._generate_analogy(seed_atoms)
        elif mode == CreativityMode.MUTATION:
            return self._generate_mutation(seed_atoms)
        elif mode == CreativityMode.ABSTRACTION:
            return self._generate_abstraction(seed_atoms)
        elif mode == CreativityMode.EXPLORATION:
            return self._generate_exploration()
        
        return None
    
    def _generate_combination(
        self,
        seed_atoms: List[AtomHandle] = None
    ) -> Optional[AtomHandle]:
        """Generate idea by combining concepts."""
        # Select concepts to combine
        if seed_atoms and len(seed_atoms) >= 2:
            atoms = [self.atomspace.get_atom(h) for h in seed_atoms[:2]]
        else:
            # Select random high-attention concepts
            concepts = [a for a in self.atomspace.get_atoms_by_type(AtomType.CONCEPT_NODE)
                       if a.attention_value.sti > 0.3]
            if len(concepts) < 2:
                return None
            atoms = random.sample(concepts, 2)
        
        atoms = [a for a in atoms if a is not None]
        if len(atoms) < 2:
            return None
        
        # Create combined concept
        combined_name = f"{atoms[0].name}_{atoms[1].name}_blend"
        
        # Check novelty
        existing = self.atomspace.get_node(AtomType.CONCEPT_NODE, combined_name)
        if existing:
            return None
        
        # Create new concept
        combined_handle = self.atomspace.add_node(
            AtomType.CONCEPT_NODE,
            combined_name,
            tv=TruthValue(0.5, 0.3),  # Low confidence for new idea
            av=AttentionValue(sti=0.6, lti=0.3)
        )
        
        # Link to source concepts
        for atom in atoms:
            self.atomspace.add_link(
                AtomType.INHERITANCE_LINK,
                [combined_handle, atom.handle],
                tv=TruthValue(0.7, 0.5)
            )
        
        self._ideas.append((combined_handle, CreativityMode.COMBINATION, time.time()))
        return combined_handle
    
    def _generate_analogy(
        self,
        seed_atoms: List[AtomHandle] = None
    ) -> Optional[AtomHandle]:
        """Generate idea by drawing analogy."""
        # Find similar structures in different domains
        if seed_atoms:
            source = self.atomspace.get_atom(seed_atoms[0])
        else:
            concepts = list(self.atomspace.get_atoms_by_type(AtomType.CONCEPT_NODE))
            if not concepts:
                return None
            source = random.choice(concepts)
        
        if not source:
            return None
        
        # Find structurally similar atoms
        source_links = list(self.atomspace.get_incoming(source.handle))
        
        # Look for atoms with similar link patterns
        candidates = []
        for atom in self.atomspace:
            if atom.handle == source.handle:
                continue
            
            atom_links = list(self.atomspace.get_incoming(atom.handle))
            
            # Compare link types
            source_types = set(l.atom_type for l in source_links)
            atom_types = set(l.atom_type for l in atom_links)
            
            similarity = len(source_types & atom_types) / max(1, len(source_types | atom_types))
            
            if similarity > 0.5:
                candidates.append((atom, similarity))
        
        if not candidates:
            return None
        
        # Select best candidate
        candidates.sort(key=lambda x: -x[1])
        target = candidates[0][0]
        
        # Create analogy link
        analogy_handle = self.atomspace.add_link(
            AtomType.SIMILARITY_LINK,
            [source.handle, target.handle],
            tv=TruthValue(candidates[0][1], 0.4)
        )
        
        self._ideas.append((analogy_handle, CreativityMode.ANALOGY, time.time()))
        return analogy_handle
    
    def _generate_mutation(
        self,
        seed_atoms: List[AtomHandle] = None
    ) -> Optional[AtomHandle]:
        """Generate idea by mutating existing concept."""
        if seed_atoms:
            source = self.atomspace.get_atom(seed_atoms[0])
        else:
            concepts = list(self.atomspace.get_atoms_by_type(AtomType.CONCEPT_NODE))
            if not concepts:
                return None
            source = random.choice(concepts)
        
        if not source or not isinstance(source, Node):
            return None
        
        # Mutate name
        mutations = [
            f"anti_{source.name}",
            f"super_{source.name}",
            f"quasi_{source.name}",
            f"{source.name}_variant"
        ]
        
        mutated_name = random.choice(mutations)
        
        # Check novelty
        existing = self.atomspace.get_node(AtomType.CONCEPT_NODE, mutated_name)
        if existing:
            return None
        
        # Create mutated concept
        mutated_handle = self.atomspace.add_node(
            AtomType.CONCEPT_NODE,
            mutated_name,
            tv=TruthValue(0.4, 0.2),
            av=AttentionValue(sti=0.5, lti=0.2)
        )
        
        # Link to source
        self.atomspace.add_link(
            AtomType.SIMILARITY_LINK,
            [mutated_handle, source.handle],
            tv=TruthValue(0.6, 0.4)
        )
        
        self._ideas.append((mutated_handle, CreativityMode.MUTATION, time.time()))
        return mutated_handle
    
    def _generate_abstraction(
        self,
        seed_atoms: List[AtomHandle] = None
    ) -> Optional[AtomHandle]:
        """Generate idea by abstracting from examples."""
        if seed_atoms and len(seed_atoms) >= 2:
            examples = [self.atomspace.get_atom(h) for h in seed_atoms]
        else:
            # Find similar concepts
            concepts = list(self.atomspace.get_atoms_by_type(AtomType.CONCEPT_NODE))
            if len(concepts) < 3:
                return None
            examples = random.sample(concepts, 3)
        
        examples = [e for e in examples if e is not None]
        if len(examples) < 2:
            return None
        
        # Create abstract concept
        abstract_name = f"Abstract_{int(time.time() * 1000) % 10000}"
        
        abstract_handle = self.atomspace.add_node(
            AtomType.CONCEPT_NODE,
            abstract_name,
            tv=TruthValue(0.6, 0.4),
            av=AttentionValue(sti=0.4, lti=0.4)
        )
        
        # Link examples to abstraction
        for example in examples:
            self.atomspace.add_link(
                AtomType.INHERITANCE_LINK,
                [example.handle, abstract_handle],
                tv=TruthValue(0.8, 0.5)
            )
        
        self._ideas.append((abstract_handle, CreativityMode.ABSTRACTION, time.time()))
        return abstract_handle
    
    def _generate_exploration(self) -> Optional[AtomHandle]:
        """Generate random exploratory idea."""
        # Create random concept
        random_name = f"Explore_{random.randint(0, 99999):05d}"
        
        handle = self.atomspace.add_node(
            AtomType.CONCEPT_NODE,
            random_name,
            tv=TruthValue(0.3, 0.1),
            av=AttentionValue(sti=0.3, lti=0.1)
        )
        
        # Connect to random existing concepts
        concepts = list(self.atomspace.get_atoms_by_type(AtomType.CONCEPT_NODE))
        if concepts:
            targets = random.sample(concepts, min(2, len(concepts)))
            for target in targets:
                self.atomspace.add_link(
                    AtomType.SIMILARITY_LINK,
                    [handle, target.handle],
                    tv=TruthValue(0.3, 0.2)
                )
        
        self._ideas.append((handle, CreativityMode.EXPLORATION, time.time()))
        return handle
    
    def evaluate_novelty(self, handle: AtomHandle) -> float:
        """Evaluate the novelty of an idea."""
        atom = self.atomspace.get_atom(handle)
        if not atom:
            return 0.0
        
        # Check similarity to existing atoms
        similarities = []
        for other in self.atomspace:
            if other.handle == handle:
                continue
            
            # Simple similarity based on shared links
            atom_links = set(l.handle for l in self.atomspace.get_incoming(handle))
            other_links = set(l.handle for l in self.atomspace.get_incoming(other.handle))
            
            if atom_links or other_links:
                jaccard = len(atom_links & other_links) / len(atom_links | other_links)
                similarities.append(jaccard)
        
        if not similarities:
            return 1.0  # Completely novel
        
        avg_similarity = sum(similarities) / len(similarities)
        return 1.0 - avg_similarity
    
    def get_recent_ideas(self, n: int = 10) -> List[Tuple[AtomHandle, CreativityMode, float]]:
        """Get recent generated ideas."""
        return self._ideas[-n:]


# =============================================================================
# EMERGENT INTELLIGENCE SERVICE
# =============================================================================

class EmergentIntelligenceService:
    """
    The main emergent intelligence service.
    
    Integrates all cognitive components to produce intelligent behavior
    that emerges from their interaction.
    """
    
    def __init__(self, atomspace: AtomSpace):
        self.atomspace = atomspace
        
        # Components
        self.synergy = CognitiveSynergy(atomspace)
        self.goals = GoalManager(atomspace)
        self.reflection = SelfReflection(atomspace, self.synergy)
        self.creativity = CreativityEngine(atomspace)
        
        # Service state
        self._running = False
        self._main_loop_thread: Optional[threading.Thread] = None
        
        # Configuration
        self.cycle_interval = 0.1  # 10 Hz
        self.introspection_interval = 60.0  # Every minute
        self.creativity_interval = 30.0  # Every 30 seconds
        
        # Timing
        self._last_introspection = 0
        self._last_creativity = 0
        
        self._lock = threading.RLock()
    
    @property
    def service_name(self) -> str:
        return "emergent_intelligence_service"
    
    def start(self) -> bool:
        """Start the emergent intelligence service."""
        if self._running:
            return False
        
        self._running = True
        self._main_loop_thread = threading.Thread(
            target=self._main_loop,
            daemon=True,
            name="emergent-intelligence"
        )
        self._main_loop_thread.start()
        
        return True
    
    def stop(self) -> bool:
        """Stop the service."""
        if not self._running:
            return False
        
        self._running = False
        if self._main_loop_thread:
            self._main_loop_thread.join(timeout=2.0)
        
        return True
    
    def _main_loop(self):
        """Main cognitive loop."""
        while self._running:
            try:
                current_time = time.time()
                
                # Process synergy requests
                self.synergy.process_requests()
                
                # Goal-directed behavior
                self._pursue_goals()
                
                # Periodic introspection
                if current_time - self._last_introspection >= self.introspection_interval:
                    self._introspect()
                    self._last_introspection = current_time
                
                # Periodic creativity
                if current_time - self._last_creativity >= self.creativity_interval:
                    self._be_creative()
                    self._last_creativity = current_time
                
            except Exception as e:
                pass  # Log in production
            
            time.sleep(self.cycle_interval)
    
    def _pursue_goals(self):
        """Pursue active goals."""
        goal = self.goals.get_next_goal()
        if not goal:
            return
        
        # Request synergy for goal pursuit
        suggestions = self.synergy.suggest_synergy(
            CognitiveSubsystem.PLN,
            CognitiveContext()
        )
        
        # Use suggested subsystems
        for subsystem, score in suggestions[:2]:
            self.synergy.request_synergy(
                source=CognitiveSubsystem.PLN,
                target=subsystem,
                request_type="goal_support",
                payload={'goal_id': goal.goal_id},
                priority=goal.priority * score
            )
    
    def _introspect(self):
        """Perform self-introspection."""
        self.reflection.introspect_attention()
        self.reflection.introspect_knowledge()
        self.reflection.introspect_performance()
    
    def _be_creative(self):
        """Generate creative ideas."""
        # Select mode based on current state
        assessment = self.reflection.get_self_assessment()
        
        if assessment['overall_health'] < 0.5:
            # System struggling - try exploration
            mode = CreativityMode.EXPLORATION
        else:
            # System healthy - try combination or analogy
            mode = random.choice([CreativityMode.COMBINATION, CreativityMode.ANALOGY])
        
        idea = self.creativity.generate_idea(mode)
        
        if idea:
            novelty = self.creativity.evaluate_novelty(idea)
            if novelty < self.creativity.novelty_threshold:
                # Not novel enough - remove
                self.atomspace.remove_atom(idea)
    
    def status(self) -> Dict[str, Any]:
        """Get service status."""
        return {
            'running': self._running,
            'active_goals': len(self.goals._active_goals),
            'pending_synergy_requests': len(self.synergy._requests),
            'recent_ideas': len(self.creativity._ideas),
            'self_assessment': self.reflection.get_self_assessment()
        }


# Export
__all__ = [
    'CognitiveSubsystem',
    'SubsystemState',
    'SynergyRequest',
    'CognitiveSynergy',
    'GoalNode',
    'GoalManager',
    'IntrospectionResult',
    'SelfReflection',
    'CreativityMode',
    'CreativityEngine',
    'EmergentIntelligenceService',
]
