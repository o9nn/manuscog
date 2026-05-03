"""
OpenCog Inferno AGI - Cognitive Memory Manager
==============================================

This module implements the cognitive memory management system,
a kernel-level service that manages the lifecycle of cognitive
resources (atoms, patterns, goals) with attention-based economics.

The memory manager implements:
- Attention-based garbage collection (forgetting)
- Working memory management
- Long-term memory consolidation
- Distributed memory coordination
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
import heapq
from collections import defaultdict
import json

from kernel.cognitive.types import (
    Atom, AtomHandle, TruthValue, AttentionValue,
    CognitiveService, MemoryService, CognitiveContext,
    LRUCache, CircularBuffer
)
from atomspace.hypergraph.atomspace import AtomSpace


# =============================================================================
# MEMORY REGIONS
# =============================================================================

@dataclass
class MemoryConfig:
    """Configuration for the memory manager."""
    forgetting_threshold: float = 0.01
    consolidation_interval: float = 60.0
    max_working_memory: int = 1000
    decay_rate: float = 0.99


class MemoryRegion(Enum):
    """Types of memory regions in the cognitive system."""
    SENSORY = auto()        # Very short-term, high capacity
    WORKING = auto()        # Short-term, limited capacity
    EPISODIC = auto()       # Medium-term, event-based
    SEMANTIC = auto()       # Long-term, conceptual
    PROCEDURAL = auto()     # Long-term, skill-based
    PERMANENT = auto()       # Never forgotten (VLTI atoms)


@dataclass
class MemoryRegionConfig:
    """Configuration for a memory region."""
    region: MemoryRegion
    capacity: int
    decay_rate: float
    consolidation_threshold: float
    min_sti_threshold: float
    
    @staticmethod
    def default_configs() -> Dict[MemoryRegion, 'MemoryRegionConfig']:
        return {
            MemoryRegion.SENSORY: MemoryRegionConfig(
                region=MemoryRegion.SENSORY,
                capacity=10000,
                decay_rate=0.5,
                consolidation_threshold=0.3,
                min_sti_threshold=-1.0
            ),
            MemoryRegion.WORKING: MemoryRegionConfig(
                region=MemoryRegion.WORKING,
                capacity=1000,
                decay_rate=0.9,
                consolidation_threshold=0.5,
                min_sti_threshold=0.0
            ),
            MemoryRegion.EPISODIC: MemoryRegionConfig(
                region=MemoryRegion.EPISODIC,
                capacity=50000,
                decay_rate=0.99,
                consolidation_threshold=0.7,
                min_sti_threshold=-0.5
            ),
            MemoryRegion.SEMANTIC: MemoryRegionConfig(
                region=MemoryRegion.SEMANTIC,
                capacity=500000,
                decay_rate=0.999,
                consolidation_threshold=0.8,
                min_sti_threshold=-0.8
            ),
            MemoryRegion.PROCEDURAL: MemoryRegionConfig(
                region=MemoryRegion.PROCEDURAL,
                capacity=100000,
                decay_rate=0.999,
                consolidation_threshold=0.9,
                min_sti_threshold=-0.9
            ),
            MemoryRegion.PERMANENT: MemoryRegionConfig(
                region=MemoryRegion.PERMANENT,
                capacity=float('inf'),
                decay_rate=1.0,
                consolidation_threshold=1.0,
                min_sti_threshold=-1.0
            ),
        }


# =============================================================================
# MEMORY ALLOCATION TRACKING
# =============================================================================

@dataclass
class MemoryAllocation:
    """Tracks memory allocation for an atom."""
    handle: AtomHandle
    region: MemoryRegion
    allocated_at: float = field(default_factory=time.time)
    last_accessed: float = field(default_factory=time.time)
    access_count: int = 0
    size_bytes: int = 0
    
    def touch(self):
        """Update access tracking."""
        self.last_accessed = time.time()
        self.access_count += 1


@dataclass
class MemoryStats:
    """Statistics for memory usage."""
    total_atoms: int = 0
    total_bytes: int = 0
    atoms_by_region: Dict[MemoryRegion, int] = field(default_factory=dict)
    bytes_by_region: Dict[MemoryRegion, int] = field(default_factory=dict)
    allocations: int = 0
    deallocations: int = 0
    consolidations: int = 0
    forgetting_events: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'total_atoms': self.total_atoms,
            'total_bytes': self.total_bytes,
            'atoms_by_region': {r.name: c for r, c in self.atoms_by_region.items()},
            'bytes_by_region': {r.name: b for r, b in self.bytes_by_region.items()},
            'allocations': self.allocations,
            'deallocations': self.deallocations,
            'consolidations': self.consolidations,
            'forgetting_events': self.forgetting_events
        }


# =============================================================================
# FORGETTING QUEUE (MIN-HEAP BY IMPORTANCE)
# =============================================================================

class ForgettingQueue:
    """
    Priority queue for atoms eligible for forgetting.
    Atoms with lowest importance are forgotten first.
    """
    
    def __init__(self):
        self._heap: List[Tuple[float, float, AtomHandle]] = []  # (importance, timestamp, handle)
        self._entries: Dict[AtomHandle, Tuple[float, float, AtomHandle]] = {}
        self._lock = threading.Lock()
        self._counter = 0  # For tie-breaking
    
    def push(self, handle: AtomHandle, importance: float):
        """Add or update an atom in the forgetting queue."""
        with self._lock:
            if handle in self._entries:
                # Mark old entry as removed
                self._entries[handle] = None
            
            entry = (importance, time.time(), handle)
            self._entries[handle] = entry
            heapq.heappush(self._heap, entry)
    
    def pop(self) -> Optional[AtomHandle]:
        """Remove and return the least important atom."""
        with self._lock:
            while self._heap:
                importance, timestamp, handle = heapq.heappop(self._heap)
                entry = self._entries.get(handle)
                if entry is not None and entry[0] == importance:
                    del self._entries[handle]
                    return handle
            return None
    
    def remove(self, handle: AtomHandle):
        """Remove an atom from the queue."""
        with self._lock:
            if handle in self._entries:
                self._entries[handle] = None
    
    def peek(self) -> Optional[Tuple[AtomHandle, float]]:
        """Peek at the least important atom without removing."""
        with self._lock:
            while self._heap:
                importance, timestamp, handle = self._heap[0]
                entry = self._entries.get(handle)
                if entry is not None and entry[0] == importance:
                    return (handle, importance)
                heapq.heappop(self._heap)
            return None
    
    def __len__(self) -> int:
        with self._lock:
            return sum(1 for e in self._entries.values() if e is not None)


# =============================================================================
# COGNITIVE MEMORY MANAGER
# =============================================================================

class CognitiveMemoryManager(MemoryService):
    """
    Kernel-level cognitive memory management service.
    
    This service manages the lifecycle of atoms in the cognitive system,
    implementing attention-based economics where:
    - Atoms pay "rent" to stay in memory based on their importance
    - Low-importance atoms are gradually forgotten
    - Important atoms are consolidated to long-term memory
    - VLTI (Very Long-Term Important) atoms are never forgotten
    
    The memory manager integrates with the AtomSpace and provides
    the foundation for cognitive resource management.
    """
    
    def __init__(
        self,
        atomspace: AtomSpace,
        configs: Optional[Dict[MemoryRegion, MemoryRegionConfig]] = None
    ):
        self.atomspace = atomspace
        self.configs = configs or MemoryRegionConfig.default_configs()
        
        # Allocation tracking
        self._allocations: Dict[AtomHandle, MemoryAllocation] = {}
        self._region_atoms: Dict[MemoryRegion, Set[AtomHandle]] = {
            r: set() for r in MemoryRegion
        }
        
        # Forgetting queue
        self._forgetting_queue = ForgettingQueue()
        
        # Statistics
        self._stats = MemoryStats()
        
        # Service state
        self._running = False
        self._lock = threading.RLock()
        
        # Background threads
        self._decay_thread: Optional[threading.Thread] = None
        self._consolidation_thread: Optional[threading.Thread] = None
        self._forgetting_thread: Optional[threading.Thread] = None
        
        # Configuration
        self.decay_interval = 1.0  # seconds
        self.consolidation_interval = 10.0  # seconds
        self.forgetting_interval = 5.0  # seconds
        
        # Callbacks
        self._on_forget_callbacks: List[Callable[[AtomHandle], None]] = []
        self._on_consolidate_callbacks: List[Callable[[AtomHandle, MemoryRegion], None]] = []
    
    # =========================================================================
    # SERVICE INTERFACE
    # =========================================================================
    
    @property
    def service_name(self) -> str:
        return "cognitive_memory_manager"
    
    def start(self) -> bool:
        """Start the memory management service."""
        if self._running:
            return False
        
        self._running = True
        
        # Start background threads
        self._decay_thread = threading.Thread(
            target=self._decay_loop,
            daemon=True,
            name="memory-decay"
        )
        self._decay_thread.start()
        
        self._consolidation_thread = threading.Thread(
            target=self._consolidation_loop,
            daemon=True,
            name="memory-consolidation"
        )
        self._consolidation_thread.start()
        
        self._forgetting_thread = threading.Thread(
            target=self._forgetting_loop,
            daemon=True,
            name="memory-forgetting"
        )
        self._forgetting_thread.start()
        
        # Subscribe to AtomSpace events
        self.atomspace.subscribe('add', self._on_atom_added)
        self.atomspace.subscribe('remove', self._on_atom_removed)
        self.atomspace.subscribe('update_av', self._on_attention_updated)
        
        return True
    
    def stop(self) -> bool:
        """Stop the memory management service."""
        if not self._running:
            return False
        
        self._running = False
        
        # Wait for threads to finish
        if self._decay_thread:
            self._decay_thread.join(timeout=2.0)
        if self._consolidation_thread:
            self._consolidation_thread.join(timeout=2.0)
        if self._forgetting_thread:
            self._forgetting_thread.join(timeout=2.0)
        
        # Unsubscribe from events
        self.atomspace.unsubscribe('add', self._on_atom_added)
        self.atomspace.unsubscribe('remove', self._on_atom_removed)
        self.atomspace.unsubscribe('update_av', self._on_attention_updated)
        
        return True
    
    def status(self) -> Dict[str, Any]:
        """Get service status."""
        return {
            'running': self._running,
            'stats': self._stats.to_dict(),
            'forgetting_queue_size': len(self._forgetting_queue),
            'region_counts': {
                r.name: len(atoms) 
                for r, atoms in self._region_atoms.items()
            }
        }
    
    # =========================================================================
    # MEMORY SERVICE INTERFACE
    # =========================================================================
    
    def allocate_atom(self, atom: Atom) -> AtomHandle:
        """Allocate memory for an atom."""
        with self._lock:
            # Determine initial region based on attention
            region = self._determine_region(atom.attention_value)
            
            # Create allocation record
            allocation = MemoryAllocation(
                handle=atom.handle,
                region=region,
                size_bytes=self._estimate_size(atom)
            )
            
            self._allocations[atom.handle] = allocation
            self._region_atoms[region].add(atom.handle)
            
            # Update stats
            self._stats.total_atoms += 1
            self._stats.total_bytes += allocation.size_bytes
            self._stats.atoms_by_region[region] = \
                self._stats.atoms_by_region.get(region, 0) + 1
            self._stats.bytes_by_region[region] = \
                self._stats.bytes_by_region.get(region, 0) + allocation.size_bytes
            self._stats.allocations += 1
            
            # Add to forgetting queue if not permanent
            if region != MemoryRegion.PERMANENT and not atom.attention_value.vlti:
                importance = self._calculate_importance(atom)
                self._forgetting_queue.push(atom.handle, importance)
            
            return atom.handle
    
    def retrieve_atom(self, handle: AtomHandle) -> Optional[Atom]:
        """Retrieve an atom and update access tracking."""
        with self._lock:
            allocation = self._allocations.get(handle)
            if allocation:
                allocation.touch()
            
            return self.atomspace.get_atom(handle)
    
    def release_atom(self, handle: AtomHandle) -> bool:
        """Release an atom from memory."""
        with self._lock:
            allocation = self._allocations.get(handle)
            if not allocation:
                return False
            
            # Update stats
            self._stats.total_atoms -= 1
            self._stats.total_bytes -= allocation.size_bytes
            self._stats.atoms_by_region[allocation.region] = \
                self._stats.atoms_by_region.get(allocation.region, 1) - 1
            self._stats.bytes_by_region[allocation.region] = \
                self._stats.bytes_by_region.get(allocation.region, allocation.size_bytes) - allocation.size_bytes
            self._stats.deallocations += 1
            
            # Remove from tracking
            self._region_atoms[allocation.region].discard(handle)
            del self._allocations[handle]
            self._forgetting_queue.remove(handle)
            
            return True
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory statistics."""
        return self._stats.to_dict()
    
    # =========================================================================
    # REGION MANAGEMENT
    # =========================================================================
    
    def _determine_region(self, av: AttentionValue) -> MemoryRegion:
        """Determine the appropriate memory region for an atom."""
        if av.vlti:
            return MemoryRegion.PERMANENT
        elif av.sti > 0.7:
            return MemoryRegion.WORKING
        elif av.sti > 0.3:
            return MemoryRegion.EPISODIC
        elif av.lti > 0.5:
            return MemoryRegion.SEMANTIC
        else:
            return MemoryRegion.SENSORY
    
    def move_to_region(self, handle: AtomHandle, new_region: MemoryRegion) -> bool:
        """Move an atom to a different memory region."""
        with self._lock:
            allocation = self._allocations.get(handle)
            if not allocation:
                return False
            
            old_region = allocation.region
            if old_region == new_region:
                return True
            
            # Update region tracking
            self._region_atoms[old_region].discard(handle)
            self._region_atoms[new_region].add(handle)
            
            # Update stats
            self._stats.atoms_by_region[old_region] = \
                self._stats.atoms_by_region.get(old_region, 1) - 1
            self._stats.atoms_by_region[new_region] = \
                self._stats.atoms_by_region.get(new_region, 0) + 1
            self._stats.bytes_by_region[old_region] = \
                self._stats.bytes_by_region.get(old_region, allocation.size_bytes) - allocation.size_bytes
            self._stats.bytes_by_region[new_region] = \
                self._stats.bytes_by_region.get(new_region, 0) + allocation.size_bytes
            
            allocation.region = new_region
            
            return True
    
    def get_region(self, handle: AtomHandle) -> Optional[MemoryRegion]:
        """Get the memory region of an atom."""
        allocation = self._allocations.get(handle)
        return allocation.region if allocation else None
    
    def get_atoms_in_region(self, region: MemoryRegion) -> Set[AtomHandle]:
        """Get all atoms in a memory region."""
        with self._lock:
            return self._region_atoms[region].copy()
    
    # =========================================================================
    # IMPORTANCE CALCULATION
    # =========================================================================
    
    def _calculate_importance(self, atom: Atom) -> float:
        """
        Calculate importance score for forgetting priority.
        Lower importance = more likely to be forgotten.
        """
        av = atom.attention_value
        tv = atom.truth_value
        
        # Base importance from attention
        importance = av.sti * 0.5 + av.lti * 0.3
        
        # Boost from truth value confidence
        importance += tv.confidence * 0.1
        
        # Boost from incoming links (more connected = more important)
        importance += min(0.1, len(atom.incoming) * 0.01)
        
        # VLTI atoms have maximum importance
        if av.vlti:
            importance = float('inf')
        
        return importance
    
    def _estimate_size(self, atom: Atom) -> int:
        """Estimate memory size of an atom in bytes."""
        # Base size for atom structure
        size = 200  # Base overhead
        
        # Add size for name if node
        from kernel.cognitive.types import Node
        if isinstance(atom, Node):
            size += len(atom.name.encode('utf-8'))
        
        # Add size for outgoing if link
        from kernel.cognitive.types import Link
        if isinstance(atom, Link):
            size += len(atom.outgoing) * 50  # Handle size estimate
        
        # Add metadata size
        size += len(json.dumps(atom.metadata)) if atom.metadata else 0
        
        return size
    
    # =========================================================================
    # BACKGROUND PROCESSES
    # =========================================================================
    
    def _decay_loop(self):
        """Background loop for attention decay."""
        while self._running:
            try:
                # Apply decay to all atoms
                self.atomspace.decay_attention(rate=0.995)
                
                # Update forgetting queue priorities
                self._update_forgetting_priorities()
                
            except Exception as e:
                pass  # Log error in production
            
            time.sleep(self.decay_interval)
    
    def _consolidation_loop(self):
        """Background loop for memory consolidation."""
        while self._running:
            try:
                self._consolidate_memories()
            except Exception as e:
                pass  # Log error in production
            
            time.sleep(self.consolidation_interval)
    
    def _forgetting_loop(self):
        """Background loop for forgetting low-importance atoms."""
        while self._running:
            try:
                self._forget_low_importance()
            except Exception as e:
                pass  # Log error in production
            
            time.sleep(self.forgetting_interval)
    
    def _update_forgetting_priorities(self):
        """Update priorities in the forgetting queue."""
        with self._lock:
            for handle, allocation in list(self._allocations.items()):
                if allocation.region == MemoryRegion.PERMANENT:
                    continue
                
                atom = self.atomspace.get_atom(handle)
                if atom and not atom.attention_value.vlti:
                    importance = self._calculate_importance(atom)
                    self._forgetting_queue.push(handle, importance)
    
    def _consolidate_memories(self):
        """Consolidate memories from short-term to long-term."""
        with self._lock:
            # Check working memory atoms for consolidation
            for handle in list(self._region_atoms[MemoryRegion.WORKING]):
                atom = self.atomspace.get_atom(handle)
                if not atom:
                    continue
                
                allocation = self._allocations.get(handle)
                if not allocation:
                    continue
                
                # Check if atom should be consolidated
                config = self.configs[MemoryRegion.WORKING]
                if atom.attention_value.lti >= config.consolidation_threshold:
                    # Move to semantic memory
                    self.move_to_region(handle, MemoryRegion.SEMANTIC)
                    self._stats.consolidations += 1
                    
                    # Notify callbacks
                    for callback in self._on_consolidate_callbacks:
                        try:
                            callback(handle, MemoryRegion.SEMANTIC)
                        except:
                            pass
            
            # Check episodic memory for semantic consolidation
            for handle in list(self._region_atoms[MemoryRegion.EPISODIC]):
                atom = self.atomspace.get_atom(handle)
                if not atom:
                    continue
                
                config = self.configs[MemoryRegion.EPISODIC]
                if atom.attention_value.lti >= config.consolidation_threshold:
                    self.move_to_region(handle, MemoryRegion.SEMANTIC)
                    self._stats.consolidations += 1
    
    def _forget_low_importance(self):
        """Forget atoms with low importance."""
        # Check each region for capacity overflow
        for region in [MemoryRegion.SENSORY, MemoryRegion.WORKING, 
                       MemoryRegion.EPISODIC]:
            config = self.configs[region]
            current_count = len(self._region_atoms[region])
            
            if current_count > config.capacity:
                # Need to forget some atoms
                to_forget = current_count - int(config.capacity * 0.9)
                forgotten = 0
                
                while forgotten < to_forget:
                    result = self._forgetting_queue.peek()
                    if not result:
                        break
                    
                    handle, importance = result
                    allocation = self._allocations.get(handle)
                    
                    if allocation and allocation.region == region:
                        # Check if importance is below threshold
                        atom = self.atomspace.get_atom(handle)
                        if atom and atom.attention_value.sti < config.min_sti_threshold:
                            self._forget_atom(handle)
                            forgotten += 1
                        else:
                            # Remove from queue but don't forget
                            self._forgetting_queue.pop()
                    else:
                        # Atom not in this region, skip
                        self._forgetting_queue.pop()
    
    def _forget_atom(self, handle: AtomHandle):
        """Forget (remove) an atom from the system."""
        # Notify callbacks before removal
        for callback in self._on_forget_callbacks:
            try:
                callback(handle)
            except:
                pass
        
        # Remove from AtomSpace
        self.atomspace.remove_atom(handle, recursive=False)
        
        # Release memory
        self.release_atom(handle)
        
        self._stats.forgetting_events += 1
    
    # =========================================================================
    # EVENT HANDLERS
    # =========================================================================
    
    def _on_atom_added(self, event):
        """Handle atom addition event."""
        atom = event.new_value
        if atom and atom.handle not in self._allocations:
            self.allocate_atom(atom)
    
    def _on_atom_removed(self, event):
        """Handle atom removal event."""
        self.release_atom(event.handle)
    
    def _on_attention_updated(self, event):
        """Handle attention value update event."""
        handle = event.handle
        new_av = event.new_value
        
        if not new_av:
            return
        
        # Check if region should change
        new_region = self._determine_region(new_av)
        current_region = self.get_region(handle)
        
        if current_region and new_region != current_region:
            self.move_to_region(handle, new_region)
        
        # Update forgetting queue
        atom = self.atomspace.get_atom(handle)
        if atom and not new_av.vlti:
            importance = self._calculate_importance(atom)
            self._forgetting_queue.push(handle, importance)
    
    # =========================================================================
    # CALLBACK REGISTRATION
    # =========================================================================
    
    def on_forget(self, callback: Callable[[AtomHandle], None]):
        """Register callback for forgetting events."""
        self._on_forget_callbacks.append(callback)
    
    def on_consolidate(self, callback: Callable[[AtomHandle, MemoryRegion], None]):
        """Register callback for consolidation events."""
        self._on_consolidate_callbacks.append(callback)
    
    # =========================================================================
    # WORKING MEMORY MANAGEMENT
    # =========================================================================
    
    def get_working_memory(self) -> List[Atom]:
        """Get all atoms currently in working memory."""
        atoms = []
        for handle in self._region_atoms[MemoryRegion.WORKING]:
            atom = self.atomspace.get_atom(handle)
            if atom:
                atoms.append(atom)
        return atoms
    
    def add_to_working_memory(self, handle: AtomHandle) -> bool:
        """Explicitly add an atom to working memory."""
        atom = self.atomspace.get_atom(handle)
        if not atom:
            return False
        
        # Boost attention
        new_av = atom.attention_value.stimulate(0.5)
        self.atomspace.set_attention_value(handle, new_av)
        
        # Move to working memory
        return self.move_to_region(handle, MemoryRegion.WORKING)
    
    def clear_working_memory(self):
        """Clear working memory (move atoms to appropriate regions)."""
        for handle in list(self._region_atoms[MemoryRegion.WORKING]):
            atom = self.atomspace.get_atom(handle)
            if atom:
                # Determine new region based on LTI
                if atom.attention_value.lti > 0.5:
                    self.move_to_region(handle, MemoryRegion.SEMANTIC)
                else:
                    self.move_to_region(handle, MemoryRegion.EPISODIC)


