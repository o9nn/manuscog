"""
OpenCog Inferno AGI - Core Cognitive Types
==========================================

This module defines the fundamental types for the cognitive kernel.
These types form the basis of all cognitive processing in the AGI OS,
where thinking and reasoning are kernel-level services.

The design follows the Inferno OS philosophy where everything is a file,
extended to: everything is a cognitive resource accessible through the
namespace hierarchy.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import (
    Dict, List, Optional, Set, Tuple, Any, Callable, 
    TypeVar, Generic, Union, Protocol, Iterator
)
from abc import ABC, abstractmethod
import uuid
import time
import hashlib
import threading
from collections import defaultdict


# =============================================================================
# FUNDAMENTAL COGNITIVE PRIMITIVES
# =============================================================================

class AtomType(Enum):
    """
    Fundamental atom types in the cognitive hypergraph.
    These represent the basic building blocks of knowledge representation.
    """
    # Node Types
    CONCEPT_NODE = auto()           # Abstract concepts
    PREDICATE_NODE = auto()         # Predicates for logical reasoning
    SCHEMA_NODE = auto()            # Procedural schemas
    GROUNDED_SCHEMA_NODE = auto()   # Schemas with executable code
    VARIABLE_NODE = auto()          # Logic variables for pattern matching
    NUMBER_NODE = auto()            # Numeric values
    TYPE_NODE = auto()              # Type definitions
    ANCHOR_NODE = auto()            # Named anchors in the atomspace
    
    # Link Types - Logical
    INHERITANCE_LINK = auto()       # IS-A relationships
    SIMILARITY_LINK = auto()        # Similarity relationships
    IMPLICATION_LINK = auto()       # Logical implication
    EQUIVALENCE_LINK = auto()       # Logical equivalence
    AND_LINK = auto()               # Logical conjunction
    OR_LINK = auto()                # Logical disjunction
    NOT_LINK = auto()               # Logical negation
    
    # Link Types - Relational
    EVALUATION_LINK = auto()        # Predicate evaluation
    EXECUTION_LINK = auto()         # Schema execution
    LIST_LINK = auto()              # Ordered list
    SET_LINK = auto()               # Unordered set
    MEMBER_LINK = auto()            # Set membership
    
    # Link Types - Contextual
    CONTEXT_LINK = auto()           # Contextual relationships
    ATTENTION_LINK = auto()         # Attention-based connections
    HEBBIAN_LINK = auto()           # Hebbian learning associations
    
    # Link Types - Temporal
    SEQUENTIAL_AND_LINK = auto()    # Temporal sequence
    PREDICTIVE_IMPLICATION_LINK = auto()  # Predictive relationships
    
    # Meta Types
    DEFINE_LINK = auto()            # Definition links
    BIND_LINK = auto()              # Variable bindings
    QUOTE_LINK = auto()             # Quoted expressions
    
    # Frame Types
    DEFINED_FRAME_NODE = auto()     # Frame definitions
    FRAME_ELEMENT_NODE = auto()     # Frame elements


@dataclass(frozen=True)
class TruthValue:
    """
    Probabilistic truth value for atoms.
    
    OpenCog uses a multi-valued truth system based on:
    - strength: probability/confidence in the truth
    - confidence: certainty about the strength estimate
    - count: evidence count (for learning)
    
    This follows Probabilistic Logic Networks (PLN) semantics.
    """
    strength: float = 1.0       # [0, 1] - probability of truth
    confidence: float = 0.9     # [0, 1] - certainty of estimate
    count: float = 1.0          # evidence count
    
    def __post_init__(self):
        # Validate bounds
        object.__setattr__(self, 'strength', max(0.0, min(1.0, self.strength)))
        object.__setattr__(self, 'confidence', max(0.0, min(1.0, self.confidence)))
        object.__setattr__(self, 'count', max(0.0, self.count))
    
    @staticmethod
    def merge(tv1: 'TruthValue', tv2: 'TruthValue') -> 'TruthValue':
        """Merge two truth values using revision formula."""
        if tv1.confidence == 0 and tv2.confidence == 0:
            return TruthValue(0.5, 0.0, 0.0)
        
        # Weighted average based on confidence
        total_conf = tv1.confidence + tv2.confidence
        new_strength = (tv1.strength * tv1.confidence + 
                       tv2.strength * tv2.confidence) / total_conf
        new_confidence = min(0.99, total_conf / (total_conf + 1))
        new_count = tv1.count + tv2.count
        
        return TruthValue(new_strength, new_confidence, new_count)
    
    @staticmethod
    def deduction(tv1: 'TruthValue', tv2: 'TruthValue') -> 'TruthValue':
        """PLN deduction: if A->B and B->C then A->C."""
        sAB, cAB = tv1.strength, tv1.confidence
        sBC, cBC = tv2.strength, tv2.confidence
        
        # Deduction formula
        sAC = sAB * sBC
        cAC = cAB * cBC * min(sAB, sBC)  # Simplified
        
        return TruthValue(sAC, cAC, min(tv1.count, tv2.count))
    
    @staticmethod
    def induction(tv1: 'TruthValue', tv2: 'TruthValue', 
                  prior: float = 0.5) -> 'TruthValue':
        """PLN induction: if A->B and A->C then B->C (with prior)."""
        sAB, cAB = tv1.strength, tv1.confidence
        sAC, cAC = tv2.strength, tv2.confidence
        
        # Induction formula (simplified)
        sBC = (sAB * sAC + prior * (1 - sAB)) / (sAB + prior * (1 - sAB) + 0.0001)
        cBC = cAB * cAC * sAB
        
        return TruthValue(sBC, cBC, min(tv1.count, tv2.count))


@dataclass
class AttentionValue:
    """
    Attention value for cognitive resource allocation.
    
    Based on OpenCog's ECAN (Economic Attention Networks):
    - sti: Short-Term Importance - current relevance
    - lti: Long-Term Importance - persistent relevance  
    - vlti: Very Long-Term Importance - permanent importance flag
    """
    sti: float = 0.0            # Short-term importance [-1, 1] normalized
    lti: float = 0.0            # Long-term importance [0, 1]
    vlti: bool = False          # Very long-term importance (permanent)
    
    # Attention economics parameters
    rent: float = 0.01          # Cost per cycle for being in attention
    wage: float = 0.0           # Reward for being useful
    
    def decay(self, rate: float = 0.99) -> 'AttentionValue':
        """Apply attention decay."""
        if self.vlti:
            return self  # VLTI atoms don't decay
        return AttentionValue(
            sti=self.sti * rate,
            lti=self.lti * rate,
            vlti=self.vlti,
            rent=self.rent,
            wage=self.wage
        )
    
    def stimulate(self, amount: float) -> 'AttentionValue':
        """Increase attention (stimulus)."""
        return AttentionValue(
            sti=min(1.0, self.sti + amount),
            lti=self.lti,
            vlti=self.vlti,
            rent=self.rent,
            wage=self.wage
        )
    
    @property
    def in_attentional_focus(self) -> bool:
        """Check if atom is in the attentional focus."""
        return self.sti > 0.5 or self.vlti


# =============================================================================
# ATOM HIERARCHY
# =============================================================================

@dataclass
class AtomHandle:
    """
    Unique identifier for atoms in the cognitive space.
    Designed for distributed operation across Inferno nodes.
    """
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))
    node_id: str = "local"      # Originating node in distributed system
    version: int = 0            # Version for conflict resolution
    
    def __hash__(self):
        return hash((self.uuid, self.node_id))
    
    def __eq__(self, other):
        if not isinstance(other, AtomHandle):
            return False
        return self.uuid == other.uuid and self.node_id == other.node_id


class Atom(ABC):
    """
    Base class for all atoms in the cognitive hypergraph.
    
    Atoms are the fundamental units of knowledge representation.
    They can be either Nodes (terminal) or Links (connecting atoms).
    """
    
    def __init__(
        self,
        atom_type: AtomType,
        truth_value: Optional[TruthValue] = None,
        attention_value: Optional[AttentionValue] = None,
        handle: Optional[AtomHandle] = None
    ):
        self.handle = handle or AtomHandle()
        self.atom_type = atom_type
        self.truth_value = truth_value or TruthValue()
        self.attention_value = attention_value or AttentionValue()
        self.incoming: Set[AtomHandle] = set()  # Links pointing to this atom
        self.metadata: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self.created_at = time.time()
        self.modified_at = time.time()
    
    @abstractmethod
    def get_hash(self) -> str:
        """Get content-based hash for deduplication."""
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Serialize atom to dictionary."""
        pass
    
    @classmethod
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Atom':
        """Deserialize atom from dictionary."""
        pass
    
    def add_incoming(self, link_handle: AtomHandle):
        """Add incoming link reference."""
        with self._lock:
            self.incoming.add(link_handle)
            self.modified_at = time.time()
    
    def remove_incoming(self, link_handle: AtomHandle):
        """Remove incoming link reference."""
        with self._lock:
            self.incoming.discard(link_handle)
            self.modified_at = time.time()
    
    def update_truth_value(self, tv: TruthValue):
        """Update truth value with revision."""
        with self._lock:
            self.truth_value = TruthValue.merge(self.truth_value, tv)
            self.modified_at = time.time()
    
    def update_attention(self, av: AttentionValue):
        """Update attention value."""
        with self._lock:
            self.attention_value = av
            self.modified_at = time.time()


