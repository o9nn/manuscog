"""
OpenCog Inferno AGI - AtomSpace Hypergraph Implementation
=========================================================

The AtomSpace is the central knowledge representation system.
It implements a weighted, labeled hypergraph where:
- Nodes represent concepts, predicates, and values
- Links (hyperedges) connect multiple atoms
- Each atom has truth values and attention values

This implementation is designed for kernel-level integration,
providing the foundational data structure for all cognitive operations.
"""

from __future__ import annotations
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from typing import Dict, List, Optional, Set, Tuple, Any, Iterator, Callable
from collections import defaultdict
import threading
import time
import json
import hashlib
from dataclasses import dataclass, field

from kernel.cognitive.types import (
    Atom, Node, Link, AtomHandle, AtomType,
    TruthValue, AttentionValue, LRUCache, CircularBuffer
)


# =============================================================================
# ATOMSPACE INDEX STRUCTURES
# =============================================================================

class TypeIndex:
    """Index atoms by their type for fast type-based queries."""
    
    def __init__(self):
        self._index: Dict[AtomType, Set[AtomHandle]] = defaultdict(set)
        self._lock = threading.RLock()
    
    def add(self, atom_type: AtomType, handle: AtomHandle):
        with self._lock:
            self._index[atom_type].add(handle)
    
    def remove(self, atom_type: AtomType, handle: AtomHandle):
        with self._lock:
            self._index[atom_type].discard(handle)
    
    def get(self, atom_type: AtomType) -> Set[AtomHandle]:
        with self._lock:
            return self._index[atom_type].copy()
    
    def get_all_types(self) -> List[AtomType]:
        with self._lock:
            return list(self._index.keys())
    
    def count(self, atom_type: AtomType) -> int:
        with self._lock:
            return len(self._index[atom_type])


class NameIndex:
    """Index nodes by their name for fast name-based lookups."""
    
    def __init__(self):
        # Maps (type, name) -> handle for unique lookup
        self._index: Dict[Tuple[AtomType, str], AtomHandle] = {}
        # Maps name -> set of handles for name-only queries
        self._name_only: Dict[str, Set[AtomHandle]] = defaultdict(set)
        self._lock = threading.RLock()
    
    def add(self, atom_type: AtomType, name: str, handle: AtomHandle):
        with self._lock:
            self._index[(atom_type, name)] = handle
            self._name_only[name].add(handle)
    
    def remove(self, atom_type: AtomType, name: str, handle: AtomHandle):
        with self._lock:
            key = (atom_type, name)
            if key in self._index:
                del self._index[key]
            self._name_only[name].discard(handle)
    
    def get(self, atom_type: AtomType, name: str) -> Optional[AtomHandle]:
        with self._lock:
            return self._index.get((atom_type, name))
    
    def get_by_name(self, name: str) -> Set[AtomHandle]:
        with self._lock:
            return self._name_only[name].copy()


class OutgoingIndex:
    """Index links by their outgoing set for pattern matching."""
    
    def __init__(self):
        # Maps atom handle -> set of links that reference it
        self._index: Dict[AtomHandle, Set[AtomHandle]] = defaultdict(set)
        self._lock = threading.RLock()
    
    def add(self, link_handle: AtomHandle, outgoing: List[AtomHandle]):
        with self._lock:
            for target in outgoing:
                self._index[target].add(link_handle)
    
    def remove(self, link_handle: AtomHandle, outgoing: List[AtomHandle]):
        with self._lock:
            for target in outgoing:
                self._index[target].discard(link_handle)
    
    def get_incoming(self, handle: AtomHandle) -> Set[AtomHandle]:
        """Get all links that point to this atom."""
        with self._lock:
            return self._index[handle].copy()