# =============================================================================
# WORKING MEMORY CONTEXT
# =============================================================================

class WorkingMemoryContext:
    """
    Context manager for working memory operations.
    Automatically manages attention for atoms used in a cognitive task.
    """
    
    def __init__(self, memory_manager: CognitiveMemoryManager):
        self.memory_manager = memory_manager
        self.active_atoms: Set[AtomHandle] = set()
        self._original_regions: Dict[AtomHandle, MemoryRegion] = {}
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Decay attention for all active atoms
        for handle in self.active_atoms:
            atom = self.memory_manager.atomspace.get_atom(handle)
            if atom:
                new_av = atom.attention_value.decay(0.8)
                self.memory_manager.atomspace.set_attention_value(handle, new_av)
        return False
    
    def activate(self, handle: AtomHandle):
        """Activate an atom in working memory."""
        if handle not in self.active_atoms:
            self.active_atoms.add(handle)
            region = self.memory_manager.get_region(handle)
            if region:
                self._original_regions[handle] = region
            self.memory_manager.add_to_working_memory(handle)
    
    def get_active_atoms(self) -> List[Atom]:
        """Get all active atoms."""
        atoms = []
        for handle in self.active_atoms:
            atom = self.memory_manager.atomspace.get_atom(handle)
            if atom:
                atoms.append(atom)
        return atoms


# Export
__all__ = [
    'MemoryConfig',
    'MemoryRegion',
    'MemoryRegionConfig',
    'MemoryAllocation',
    'MemoryStats',
    'ForgettingQueue',
    'CognitiveMemoryManager',
    'WorkingMemoryContext',
]