class Node(Atom):
    """
    Terminal atom representing a concept, predicate, or value.
    Nodes are the leaves of the hypergraph.
    """
    
    def __init__(
        self,
        atom_type: AtomType,
        name: str,
        truth_value: Optional[TruthValue] = None,
        attention_value: Optional[AttentionValue] = None,
        handle: Optional[AtomHandle] = None
    ):
        super().__init__(atom_type, truth_value, attention_value, handle)
        self.name = name
    
    def get_hash(self) -> str:
        """Content hash based on type and name."""
        content = f"{self.atom_type.name}:{self.name}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'class': 'Node',
            'handle': {
                'uuid': self.handle.uuid,
                'node_id': self.handle.node_id,
                'version': self.handle.version
            },
            'atom_type': self.atom_type.name,
            'name': self.name,
            'truth_value': {
                'strength': self.truth_value.strength,
                'confidence': self.truth_value.confidence,
                'count': self.truth_value.count
            },
            'attention_value': {
                'sti': self.attention_value.sti,
                'lti': self.attention_value.lti,
                'vlti': self.attention_value.vlti
            },
            'metadata': self.metadata,
            'created_at': self.created_at,
            'modified_at': self.modified_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Node':
        handle = AtomHandle(
            uuid=data['handle']['uuid'],
            node_id=data['handle']['node_id'],
            version=data['handle']['version']
        )
        tv = TruthValue(
            strength=data['truth_value']['strength'],
            confidence=data['truth_value']['confidence'],
            count=data['truth_value']['count']
        )
        av = AttentionValue(
            sti=data['attention_value']['sti'],
            lti=data['attention_value']['lti'],
            vlti=data['attention_value']['vlti']
        )
        node = cls(
            atom_type=AtomType[data['atom_type']],
            name=data['name'],
            truth_value=tv,
            attention_value=av,
            handle=handle
        )
        node.metadata = data.get('metadata', {})
        node.created_at = data.get('created_at', time.time())
        node.modified_at = data.get('modified_at', time.time())
        return node
    
    def __repr__(self):
        return f"Node({self.atom_type.name}, '{self.name}')"