class AttentionIndex:
    """Index atoms by attention value for focus management."""
    
    def __init__(self, focus_threshold: float = 0.5):
        self.focus_threshold = focus_threshold
        self._sti_sorted: List[Tuple[float, AtomHandle]] = []
        self._vlti_atoms: Set[AtomHandle] = set()
        self._lock = threading.RLock()
    
    def update(self, handle: AtomHandle, av: AttentionValue):
        with self._lock:
            # Remove old entry if exists
            self._sti_sorted = [
                (sti, h) for sti, h in self._sti_sorted 
                if h != handle
            ]
            # Add new entry
            self._sti_sorted.append((av.sti, handle))
            self._sti_sorted.sort(reverse=True, key=lambda x: x[0])
            
            # Track VLTI atoms
            if av.vlti:
                self._vlti_atoms.add(handle)
            else:
                self._vlti_atoms.discard(handle)
    
    def remove(self, handle: AtomHandle):
        with self._lock:
            self._sti_sorted = [
                (sti, h) for sti, h in self._sti_sorted 
                if h != handle
            ]
            self._vlti_atoms.discard(handle)
    
    def get_attentional_focus(self, limit: int = 100) -> List[AtomHandle]:
        """Get atoms in attentional focus (high STI)."""
        with self._lock:
            focus = []
            for sti, handle in self._sti_sorted[:limit]:
                if sti >= self.focus_threshold:
                    focus.append(handle)
                else:
                    break
            return focus
    
    def get_top_n(self, n: int) -> List[Tuple[float, AtomHandle]]:
        """Get top N atoms by STI."""
        with self._lock:
            return self._sti_sorted[:n].copy()
    
    def get_vlti_atoms(self) -> Set[AtomHandle]:
        """Get all VLTI (permanent) atoms."""
        with self._lock:
            return self._vlti_atoms.copy()


class ContentHashIndex:
    """Index atoms by content hash for deduplication."""
    
    def __init__(self):
        self._index: Dict[str, AtomHandle] = {}
        self._lock = threading.RLock()
    
    def add(self, content_hash: str, handle: AtomHandle):
        with self._lock:
            self._index[content_hash] = handle
    
    def remove(self, content_hash: str):
        with self._lock:
            if content_hash in self._index:
                del self._index[content_hash]
    
    def get(self, content_hash: str) -> Optional[AtomHandle]:
        with self._lock:
            return self._index.get(content_hash)
    
    def exists(self, content_hash: str) -> bool:
        with self._lock:
            return content_hash in self._index


# =============================================================================
# ATOMSPACE EVENTS
# =============================================================================

@dataclass
class AtomSpaceEvent:
    """Event emitted by AtomSpace operations."""
    event_type: str  # 'add', 'remove', 'update_tv', 'update_av'
    handle: AtomHandle
    timestamp: float = field(default_factory=time.time)
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None


class AtomSpaceEventBus:
    """Event bus for AtomSpace notifications."""
    
    def __init__(self, buffer_size: int = 10000):
        self._subscribers: Dict[str, List[Callable[[AtomSpaceEvent], None]]] = defaultdict(list)
        self._event_buffer = CircularBuffer[AtomSpaceEvent](buffer_size)
        self._lock = threading.Lock()
    
    def subscribe(self, event_type: str, callback: Callable[[AtomSpaceEvent], None]):
        """Subscribe to events of a specific type."""
        with self._lock:
            self._subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: str, callback: Callable[[AtomSpaceEvent], None]):
        """Unsubscribe from events."""
        with self._lock:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)
    
    def emit(self, event: AtomSpaceEvent):
        """Emit an event to all subscribers."""
        self._event_buffer.push(event)
        with self._lock:
            callbacks = self._subscribers.get(event.event_type, []).copy()
            callbacks.extend(self._subscribers.get('*', []))  # Wildcard subscribers
        
        for callback in callbacks:
            try:
                callback(event)
            except Exception as e:
                # Log error but don't break event propagation
                pass
    
    def get_recent_events(self, count: int = 100) -> List[AtomSpaceEvent]:
        """Get recent events from buffer."""
        events = list(self._event_buffer)
        return events[-count:]


# =============================================================================
# MAIN ATOMSPACE CLASS
# =============================================================================

