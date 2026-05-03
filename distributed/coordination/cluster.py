"""
OpenCog Inferno AGI - Distributed Coordination System
=====================================================

This module implements distributed coordination for the AGI OS:
- Cluster management and node discovery
- Distributed AtomSpace synchronization
- Consensus protocols for shared knowledge
- Load balancing for cognitive processes
- Fault tolerance and recovery

Following Inferno OS principles, distribution is transparent -
cognitive processes can run on any node and access any AtomSpace.
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
import json
import hashlib
import random
from collections import defaultdict

from kernel.cognitive.types import (
    Atom, Node, Link, AtomHandle, AtomType,
    TruthValue, AttentionValue
)
from atomspace.hypergraph.atomspace import AtomSpace


# =============================================================================
# NODE MANAGEMENT
# =============================================================================

class NodeState(Enum):
    """State of a cluster node."""
    UNKNOWN = auto()
    JOINING = auto()
    ACTIVE = auto()
    LEAVING = auto()
    FAILED = auto()


class NodeRole(Enum):
    """Role of a node in the cluster."""
    COORDINATOR = auto()    # Manages cluster membership
    WORKER = auto()         # Executes cognitive processes
    STORAGE = auto()        # Stores AtomSpace data
    GATEWAY = auto()        # External interface


@dataclass
class ClusterNode:
    """A node in the distributed cluster."""
    node_id: str
    address: str
    port: int
    roles: Set[NodeRole] = field(default_factory=set)
    state: NodeState = NodeState.UNKNOWN
    
    # Capabilities
    cpu_cores: int = 1
    memory_mb: int = 1024
    gpu_available: bool = False
    
    # Health metrics
    last_heartbeat: float = field(default_factory=time.time)
    load_average: float = 0.0
    atom_count: int = 0
    process_count: int = 0
    
    # Partition assignment
    partitions: Set[int] = field(default_factory=set)
    
    def is_healthy(self, timeout: float = 30.0) -> bool:
        """Check if node is healthy."""
        return (
            self.state == NodeState.ACTIVE and
            time.time() - self.last_heartbeat < timeout
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'node_id': self.node_id,
            'address': self.address,
            'port': self.port,
            'roles': [r.name for r in self.roles],
            'state': self.state.name,
            'load_average': self.load_average,
            'atom_count': self.atom_count,
            'process_count': self.process_count
        }


@dataclass
class ClusterConfig:
    """Configuration for the cluster."""
    cluster_name: str = "opencog-cluster"
    heartbeat_interval: float = 5.0
    failure_timeout: float = 30.0
    replication_factor: int = 2
    num_partitions: int = 16
    sync_interval: float = 1.0


# =============================================================================
# CLUSTER MANAGER
# =============================================================================

class ClusterManager:
    """
    Manages the distributed cluster of AGI nodes.
    """
    
    def __init__(
        self,
        local_node: ClusterNode,
        config: ClusterConfig = None
    ):
        self.local_node = local_node
        self.config = config or ClusterConfig()
        
        # Cluster state
        self._nodes: Dict[str, ClusterNode] = {local_node.node_id: local_node}
        self._coordinator_id: Optional[str] = None
        
        # Partition map
        self._partition_map: Dict[int, List[str]] = {}  # partition -> node_ids
        
        # Service state
        self._running = False
        self._heartbeat_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        
        # Callbacks
        self._on_node_joined: List[Callable[[ClusterNode], None]] = []
        self._on_node_left: List[Callable[[ClusterNode], None]] = []
        self._on_coordinator_changed: List[Callable[[str], None]] = []
    
    # =========================================================================
    # CLUSTER OPERATIONS
    # =========================================================================
    
    def start(self) -> bool:
        """Start the cluster manager."""
        if self._running:
            return False
        
        self._running = True
        self.local_node.state = NodeState.ACTIVE
        
        # Start heartbeat
        self._heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True,
            name="cluster-heartbeat"
        )
        self._heartbeat_thread.start()
        
        # Initialize partitions
        self._initialize_partitions()
        
        # Elect coordinator if needed
        if not self._coordinator_id:
            self._elect_coordinator()
        
        return True
    
    def stop(self) -> bool:
        """Stop the cluster manager."""
        if not self._running:
            return False
        
        self._running = False
        self.local_node.state = NodeState.LEAVING
        
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=2.0)
        
        return True
    
    def join_cluster(self, seed_address: str, seed_port: int) -> bool:
        """Join an existing cluster."""
        # In production, this would connect to the seed node
        # and exchange cluster state
        self.local_node.state = NodeState.JOINING
        
        # Simplified: just mark as active
        self.local_node.state = NodeState.ACTIVE
        return True
    
    def add_node(self, node: ClusterNode):
        """Add a node to the cluster."""
        with self._lock:
            self._nodes[node.node_id] = node
            node.state = NodeState.ACTIVE
            
            # Rebalance partitions
            self._rebalance_partitions()
            
            # Notify callbacks
            for callback in self._on_node_joined:
                try:
                    callback(node)
                except:
                    pass
    
    def remove_node(self, node_id: str):
        """Remove a node from the cluster."""
        with self._lock:
            node = self._nodes.pop(node_id, None)
            if node:
                node.state = NodeState.LEAVING
                
                # Rebalance partitions
                self._rebalance_partitions()
                
                # Elect new coordinator if needed
                if node_id == self._coordinator_id:
                    self._elect_coordinator()
                
                # Notify callbacks
                for callback in self._on_node_left:
                    try:
                        callback(node)
                    except:
                        pass
    
    def get_node(self, node_id: str) -> Optional[ClusterNode]:
        """Get a node by ID."""
        return self._nodes.get(node_id)
    
    def get_active_nodes(self) -> List[ClusterNode]:
        """Get all active nodes."""
        return [n for n in self._nodes.values() if n.state == NodeState.ACTIVE]
    
    def get_coordinator(self) -> Optional[ClusterNode]:
        """Get the current coordinator node."""
        if self._coordinator_id:
            return self._nodes.get(self._coordinator_id)
        return None
    
    def is_coordinator(self) -> bool:
        """Check if local node is the coordinator."""
        return self._coordinator_id == self.local_node.node_id
    
    # =========================================================================
    # PARTITIONING
    # =========================================================================
    
    def _initialize_partitions(self):
        """Initialize partition assignments."""
        with self._lock:
            for partition in range(self.config.num_partitions):
                self._partition_map[partition] = [self.local_node.node_id]
                self.local_node.partitions.add(partition)
    
    def _rebalance_partitions(self):
        """Rebalance partitions across nodes."""
        with self._lock:
            active_nodes = self.get_active_nodes()
            if not active_nodes:
                return
            
            # Clear current assignments
            for node in active_nodes:
                node.partitions.clear()
            
            # Distribute partitions evenly
            for partition in range(self.config.num_partitions):
                # Assign to nodes based on hash
                assigned = []
                for i in range(min(self.config.replication_factor, len(active_nodes))):
                    idx = (partition + i) % len(active_nodes)
                    node = active_nodes[idx]
                    assigned.append(node.node_id)
                    node.partitions.add(partition)
                
                self._partition_map[partition] = assigned
    
    def get_partition_for_atom(self, handle: AtomHandle) -> int:
        """Get the partition for an atom."""
        hash_val = int(hashlib.md5(handle.uuid.encode()).hexdigest(), 16)
        return hash_val % self.config.num_partitions
    
    def get_nodes_for_partition(self, partition: int) -> List[ClusterNode]:
        """Get nodes responsible for a partition."""
        node_ids = self._partition_map.get(partition, [])
        return [self._nodes[nid] for nid in node_ids if nid in self._nodes]
    
    def get_nodes_for_atom(self, handle: AtomHandle) -> List[ClusterNode]:
        """Get nodes responsible for an atom."""
        partition = self.get_partition_for_atom(handle)
        return self.get_nodes_for_partition(partition)
    
    # =========================================================================
    # COORDINATOR ELECTION
    # =========================================================================
    
    def _elect_coordinator(self):
        """Elect a coordinator using simple leader election."""
        with self._lock:
            active_nodes = self.get_active_nodes()
            if not active_nodes:
                return
            
            # Simple: node with lowest ID becomes coordinator
            active_nodes.sort(key=lambda n: n.node_id)
            new_coordinator = active_nodes[0].node_id
            
            if new_coordinator != self._coordinator_id:
                self._coordinator_id = new_coordinator
                
                # Notify callbacks
                for callback in self._on_coordinator_changed:
                    try:
                        callback(new_coordinator)
                    except:
                        pass
    
    # =========================================================================
    # HEARTBEAT
    # =========================================================================
    
    def _heartbeat_loop(self):
        """Background heartbeat loop."""
        while self._running:
            try:
                self._send_heartbeat()
                self._check_node_health()
            except Exception as e:
                pass  # Log in production
            
            time.sleep(self.config.heartbeat_interval)
    
    def _send_heartbeat(self):
        """Send heartbeat to other nodes."""
        self.local_node.last_heartbeat = time.time()
        # In production, would broadcast to other nodes
    
    def _check_node_health(self):
        """Check health of all nodes."""
        with self._lock:
            failed_nodes = []
            
            for node in self._nodes.values():
                if node.node_id == self.local_node.node_id:
                    continue
                
                if not node.is_healthy(self.config.failure_timeout):
                    node.state = NodeState.FAILED
                    failed_nodes.append(node.node_id)
            
            # Remove failed nodes
            for node_id in failed_nodes:
                self.remove_node(node_id)
    
    # =========================================================================
    # CALLBACKS
    # =========================================================================
    
    def on_node_joined(self, callback: Callable[[ClusterNode], None]):
        """Register callback for node join."""
        self._on_node_joined.append(callback)
    
    def on_node_left(self, callback: Callable[[ClusterNode], None]):
        """Register callback for node leave."""
        self._on_node_left.append(callback)
    
    def on_coordinator_changed(self, callback: Callable[[str], None]):
        """Register callback for coordinator change."""
        self._on_coordinator_changed.append(callback)
    
    # =========================================================================
    # STATUS
    # =========================================================================
    
    def status(self) -> Dict[str, Any]:
        """Get cluster status."""
        return {
            'cluster_name': self.config.cluster_name,
            'local_node_id': self.local_node.node_id,
            'coordinator_id': self._coordinator_id,
            'is_coordinator': self.is_coordinator(),
            'node_count': len(self._nodes),
            'active_count': len(self.get_active_nodes()),
            'partition_count': self.config.num_partitions,
            'nodes': [n.to_dict() for n in self._nodes.values()]
        }


# =============================================================================
# DISTRIBUTED ATOMSPACE
# =============================================================================

@dataclass
class AtomUpdate:
    """An update to an atom for synchronization."""
    handle: AtomHandle
    operation: str  # 'add', 'update', 'remove'
    atom_data: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)
    source_node: str = ""
    version: int = 0


class DistributedAtomSpace:
    """
    Distributed AtomSpace with synchronization.
    
    Provides transparent access to atoms across the cluster.
    """
    
    def __init__(
        self,
        local_atomspace: AtomSpace,
        cluster_manager: ClusterManager
    ):
        self.local = local_atomspace
        self.cluster = cluster_manager
        
        # Pending updates for synchronization
        self._pending_updates: List[AtomUpdate] = []
        self._update_log: List[AtomUpdate] = []
        
        # Version vectors for conflict resolution
        self._version_vectors: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        # Sync state
        self._running = False
        self._sync_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        
        # Statistics
        self.stats = {
            'local_reads': 0,
            'remote_reads': 0,
            'writes': 0,
            'syncs': 0,
            'conflicts': 0
        }
    
    # =========================================================================
    # DISTRIBUTED OPERATIONS
    # =========================================================================
    
    def add_node(
        self,
        atom_type: AtomType,
        name: str,
        tv: TruthValue = None,
        av: AttentionValue = None
    ) -> AtomHandle:
        """Add a node to the distributed AtomSpace."""
        # Add locally
        handle = self.local.add_node(atom_type, name, tv=tv, av=av)
        
        # Queue for synchronization
        self._queue_update(AtomUpdate(
            handle=handle,
            operation='add',
            atom_data={
                'type': atom_type.name,
                'name': name,
                'tv': tv.to_dict() if tv else None,
                'av': av.to_dict() if av else None
            },
            source_node=self.cluster.local_node.node_id
        ))
        
        self.stats['writes'] += 1
        return handle
    
    def add_link(
        self,
        atom_type: AtomType,
        outgoing: List[AtomHandle],
        tv: TruthValue = None,
        av: AttentionValue = None
    ) -> AtomHandle:
        """Add a link to the distributed AtomSpace."""
        # Add locally
        handle = self.local.add_link(atom_type, outgoing, tv=tv, av=av)
        
        # Queue for synchronization
        self._queue_update(AtomUpdate(
            handle=handle,
            operation='add',
            atom_data={
                'type': atom_type.name,
                'outgoing': [h.uuid for h in outgoing],
                'tv': tv.to_dict() if tv else None,
                'av': av.to_dict() if av else None
            },
            source_node=self.cluster.local_node.node_id
        ))
        
        self.stats['writes'] += 1
        return handle
    
    def get_atom(self, handle: AtomHandle) -> Optional[Atom]:
        """Get an atom, potentially from remote node."""
        # Try local first
        atom = self.local.get_atom(handle)
        if atom:
            self.stats['local_reads'] += 1
            return atom
        
        # Try remote nodes
        nodes = self.cluster.get_nodes_for_atom(handle)
        for node in nodes:
            if node.node_id == self.cluster.local_node.node_id:
                continue
            
            # In production, would fetch from remote node
            self.stats['remote_reads'] += 1
        
        return None
    
    def remove_atom(self, handle: AtomHandle) -> bool:
        """Remove an atom from the distributed AtomSpace."""
        result = self.local.remove_atom(handle)
        
        if result:
            self._queue_update(AtomUpdate(
                handle=handle,
                operation='remove',
                atom_data={},
                source_node=self.cluster.local_node.node_id
            ))
        
        return result
    
    # =========================================================================
    # SYNCHRONIZATION
    # =========================================================================
    
    def start_sync(self) -> bool:
        """Start synchronization."""
        if self._running:
            return False
        
        self._running = True
        self._sync_thread = threading.Thread(
            target=self._sync_loop,
            daemon=True,
            name="atomspace-sync"
        )
        self._sync_thread.start()
        return True
    
    def stop_sync(self) -> bool:
        """Stop synchronization."""
        if not self._running:
            return False
        
        self._running = False
        if self._sync_thread:
            self._sync_thread.join(timeout=2.0)
        return True
    
    def _sync_loop(self):
        """Background synchronization loop."""
        while self._running:
            try:
                self._process_pending_updates()
                self._pull_remote_updates()
            except Exception as e:
                pass  # Log in production
            
            time.sleep(self.cluster.config.sync_interval)
    
    def _queue_update(self, update: AtomUpdate):
        """Queue an update for synchronization."""
        with self._lock:
            # Update version vector
            node_id = self.cluster.local_node.node_id
            self._version_vectors[update.handle.uuid][node_id] += 1
            update.version = self._version_vectors[update.handle.uuid][node_id]
            
            self._pending_updates.append(update)
            self._update_log.append(update)
    
    def _process_pending_updates(self):
        """Process and send pending updates."""
        with self._lock:
            if not self._pending_updates:
                return
            
            updates = self._pending_updates.copy()
            self._pending_updates.clear()
        
        # In production, would send to replica nodes
        for update in updates:
            nodes = self.cluster.get_nodes_for_atom(update.handle)
            for node in nodes:
                if node.node_id != self.cluster.local_node.node_id:
                    # Send update to node
                    pass
        
        self.stats['syncs'] += 1
    
    def _pull_remote_updates(self):
        """Pull updates from remote nodes."""
        # In production, would pull from other nodes
        pass
    
    def apply_remote_update(self, update: AtomUpdate) -> bool:
        """Apply an update received from a remote node."""
        with self._lock:
            # Check for conflicts
            current_version = self._version_vectors[update.handle.uuid].get(update.source_node, 0)
            
            if update.version <= current_version:
                # Already applied or outdated
                return False
            
            # Apply update
            if update.operation == 'add':
                self._apply_add(update)
            elif update.operation == 'update':
                self._apply_update(update)
            elif update.operation == 'remove':
                self.local.remove_atom(update.handle)
            
            # Update version vector
            self._version_vectors[update.handle.uuid][update.source_node] = update.version
            
            return True
    
    def _apply_add(self, update: AtomUpdate):
        """Apply an add operation."""
        data = update.atom_data
        atom_type = AtomType[data['type']]
        
        tv = TruthValue(**data['tv']) if data.get('tv') else None
        av = AttentionValue(**data['av']) if data.get('av') else None
        
        if 'name' in data:
            self.local.add_node(atom_type, data['name'], tv=tv, av=av)
        elif 'outgoing' in data:
            outgoing = [AtomHandle(uuid=h) for h in data['outgoing']]
            self.local.add_link(atom_type, outgoing, tv=tv, av=av)
    
    def _apply_update(self, update: AtomUpdate):
        """Apply an update operation."""
        data = update.atom_data
        
        if 'tv' in data and data['tv']:
            tv = TruthValue(**data['tv'])
            self.local.set_truth_value(update.handle, tv)
        
        if 'av' in data and data['av']:
            av = AttentionValue(**data['av'])
            self.local.set_attention_value(update.handle, av)
    
    # =========================================================================
    # STATUS
    # =========================================================================
    
    def status(self) -> Dict[str, Any]:
        """Get distributed AtomSpace status."""
        return {
            'running': self._running,
            'stats': self.stats.copy(),
            'pending_updates': len(self._pending_updates),
            'update_log_size': len(self._update_log),
            'local_atom_count': self.local.size()
        }


# =============================================================================
# CONSENSUS PROTOCOL
# =============================================================================

class ConsensusState(Enum):
    """State of a consensus round."""
    IDLE = auto()
    PREPARE = auto()
    PROMISE = auto()
    ACCEPT = auto()
    COMMITTED = auto()
    ABORTED = auto()


@dataclass
class ConsensusProposal:
    """A proposal for consensus."""
    proposal_id: str
    proposer: str
    value: Any
    round_number: int = 0
    state: ConsensusState = ConsensusState.IDLE
    votes: Dict[str, bool] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class PaxosConsensus:
    """
    Simplified Paxos consensus for distributed decisions.
    
    Used for cluster-wide decisions like:
    - Schema changes
    - Global goal updates
    - Configuration changes
    """
    
    def __init__(self, cluster_manager: ClusterManager):
        self.cluster = cluster_manager
        
        # Consensus state
        self._proposals: Dict[str, ConsensusProposal] = {}
        self._highest_round: int = 0
        self._accepted_value: Any = None
        
        self._lock = threading.RLock()
    
    def propose(self, value: Any) -> Optional[str]:
        """Propose a value for consensus."""
        with self._lock:
            # Create proposal
            proposal_id = f"prop_{int(time.time() * 1000)}_{random.randint(0, 999)}"
            self._highest_round += 1
            
            proposal = ConsensusProposal(
                proposal_id=proposal_id,
                proposer=self.cluster.local_node.node_id,
                value=value,
                round_number=self._highest_round,
                state=ConsensusState.PREPARE
            )
            
            self._proposals[proposal_id] = proposal
            
            # Phase 1: Prepare
            if self._prepare_phase(proposal):
                # Phase 2: Accept
                if self._accept_phase(proposal):
                    proposal.state = ConsensusState.COMMITTED
                    return proposal_id
            
            proposal.state = ConsensusState.ABORTED
            return None
    
    def _prepare_phase(self, proposal: ConsensusProposal) -> bool:
        """Execute prepare phase."""
        active_nodes = self.cluster.get_active_nodes()
        quorum = len(active_nodes) // 2 + 1
        
        # Collect promises
        promises = 1  # Self
        proposal.votes[self.cluster.local_node.node_id] = True
        
        # In production, would send prepare messages to other nodes
        # and wait for promises
        
        # Simplified: assume all nodes promise
        for node in active_nodes:
            if node.node_id != self.cluster.local_node.node_id:
                promises += 1
                proposal.votes[node.node_id] = True
        
        proposal.state = ConsensusState.PROMISE
        return promises >= quorum
    
    def _accept_phase(self, proposal: ConsensusProposal) -> bool:
        """Execute accept phase."""
        active_nodes = self.cluster.get_active_nodes()
        quorum = len(active_nodes) // 2 + 1
        
        # Collect accepts
        accepts = 1  # Self
        self._accepted_value = proposal.value
        
        # In production, would send accept messages to other nodes
        
        # Simplified: assume all nodes accept
        for node in active_nodes:
            if node.node_id != self.cluster.local_node.node_id:
                accepts += 1
        
        proposal.state = ConsensusState.ACCEPT
        return accepts >= quorum
    
    def handle_prepare(self, round_number: int, proposer: str) -> Tuple[bool, int, Any]:
        """Handle a prepare message."""
        with self._lock:
            if round_number > self._highest_round:
                self._highest_round = round_number
                return True, self._highest_round, self._accepted_value
            return False, self._highest_round, None
    
    def handle_accept(self, round_number: int, value: Any) -> bool:
        """Handle an accept message."""
        with self._lock:
            if round_number >= self._highest_round:
                self._highest_round = round_number
                self._accepted_value = value
                return True
            return False
    
    def get_proposal(self, proposal_id: str) -> Optional[ConsensusProposal]:
        """Get a proposal by ID."""
        return self._proposals.get(proposal_id)


# =============================================================================
# LOAD BALANCER
# =============================================================================

class LoadBalancer:
    """
    Balances cognitive process load across cluster nodes.
    """
    
    def __init__(self, cluster_manager: ClusterManager):
        self.cluster = cluster_manager
        
        # Load tracking
        self._node_loads: Dict[str, float] = {}
        
        self._lock = threading.Lock()
    
    def select_node_for_process(
        self,
        process_type: str = None,
        required_atoms: List[AtomHandle] = None
    ) -> Optional[ClusterNode]:
        """Select the best node for a cognitive process."""
        active_nodes = self.cluster.get_active_nodes()
        if not active_nodes:
            return None
        
        # Score each node
        scores = []
        for node in active_nodes:
            score = self._calculate_node_score(node, process_type, required_atoms)
            scores.append((score, node))
        
        # Select highest scoring node
        scores.sort(key=lambda x: -x[0])
        return scores[0][1] if scores else None
    
    def _calculate_node_score(
        self,
        node: ClusterNode,
        process_type: str,
        required_atoms: List[AtomHandle]
    ) -> float:
        """Calculate a score for a node."""
        score = 100.0
        
        # Penalize high load
        score -= node.load_average * 20
        
        # Penalize many processes
        score -= node.process_count * 2
        
        # Bonus for data locality
        if required_atoms:
            local_atoms = 0
            for handle in required_atoms:
                partition = self.cluster.get_partition_for_atom(handle)
                if partition in node.partitions:
                    local_atoms += 1
            
            locality_ratio = local_atoms / len(required_atoms)
            score += locality_ratio * 30
        
        # Bonus for GPU if needed
        if process_type in ['learning', 'pattern'] and node.gpu_available:
            score += 20
        
        return max(0, score)
    
    def update_node_load(self, node_id: str, load: float):
        """Update the load for a node."""
        with self._lock:
            self._node_loads[node_id] = load
            
            node = self.cluster.get_node(node_id)
            if node:
                node.load_average = load
    
    def get_load_distribution(self) -> Dict[str, float]:
        """Get load distribution across nodes."""
        return {
            node.node_id: node.load_average
            for node in self.cluster.get_active_nodes()
        }


# =============================================================================
# DISTRIBUTED COORDINATION SERVICE
# =============================================================================

class DistributedCoordinationService:
    """
    Main distributed coordination service.
    
    Integrates cluster management, distributed AtomSpace,
    consensus, and load balancing.
    """
    
    def __init__(
        self,
        atomspace: AtomSpace,
        node_id: str = None,
        address: str = "localhost",
        port: int = 9000
    ):
        # Create local node
        self.local_node = ClusterNode(
            node_id=node_id or f"node_{random.randint(0, 9999):04d}",
            address=address,
            port=port,
            roles={NodeRole.WORKER, NodeRole.STORAGE}
        )
        
        # Components
        self.cluster = ClusterManager(self.local_node)
        self.distributed_atomspace = DistributedAtomSpace(atomspace, self.cluster)
        self.consensus = PaxosConsensus(self.cluster)
        self.load_balancer = LoadBalancer(self.cluster)
        
        self._running = False
    
    @property
    def service_name(self) -> str:
        return "distributed_coordination_service"
    
    def start(self) -> bool:
        """Start the coordination service."""
        if self._running:
            return False
        
        self._running = True
        self.cluster.start()
        self.distributed_atomspace.start_sync()
        
        return True
    
    def stop(self) -> bool:
        """Stop the coordination service."""
        if not self._running:
            return False
        
        self._running = False
        self.distributed_atomspace.stop_sync()
        self.cluster.stop()
        
        return True
    
    def status(self) -> Dict[str, Any]:
        """Get service status."""
        return {
            'running': self._running,
            'cluster': self.cluster.status(),
            'atomspace': self.distributed_atomspace.status(),
            'load_distribution': self.load_balancer.get_load_distribution()
        }


# Export
__all__ = [
    'NodeState',
    'NodeRole',
    'ClusterNode',
    'ClusterConfig',
    'ClusterManager',
    'AtomUpdate',
    'DistributedAtomSpace',
    'ConsensusState',
    'ConsensusProposal',
    'PaxosConsensus',
    'LoadBalancer',
    'DistributedCoordinationService',
]