class Link(Atom):
    """
    Hyperedge connecting multiple atoms.
    Links form the structure of the knowledge hypergraph.
    """
    
    def __init__(
        self,
        atom_type: AtomType,
        outgoing: List[AtomHandle],
        truth_value: Optional[TruthValue] = None,
        attention_value: Optional[AttentionValue] = None,
        handle: Optional[AtomHandle] = None
    ):
        super().__init__(atom_type, truth_value, attention_value, handle)
        self.outgoing = outgoing  # Ordered list of target atom handles
    
    @property
    def arity(self) -> int:
        """Number of atoms this link connects."""
        return len(self.outgoing)
    
    def get_hash(self) -> str:
        """Content hash based on type and outgoing set."""
        outgoing_str = ",".join(h.uuid for h in self.outgoing)
        content = f"{self.atom_type.name}:[{outgoing_str}]"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'class': 'Link',
            'handle': {
                'uuid': self.handle.uuid,
                'node_id': self.handle.node_id,
                'version': self.handle.version
            },
            'atom_type': self.atom_type.name,
            'outgoing': [
                {'uuid': h.uuid, 'node_id': h.node_id, 'version': h.version}
                for h in self.outgoing
            ],
            'truth_value': {
                'strength': self.truth_value.strength,
                'confidence': self.truth_value.confidence,
                'count': self.truth_value.count
            },
            'attention_value': {
                'sti': self.attention_value.sti,
                'lti': self.attention_value.lti,
                'vlti': self.attention_value.vlti
            },
            'metadata': self.metadata,
            'created_at': self.created_at,
            'modified_at': self.modified_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Link':
        handle = AtomHandle(
            uuid=data['handle']['uuid'],
            node_id=data['handle']['node_id'],
            version=data['handle']['version']
        )
        outgoing = [
            AtomHandle(uuid=h['uuid'], node_id=h['node_id'], version=h['version'])
            for h in data['outgoing']
        ]
        tv = TruthValue(
            strength=data['truth_value']['strength'],
            confidence=data['truth_value']['confidence'],
            count=data['truth_value']['count']
        )
        av = AttentionValue(
            sti=data['attention_value']['sti'],
            lti=data['attention_value']['lti'],
            vlti=data['attention_value']['vlti']
        )
        link = cls(
            atom_type=AtomType[data['atom_type']],
            outgoing=outgoing,
            truth_value=tv,
            attention_value=av,
            handle=handle
        )
        link.metadata = data.get('metadata', {})
        link.created_at = data.get('created_at', time.time())
        link.modified_at = data.get('modified_at', time.time())
        return link
    
    def __repr__(self):
        return f"Link({self.atom_type.name}, arity={self.arity})"