class AtomSpace:
    """
    The AtomSpace: Central knowledge hypergraph for the cognitive kernel.
    
    This is the core data structure where all knowledge is stored and
    manipulated. It provides:
    - Efficient storage and retrieval of atoms
    - Multiple indexes for fast queries
    - Thread-safe operations
    - Event notification system
    - Attention-based memory management
    
    In the Inferno AGI OS, the AtomSpace is a kernel-level service,
    accessible through the cognitive file system.
    """
    
    def __init__(
        self,
        name: str = "default",
        node_id: str = "local",
        cache_size: int = 10000
    ):
        self.name = name
        self.node_id = node_id
        
        # Primary storage
        self._atoms: Dict[AtomHandle, Atom] = {}
        self._lock = threading.RLock()
        
        # Indexes
        self._type_index = TypeIndex()
        self._name_index = NameIndex()
        self._outgoing_index = OutgoingIndex()
        self._attention_index = AttentionIndex()
        self._content_hash_index = ContentHashIndex()
        
        # Cache for frequently accessed atoms
        self._cache = LRUCache[Atom](cache_size)
        
        # Event system
        self._event_bus = AtomSpaceEventBus()
        
        # Statistics
        self._stats = {
            'atoms_added': 0,
            'atoms_removed': 0,
            'queries': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'created_at': time.time()
        }
    
    # =========================================================================
    # ATOM MANAGEMENT
    # =========================================================================
    
    def add_node(
        self,
        atom_type: AtomType,
        name: str,
        tv: Optional[TruthValue] = None,
        av: Optional[AttentionValue] = None
    ) -> AtomHandle:
        """
        Add a node to the AtomSpace.
        If a node with the same type and name exists, merge truth values.
        """
        with self._lock:
            # Check if node already exists
            existing_handle = self._name_index.get(atom_type, name)
            if existing_handle:
                existing_atom = self._atoms[existing_handle]
                if tv:
                    existing_atom.update_truth_value(tv)
                if av:
                    existing_atom.update_attention(av)
                    self._attention_index.update(existing_handle, av)
                return existing_handle
            
            # Create new node
            node = Node(
                atom_type=atom_type,
                name=name,
                truth_value=tv or TruthValue(),
                attention_value=av or AttentionValue(),
                handle=AtomHandle(node_id=self.node_id)
            )
            
            # Store and index
            self._atoms[node.handle] = node
            self._type_index.add(atom_type, node.handle)
            self._name_index.add(atom_type, name, node.handle)
            self._content_hash_index.add(node.get_hash(), node.handle)
            self._attention_index.update(node.handle, node.attention_value)
            self._cache.put(node.handle.uuid, node)
            
            # Emit event
            self._event_bus.emit(AtomSpaceEvent(
                event_type='add',
                handle=node.handle,
                new_value=node
            ))
            
            self._stats['atoms_added'] += 1
            return node.handle
    
    def add_link(
        self,
        atom_type: AtomType,
        outgoing: List[AtomHandle],
        tv: Optional[TruthValue] = None,
        av: Optional[AttentionValue] = None
    ) -> Optional[AtomHandle]:
        """
        Add a link to the AtomSpace.
        All outgoing atoms must exist. If identical link exists, merge TVs.
        """
        with self._lock:
            # Verify all outgoing atoms exist
            for handle in outgoing:
                if handle not in self._atoms:
                    return None
            
            # Create link to compute hash
            link = Link(
                atom_type=atom_type,
                outgoing=outgoing,
                truth_value=tv or TruthValue(),
                attention_value=av or AttentionValue(),
                handle=AtomHandle(node_id=self.node_id)
            )
            
            # Check for existing identical link
            content_hash = link.get_hash()
            existing_handle = self._content_hash_index.get(content_hash)
            if existing_handle:
                existing_atom = self._atoms[existing_handle]
                if tv:
                    existing_atom.update_truth_value(tv)
                if av:
                    existing_atom.update_attention(av)
                    self._attention_index.update(existing_handle, av)
                return existing_handle
            
            # Store and index
            self._atoms[link.handle] = link
            self._type_index.add(atom_type, link.handle)
            self._outgoing_index.add(link.handle, outgoing)
            self._content_hash_index.add(content_hash, link.handle)
            self._attention_index.update(link.handle, link.attention_value)
            self._cache.put(link.handle.uuid, link)
            
            # Update incoming references
            for target_handle in outgoing:
                target_atom = self._atoms[target_handle]
                target_atom.add_incoming(link.handle)
            
            # Emit event
            self._event_bus.emit(AtomSpaceEvent(
                event_type='add',
                handle=link.handle,
                new_value=link
            ))
            
            self._stats['atoms_added'] += 1
            return link.handle
    
    def remove_atom(self, handle: AtomHandle, recursive: bool = False) -> bool:
        """
        Remove an atom from the AtomSpace.
        If recursive=True, also remove all links that reference this atom.
        """
        with self._lock:
            if handle not in self._atoms:
                return False
            
            atom = self._atoms[handle]
            
            # Check for incoming links
            if atom.incoming and not recursive:
                return False  # Cannot remove atom with incoming links
            
            # Recursively remove incoming links first
            if recursive:
                for incoming_handle in list(atom.incoming):
                    self.remove_atom(incoming_handle, recursive=True)
            
            # Remove from indexes
            self._type_index.remove(atom.atom_type, handle)
            self._content_hash_index.remove(atom.get_hash())
            self._attention_index.remove(handle)
            self._cache.remove(handle.uuid)
            
            if isinstance(atom, Node):
                self._name_index.remove(atom.atom_type, atom.name, handle)
            elif isinstance(atom, Link):
                self._outgoing_index.remove(handle, atom.outgoing)
                # Update incoming references of target atoms
                for target_handle in atom.outgoing:
                    if target_handle in self._atoms:
                        self._atoms[target_handle].remove_incoming(handle)
            
            # Remove from storage
            del self._atoms[handle]
            
            # Emit event
            self._event_bus.emit(AtomSpaceEvent(
                event_type='remove',
                handle=handle,
                old_value=atom
            ))
            
            self._stats['atoms_removed'] += 1
            return True
    
    def get_atom(self, handle: AtomHandle) -> Optional[Atom]:
        """Get an atom by its handle."""
        # Check cache first
        cached = self._cache.get(handle.uuid)
        if cached:
            self._stats['cache_hits'] += 1
            return cached
        
        self._stats['cache_misses'] += 1
        
        with self._lock:
            atom = self._atoms.get(handle)
            if atom:
                self._cache.put(handle.uuid, atom)
            return atom
    
    def get_node(self, atom_type: AtomType, name: str) -> Optional[Node]:
        """Get a node by type and name."""
        self._stats['queries'] += 1
        handle = self._name_index.get(atom_type, name)
        if handle:
            atom = self.get_atom(handle)
            if isinstance(atom, Node):
                return atom
        return None
    
    # =========================================================================
    # TRUTH VALUE AND ATTENTION OPERATIONS
    # =========================================================================
    
    def set_truth_value(self, handle: AtomHandle, tv: TruthValue) -> bool:
        """Set the truth value of an atom."""
        with self._lock:
            atom = self._atoms.get(handle)
            if not atom:
                return False
            
            old_tv = atom.truth_value
            atom.truth_value = tv
            atom.modified_at = time.time()
            
            self._event_bus.emit(AtomSpaceEvent(
                event_type='update_tv',
                handle=handle,
                old_value=old_tv,
                new_value=tv
            ))
            return True
    
    def merge_truth_value(self, handle: AtomHandle, tv: TruthValue) -> bool:
        """Merge a truth value with existing using revision."""
        with self._lock:
            atom = self._atoms.get(handle)
            if not atom:
                return False
            
            old_tv = atom.truth_value
            atom.update_truth_value(tv)
            
            self._event_bus.emit(AtomSpaceEvent(
                event_type='update_tv',
                handle=handle,
                old_value=old_tv,
                new_value=atom.truth_value
            ))
            return True
    
    def set_attention_value(self, handle: AtomHandle, av: AttentionValue) -> bool:
        """Set the attention value of an atom."""
        with self._lock:
            atom = self._atoms.get(handle)
            if not atom:
                return False
            
            old_av = atom.attention_value
            atom.attention_value = av
            atom.modified_at = time.time()
            self._attention_index.update(handle, av)
            
            self._event_bus.emit(AtomSpaceEvent(
                event_type='update_av',
                handle=handle,
                old_value=old_av,
                new_value=av
            ))
            return True
    
    def stimulate(self, handle: AtomHandle, amount: float) -> bool:
        """Stimulate an atom's attention."""
        with self._lock:
            atom = self._atoms.get(handle)
            if not atom:
                return False
            
            new_av = atom.attention_value.stimulate(amount)
            return self.set_attention_value(handle, new_av)
    
    # =========================================================================
    # QUERY OPERATIONS
    # =========================================================================
    
    def get_atoms_by_type(
        self,
        atom_type: AtomType,
        subtype: bool = False
    ) -> List[Atom]:
        """Get all atoms of a specific type."""
        self._stats['queries'] += 1
        handles = self._type_index.get(atom_type)
        return [self._atoms[h] for h in handles if h in self._atoms]
    
    def get_atoms_by_name(self, name: str) -> List[Atom]:
        """Get all atoms with a specific name."""
        self._stats['queries'] += 1
        handles = self._name_index.get_by_name(name)
        return [self._atoms[h] for h in handles if h in self._atoms]
    
    def get_incoming(self, handle: AtomHandle) -> List[Link]:
        """Get all links pointing to an atom."""
        self._stats['queries'] += 1
        atom = self._atoms.get(handle)
        if not atom:
            return []
        
        return [
            self._atoms[h] for h in atom.incoming 
            if h in self._atoms and isinstance(self._atoms[h], Link)
        ]
    
    def get_outgoing(self, handle: AtomHandle) -> List[Atom]:
        """Get all atoms that a link points to."""
        self._stats['queries'] += 1
        atom = self._atoms.get(handle)
        if not isinstance(atom, Link):
            return []
        
        return [self._atoms[h] for h in atom.outgoing if h in self._atoms]
    
    def get_neighbors(
        self,
        handle: AtomHandle,
        link_type: Optional[AtomType] = None
    ) -> List[Atom]:
        """Get neighboring atoms connected through links."""
        self._stats['queries'] += 1
        neighbors = []
        
        for link in self.get_incoming(handle):
            if link_type and link.atom_type != link_type:
                continue
            for target_handle in link.outgoing:
                if target_handle != handle and target_handle in self._atoms:
                    neighbors.append(self._atoms[target_handle])
        
        return neighbors
    
    def get_attentional_focus(self, limit: int = 100) -> List[Atom]:
        """Get atoms currently in attentional focus."""
        handles = self._attention_index.get_attentional_focus(limit)
        return [self._atoms[h] for h in handles if h in self._atoms]
    
    def get_top_attention(self, n: int = 10) -> List[Tuple[float, Atom]]:
        """Get top N atoms by attention."""
        top = self._attention_index.get_top_n(n)
        return [
            (sti, self._atoms[h]) 
            for sti, h in top 
            if h in self._atoms
        ]
    
    # =========================================================================
    # PATTERN MATCHING
    # =========================================================================
    
    def match_pattern(
        self,
        pattern_type: AtomType,
        pattern_outgoing: List[Optional[AtomHandle]] = None
    ) -> List[Link]:
        """
        Simple pattern matching for links.
        None in pattern_outgoing matches any atom.
        """
        self._stats['queries'] += 1
        results = []
        
        for link in self.get_atoms_by_type(pattern_type):
            if not isinstance(link, Link):
                continue
            
            if pattern_outgoing is None:
                results.append(link)
                continue
            
            if len(link.outgoing) != len(pattern_outgoing):
                continue
            
            match = True
            for i, pattern_handle in enumerate(pattern_outgoing):
                if pattern_handle is not None and link.outgoing[i] != pattern_handle:
                    match = False
                    break
            
            if match:
                results.append(link)
        
        return results
    
    def find_inheritance_chain(
        self,
        start: AtomHandle,
        end: AtomHandle,
        max_depth: int = 10
    ) -> Optional[List[AtomHandle]]:
        """Find inheritance chain between two concepts."""
        self._stats['queries'] += 1
        
        visited = set()
        queue = [(start, [start])]
        
        while queue:
            current, path = queue.pop(0)
            
            if current == end:
                return path
            
            if current in visited or len(path) > max_depth:
                continue
            
            visited.add(current)
            
            # Find inheritance links where current is the first argument
            for link in self.get_incoming(current):
                if link.atom_type == AtomType.INHERITANCE_LINK:
                    if link.outgoing[0] == current and len(link.outgoing) > 1:
                        next_handle = link.outgoing[1]
                        if next_handle not in visited:
                            queue.append((next_handle, path + [next_handle]))
        
        return None
    
    # =========================================================================
    # ATTENTION DYNAMICS
    # =========================================================================
    
    def decay_attention(self, rate: float = 0.99) -> int:
        """Apply attention decay to all atoms."""
        count = 0
        with self._lock:
            for handle, atom in self._atoms.items():
                if not atom.attention_value.vlti:
                    new_av = atom.attention_value.decay(rate)
                    atom.attention_value = new_av
                    self._attention_index.update(handle, new_av)
                    count += 1
        return count
    
    def spread_attention(
        self,
        source: AtomHandle,
        spread_factor: float = 0.1,
        max_spread: int = 10
    ) -> int:
        """Spread attention from source to neighbors."""
        atom = self.get_atom(source)
        if not atom:
            return 0
        
        spread_amount = atom.attention_value.sti * spread_factor
        if spread_amount < 0.001:
            return 0
        
        neighbors = self.get_neighbors(source)[:max_spread]
        for neighbor in neighbors:
            self.stimulate(neighbor.handle, spread_amount / len(neighbors))
        
        return len(neighbors)
    
    # =========================================================================
    # PERSISTENCE
    # =========================================================================
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize AtomSpace to dictionary."""
        with self._lock:
            return {
                'name': self.name,
                'node_id': self.node_id,
                'atoms': [atom.to_dict() for atom in self._atoms.values()],
                'stats': self._stats.copy()
            }
    
    def save(self, filepath: str):
        """Save AtomSpace to file."""
        data = self.to_dict()
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    @classmethod
    def load(cls, filepath: str) -> 'AtomSpace':
        """Load AtomSpace from file."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        atomspace = cls(name=data['name'], node_id=data['node_id'])
        
        # First pass: create all nodes
        handle_map = {}  # old handle -> new handle
        for atom_data in data['atoms']:
            if atom_data['class'] == 'Node':
                node = Node.from_dict(atom_data)
                atomspace._atoms[node.handle] = node
                atomspace._type_index.add(node.atom_type, node.handle)
                atomspace._name_index.add(node.atom_type, node.name, node.handle)
                atomspace._content_hash_index.add(node.get_hash(), node.handle)
                atomspace._attention_index.update(node.handle, node.attention_value)
                handle_map[atom_data['handle']['uuid']] = node.handle
        
        # Second pass: create all links
        for atom_data in data['atoms']:
            if atom_data['class'] == 'Link':
                link = Link.from_dict(atom_data)
                atomspace._atoms[link.handle] = link
                atomspace._type_index.add(link.atom_type, link.handle)
                atomspace._outgoing_index.add(link.handle, link.outgoing)
                atomspace._content_hash_index.add(link.get_hash(), link.handle)
                atomspace._attention_index.update(link.handle, link.attention_value)
                
                # Update incoming references
                for target_handle in link.outgoing:
                    if target_handle in atomspace._atoms:
                        atomspace._atoms[target_handle].add_incoming(link.handle)
        
        atomspace._stats = data.get('stats', atomspace._stats)
        return atomspace
    
    # =========================================================================
    # STATISTICS AND UTILITIES
    # =========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get AtomSpace statistics."""
        with self._lock:
            type_counts = {}
            for atom_type in self._type_index.get_all_types():
                type_counts[atom_type.name] = self._type_index.count(atom_type)
            
            return {
                **self._stats,
                'total_atoms': len(self._atoms),
                'type_counts': type_counts,
                'focus_size': len(self._attention_index.get_attentional_focus()),
                'vlti_count': len(self._attention_index.get_vlti_atoms())
            }
    
    def clear(self):
        """Clear all atoms from the AtomSpace."""
        with self._lock:
            self._atoms.clear()
            self._type_index = TypeIndex()
            self._name_index = NameIndex()
            self._outgoing_index = OutgoingIndex()
            self._attention_index = AttentionIndex()
            self._content_hash_index = ContentHashIndex()
            self._cache = LRUCache[Atom](self._cache.capacity)
    
    def __len__(self) -> int:
        return len(self._atoms)
    
    def size(self) -> int:
        """Return the number of atoms in the AtomSpace."""
        return len(self._atoms)
    
    def __iter__(self) -> Iterator[Atom]:
        with self._lock:
            return iter(list(self._atoms.values()))
    
    def __contains__(self, handle: AtomHandle) -> bool:
        return handle in self._atoms
    
    # =========================================================================
    # EVENT SUBSCRIPTION
    # =========================================================================
    
    def subscribe(self, event_type: str, callback: Callable[[AtomSpaceEvent], None]):
        """Subscribe to AtomSpace events."""
        self._event_bus.subscribe(event_type, callback)
    
    def unsubscribe(self, event_type: str, callback: Callable[[AtomSpaceEvent], None]):
        """Unsubscribe from AtomSpace events."""
        self._event_bus.unsubscribe(event_type, callback)
    
    def get_recent_events(self, count: int = 100) -> List[AtomSpaceEvent]:
        """Get recent events."""
        return self._event_bus.get_recent_events(count)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_concept(atomspace: AtomSpace, name: str, **kwargs) -> AtomHandle:
    """Create a concept node."""
    return atomspace.add_node(AtomType.CONCEPT_NODE, name, **kwargs)