# =============================================================================
# COGNITIVE PROCESS TYPES
# =============================================================================

class CognitiveProcessState(Enum):
    """States for cognitive processes in the kernel."""
    IDLE = auto()
    READY = auto()
    RUNNING = auto()
    WAITING = auto()
    BLOCKED = auto()
    TERMINATED = auto()


@dataclass
class CognitiveContext:
    """
    Execution context for cognitive processes.
    Similar to process context in traditional OS but for cognitive operations.
    """
    process_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    parent_id: Optional[str] = None
    state: CognitiveProcessState = CognitiveProcessState.IDLE
    
    # Attention budget for this process
    attention_budget: float = 1.0
    priority: int = 0
    
    # Working memory for this context
    working_atoms: Set[AtomHandle] = field(default_factory=set)
    goal_atoms: Set[AtomHandle] = field(default_factory=set)
    
    # Execution state
    program_counter: int = 0
    call_stack: List[Dict[str, Any]] = field(default_factory=list)
    local_bindings: Dict[str, AtomHandle] = field(default_factory=dict)
    
    # Resource tracking
    cycles_used: int = 0
    atoms_accessed: int = 0
    inferences_made: int = 0
    
    # Timing
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    finished_at: Optional[float] = None


class InferenceType(Enum):
    """Types of inference operations."""
    DEDUCTION = auto()      # A->B, B->C => A->C
    INDUCTION = auto()      # A->B, A->C => B->C
    ABDUCTION = auto()      # A->B, C->B => A->C
    REVISION = auto()       # Merge evidence
    MODUS_PONENS = auto()   # A, A->B => B
    UNIFICATION = auto()    # Pattern matching


@dataclass
class InferenceResult:
    """Result of an inference operation."""
    inference_type: InferenceType
    premises: List[AtomHandle]
    conclusion: Optional[Atom]
    truth_value: TruthValue
    confidence: float
    computation_cost: float
    timestamp: float = field(default_factory=time.time)


# =============================================================================
# KERNEL SERVICE INTERFACES
# =============================================================================

class CognitiveService(Protocol):
    """Protocol for cognitive kernel services."""
    
    @property
    def service_name(self) -> str:
        """Name of the service."""
        ...
    
    def start(self) -> bool:
        """Start the service."""
        ...
    
    def stop(self) -> bool:
        """Stop the service."""
        ...
    
    def status(self) -> Dict[str, Any]:
        """Get service status."""
        ...


class MemoryService(CognitiveService, Protocol):
    """Protocol for memory management services."""
    
    def allocate_atom(self, atom: Atom) -> AtomHandle:
        """Allocate space for an atom."""
        ...
    
    def retrieve_atom(self, handle: AtomHandle) -> Optional[Atom]:
        """Retrieve an atom by handle."""
        ...
    
    def release_atom(self, handle: AtomHandle) -> bool:
        """Release an atom from memory."""
        ...
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        ...


class ReasoningService(CognitiveService, Protocol):
    """Protocol for reasoning/inference services."""
    
    def infer(
        self, 
        premises: List[AtomHandle], 
        inference_type: InferenceType
    ) -> Optional[InferenceResult]:
        """Perform inference."""
        ...
    
    def query(self, pattern: Atom) -> List[Dict[str, AtomHandle]]:
        """Query the knowledge base with a pattern."""
        ...


class AttentionService(CognitiveService, Protocol):
    """Protocol for attention allocation services."""
    
    def get_attentional_focus(self) -> Set[AtomHandle]:
        """Get atoms currently in attentional focus."""
        ...
    
    def stimulate(self, handle: AtomHandle, amount: float) -> bool:
        """Stimulate an atom's attention."""
        ...
    
    def spread_attention(self) -> int:
        """Spread attention through the hypergraph."""
        ...


class LearningService(CognitiveService, Protocol):
    """Protocol for learning services."""
    
    def learn_pattern(self, examples: List[Atom]) -> Optional[Atom]:
        """Learn a pattern from examples."""
        ...
    
    def reinforce(self, handle: AtomHandle, reward: float) -> bool:
        """Reinforce an atom based on reward."""
        ...


class KernelService(Protocol):
    """Protocol for kernel services."""
    
    @property
    def service_name(self) -> str:
        """Get the service name."""
        ...
    
    def start(self) -> bool:
        """Start the service."""
        ...
    
    def stop(self) -> bool:
        """Stop the service."""
        ...
    
    def status(self) -> Dict[str, Any]:
        """Get service status."""
        ...


# =============================================================================
# STYX/9P COGNITIVE FILE SYSTEM TYPES
# =============================================================================

class CogFSNodeType(Enum):
    """Types of nodes in the cognitive file system."""
    DIRECTORY = auto()
    ATOM_FILE = auto()
    QUERY_FILE = auto()
    INFERENCE_FILE = auto()
    ATTENTION_FILE = auto()
    PROCESS_FILE = auto()
    STATS_FILE = auto()


@dataclass
class CogFSNode:
    """
    Node in the cognitive file system.
    
    Following Inferno's philosophy, cognitive resources are exposed
    as files in a namespace hierarchy:
    
    /cog/
        atoms/          - Direct atom access
        types/          - Atoms organized by type
        attention/      - Attention-based views
        inference/      - Inference operations
        learning/       - Learning operations
        processes/      - Cognitive processes
        stats/          - System statistics
    """
    name: str
    node_type: CogFSNodeType
    parent: Optional['CogFSNode'] = None
    children: Dict[str, 'CogFSNode'] = field(default_factory=dict)
    
    # For atom files
    atom_handle: Optional[AtomHandle] = None
    
    # Permissions (following Unix model)
    mode: int = 0o644
    owner: str = "cognitive"
    group: str = "kernel"
    
    # Timestamps
    atime: float = field(default_factory=time.time)
    mtime: float = field(default_factory=time.time)
    ctime: float = field(default_factory=time.time)
    
    def get_path(self) -> str:
        """Get full path of this node."""
        if self.parent is None:
            return "/" + self.name
        return self.parent.get_path() + "/" + self.name
    
    def add_child(self, child: 'CogFSNode') -> bool:
        """Add a child node."""
        if self.node_type != CogFSNodeType.DIRECTORY:
            return False
        child.parent = self
        self.children[child.name] = child
        self.mtime = time.time()
        return True


# =============================================================================
# DISTRIBUTED COORDINATION TYPES
# =============================================================================

@dataclass
class NodeInfo:
    """Information about a node in the distributed cognitive system."""
    node_id: str
    address: str
    port: int
    capabilities: Set[str] = field(default_factory=set)
    load: float = 0.0
    atom_count: int = 0
    last_heartbeat: float = field(default_factory=time.time)
    is_alive: bool = True


class ConsensusState(Enum):
    """States for distributed consensus."""
    FOLLOWER = auto()
    CANDIDATE = auto()
    LEADER = auto()


@dataclass
class CognitiveMessage:
    """
    Message for distributed cognitive coordination.
    Uses Styx/9P-inspired protocol for cognitive operations.
    """
    msg_type: str
    sender: str
    recipient: str
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    
    # For reliable delivery
    requires_ack: bool = False
    retry_count: int = 0
    max_retries: int = 3


# =============================================================================
# PATTERN MATCHING TYPES
# =============================================================================