def create_predicate(atomspace: AtomSpace, name: str, **kwargs) -> AtomHandle:
    """Create a predicate node."""
    return atomspace.add_node(AtomType.PREDICATE_NODE, name, **kwargs)


def create_inheritance(
    atomspace: AtomSpace,
    child: AtomHandle,
    parent: AtomHandle,
    tv: Optional[TruthValue] = None
) -> Optional[AtomHandle]:
    """Create an inheritance link (child IS-A parent)."""
    return atomspace.add_link(
        AtomType.INHERITANCE_LINK,
        [child, parent],
        tv=tv or TruthValue(1.0, 0.9)
    )


def create_similarity(
    atomspace: AtomSpace,
    atom1: AtomHandle,
    atom2: AtomHandle,
    tv: Optional[TruthValue] = None
) -> Optional[AtomHandle]:
    """Create a similarity link."""
    return atomspace.add_link(
        AtomType.SIMILARITY_LINK,
        [atom1, atom2],
        tv=tv or TruthValue(0.5, 0.5)
    )


def create_evaluation(
    atomspace: AtomSpace,
    predicate: AtomHandle,
    arguments: List[AtomHandle],
    tv: Optional[TruthValue] = None
) -> Optional[AtomHandle]:
    """Create an evaluation link."""
    list_link = atomspace.add_link(AtomType.LIST_LINK, arguments)
    if list_link:
        return atomspace.add_link(
            AtomType.EVALUATION_LINK,
            [predicate, list_link],
            tv=tv
        )
    return None


# Export
__all__ = [
    'AtomSpace',
    'AtomSpaceEvent',
    'AtomSpaceEventBus',
    'TypeIndex',
    'NameIndex',
    'OutgoingIndex',
    'AttentionIndex',
    'ContentHashIndex',
    'create_concept',
    'create_predicate',
    'create_inheritance',
    'create_similarity',
    'create_evaluation',
]