@dataclass
class Pattern:
    """
    Pattern for matching against the atomspace.
    Supports variables for flexible matching.
    """
    root: Atom
    variables: Dict[str, AtomType] = field(default_factory=dict)
    constraints: List[Callable[[Dict[str, Atom]], bool]] = field(default_factory=list)
    
    def matches(self, atom: Atom, bindings: Dict[str, Atom]) -> bool:
        """Check if atom matches this pattern with given bindings."""
        # Implementation in pattern matching module
        pass


@dataclass
class BindingSet:
    """Set of variable bindings from pattern matching."""
    bindings: Dict[str, AtomHandle]
    confidence: float = 1.0
    source_atoms: Set[AtomHandle] = field(default_factory=set)


# =============================================================================
# GOAL AND PLANNING TYPES
# =============================================================================

class GoalState(Enum):
    """States for goals in the cognitive system."""
    PENDING = auto()
    ACTIVE = auto()
    ACHIEVED = auto()
    FAILED = auto()
    ABANDONED = auto()


@dataclass
class CognitiveGoal:
    """
    A goal in the cognitive system.
    Goals drive cognitive processing and attention allocation.
    """
    goal_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = ""
    description: str = ""
    target_pattern: Optional[Pattern] = None
    state: GoalState = GoalState.PENDING
    priority: float = 0.5
    
    # Subgoals for hierarchical planning
    parent_goal: Optional[str] = None
    subgoals: List[str] = field(default_factory=list)
    
    # Progress tracking
    progress: float = 0.0
    attempts: int = 0
    max_attempts: int = 100
    
    # Timing
    created_at: float = field(default_factory=time.time)
    deadline: Optional[float] = None
    achieved_at: Optional[float] = None


# =============================================================================
# UTILITY TYPES
# =============================================================================

T = TypeVar('T')

class LRUCache(Generic[T]):
    """LRU cache for cognitive resources."""
    
    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self.cache: Dict[str, Tuple[T, float]] = {}
        self.access_order: List[str] = []
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[T]:
        with self._lock:
            if key in self.cache:
                self.access_order.remove(key)
                self.access_order.append(key)
                return self.cache[key][0]
            return None
    
    def put(self, key: str, value: T):
        with self._lock:
            if key in self.cache:
                self.access_order.remove(key)
            elif len(self.cache) >= self.capacity:
                oldest = self.access_order.pop(0)
                del self.cache[oldest]
            
            self.cache[key] = (value, time.time())
            self.access_order.append(key)
    
    def remove(self, key: str) -> bool:
        with self._lock:
            if key in self.cache:
                del self.cache[key]
                self.access_order.remove(key)
                return True
            return False


class CircularBuffer(Generic[T]):
    """Circular buffer for cognitive event streams."""
    
    def __init__(self, capacity: int = 1000):
        self.capacity = capacity
        self.buffer: List[Optional[T]] = [None] * capacity
        self.head = 0
        self.tail = 0
        self.size = 0
        self._lock = threading.Lock()
    
    def push(self, item: T):
        with self._lock:
            self.buffer[self.tail] = item
            self.tail = (self.tail + 1) % self.capacity
            if self.size < self.capacity:
                self.size += 1
            else:
                self.head = (self.head + 1) % self.capacity
    
    def pop(self) -> Optional[T]:
        with self._lock:
            if self.size == 0:
                return None
            item = self.buffer[self.head]
            self.head = (self.head + 1) % self.capacity
            self.size -= 1
            return item
    
    def __iter__(self) -> Iterator[T]:
        with self._lock:
            idx = self.head
            for _ in range(self.size):
                yield self.buffer[idx]
                idx = (idx + 1) % self.capacity


# Export all types
__all__ = [
    # Enums
    'AtomType', 'CognitiveProcessState', 'InferenceType', 
    'CogFSNodeType', 'ConsensusState', 'GoalState',
    
    # Core types
    'TruthValue', 'AttentionValue', 'AtomHandle',
    'Atom', 'Node', 'Link',
    
    # Process types
    'CognitiveContext', 'InferenceResult',
    
    # Service protocols
    'CognitiveService', 'MemoryService', 'ReasoningService',
    'AttentionService', 'LearningService', 'KernelService',
    
    # File system types
    'CogFSNode',
    
    # Distributed types
    'NodeInfo', 'CognitiveMessage',
    
    # Pattern types
    'Pattern', 'BindingSet',
    
    # Goal types
    'CognitiveGoal',
    
    # Utility types
    'LRUCache', 'CircularBuffer',
]
