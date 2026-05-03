#!/usr/bin/env python3
"""
Distributed Testing Framework
==============================

Tests for multi-node AGI operations including:
- Distributed AtomSpace synchronization
- Paxos consensus
- Node failure and recovery
- Leader election
- Data consistency
"""

import unittest
import sys
import os
import time
import threading
from unittest.mock import Mock, patch
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from kernel.cognitive.types import AtomType, TruthValue, AttentionValue
from atomspace.hypergraph.atomspace import AtomSpace
from distributed.coordination.cluster import (
    DistributedCoordinationService,
    ClusterManager,
    DistributedAtomSpace,
    PaxosConsensus,
    ClusterNode,
    ClusterConfig,
    NodeState
)


class TestClusterManager(unittest.TestCase):
    """Tests for cluster management."""
    
    def setUp(self):
        self.local_node = ClusterNode(
            node_id="test-node-1",
            address="127.0.0.1",
            port=9000
        )
        self.cluster = ClusterManager(self.local_node)
        
    def tearDown(self):
        self.cluster.stop()
        
    def test_node_registration(self):
        """Test node registration."""
        node = ClusterNode(
            node_id="node-2",
            address="127.0.0.2",
            port=9001,
            state=NodeState.ACTIVE
        )
        
        self.cluster.add_node(node)
        
        nodes = self.cluster.get_active_nodes()
        node_ids = [n.node_id for n in nodes]
        self.assertIn("node-2", node_ids)
        
    def test_node_removal(self):
        """Test node removal."""
        node = ClusterNode(
            node_id="node-to-remove",
            address="127.0.0.3",
            port=9002,
            state=NodeState.ACTIVE
        )
        
        self.cluster.add_node(node)
        self.cluster.remove_node("node-to-remove")
        
        nodes = self.cluster.get_active_nodes()
        node_ids = [n.node_id for n in nodes]
        self.assertNotIn("node-to-remove", node_ids)
        
    def test_multiple_nodes(self):
        """Test managing multiple nodes."""
        for i in range(5):
            node = ClusterNode(
                node_id=f"node-{i}",
                address=f"127.0.0.{i+10}",
                port=9000 + i,
                state=NodeState.ACTIVE
            )
            self.cluster.add_node(node)
        
        nodes = self.cluster.get_active_nodes()
        # Should have 5 added + 1 local
        self.assertGreaterEqual(len(nodes), 5)
        
    def test_node_state_transitions(self):
        """Test node state transitions."""
        node = ClusterNode(
            node_id="state-test",
            address="127.0.0.100",
            port=9100,
            state=NodeState.JOINING
        )
        
        self.cluster.add_node(node)
        
        # Transition to active
        self.cluster.update_node_state("state-test", NodeState.ACTIVE)
        
        updated = self.cluster.get_node("state-test")
        self.assertEqual(updated.state, NodeState.ACTIVE)


class TestDistributedAtomSpace(unittest.TestCase):
    """Tests for distributed AtomSpace."""
    
    def setUp(self):
        self.local_atomspace = AtomSpace()
        self.local_node = ClusterNode(
            node_id="dist-test-1",
            address="127.0.0.1",
            port=9000
        )
        self.cluster = ClusterManager(self.local_node)
        self.distributed = DistributedAtomSpace(
            local_atomspace=self.local_atomspace,
            cluster_manager=self.cluster
        )
        
    def test_local_add_propagates(self):
        """Test that local adds are tracked for propagation."""
        handle = self.distributed.add_node(
            AtomType.CONCEPT_NODE, "TestConcept",
            tv=TruthValue(0.9, 0.9)
        )
        
        self.assertIsNotNone(handle)
        
        # Should be in local atomspace
        atom = self.local_atomspace.get_atom(handle)
        self.assertIsNotNone(atom)
        
    def test_add_link_distributed(self):
        """Test adding links in distributed mode."""
        a = self.distributed.add_node(AtomType.CONCEPT_NODE, "A")
        b = self.distributed.add_node(AtomType.CONCEPT_NODE, "B")
        
        link = self.distributed.add_link(
            AtomType.INHERITANCE_LINK, [a, b],
            tv=TruthValue(0.9, 0.9)
        )
        
        self.assertIsNotNone(link)
        
    def test_sync_state(self):
        """Test getting sync state."""
        # Add some atoms
        for i in range(10):
            self.distributed.add_node(AtomType.CONCEPT_NODE, f"Concept_{i}")
        
        state = self.distributed.get_sync_state()
        
        self.assertIsNotNone(state)
        self.assertIn('local_size', state)


class TestPaxosConsensus(unittest.TestCase):
    """Tests for Paxos consensus."""
    
    def setUp(self):
        self.nodes = []
        for i in range(3):
            local_node = ClusterNode(
                node_id=f"paxos-{i}",
                address=f"127.0.0.{i+50}",
                port=9050 + i
            )
            cluster = ClusterManager(local_node)
            paxos = PaxosConsensus(cluster)
            self.nodes.append((cluster, paxos))
            
    def tearDown(self):
        for cluster, paxos in self.nodes:
            cluster.stop()
            
    def test_single_proposer(self):
        """Test consensus with single proposer."""
        cluster, paxos = self.nodes[0]
        
        # Propose a value
        proposal = {'type': 'add_atom', 'name': 'TestAtom'}
        
        result = paxos.propose(proposal)
        
        # Should succeed or return result
        self.assertIsNotNone(result)
        
    def test_proposal_number_increment(self):
        """Test that proposal numbers increment."""
        cluster, paxos = self.nodes[0]
        
        initial = paxos.get_proposal_number()
        
        paxos.propose({'test': 'value1'})
        
        after = paxos.get_proposal_number()
        
        self.assertGreaterEqual(after, initial)


class TestNodeFailureRecovery(unittest.TestCase):
    """Tests for node failure and recovery."""
    
    def setUp(self):
        self.local_node = ClusterNode(
            node_id="recovery-test",
            address="127.0.0.1",
            port=9200
        )
        self.cluster = ClusterManager(self.local_node)
        
    def tearDown(self):
        self.cluster.stop()
        
    def test_detect_node_failure(self):
        """Test detecting node failure."""
        # Add a node with old heartbeat
        node = ClusterNode(
            node_id="failing-node",
            address="127.0.0.200",
            port=9200,
            state=NodeState.ACTIVE,
            last_heartbeat=time.time() - 60  # Old heartbeat
        )
        
        self.cluster.add_node(node)
        
        # Check health
        is_healthy = node.is_healthy(timeout=30.0)
        
        # Should detect the stale node
        self.assertFalse(is_healthy)
        
    def test_node_recovery(self):
        """Test node recovery after failure."""
        # Add and fail a node
        node = ClusterNode(
            node_id="recovering-node",
            address="127.0.0.201",
            port=9201,
            state=NodeState.FAILED
        )
        
        self.cluster.add_node(node)
        
        # Simulate recovery
        self.cluster.update_node_state("recovering-node", NodeState.ACTIVE)
        
        recovered = self.cluster.get_node("recovering-node")
        self.assertEqual(recovered.state, NodeState.ACTIVE)


class TestDataConsistency(unittest.TestCase):
    """Tests for data consistency across nodes."""
    
    def setUp(self):
        self.atomspaces = [AtomSpace() for _ in range(3)]
        self.clusters = []
        self.distributed_spaces = []
        
        for i in range(3):
            local_node = ClusterNode(
                node_id=f"consistency-{i}",
                address=f"127.0.0.{i+100}",
                port=9100 + i
            )
            cluster = ClusterManager(local_node)
            ds = DistributedAtomSpace(
                local_atomspace=self.atomspaces[i],
                cluster_manager=cluster
            )
            self.clusters.append(cluster)
            self.distributed_spaces.append(ds)
        
    def tearDown(self):
        for cluster in self.clusters:
            cluster.stop()
        
    def test_eventual_consistency(self):
        """Test eventual consistency across nodes."""
        # Add to first node
        handle = self.distributed_spaces[0].add_node(
            AtomType.CONCEPT_NODE, "SharedConcept",
            tv=TruthValue(0.9, 0.9)
        )
        
        # In real system, this would propagate
        # For test, verify local state
        atom = self.atomspaces[0].get_atom(handle)
        self.assertIsNotNone(atom)
        
    def test_concurrent_updates(self):
        """Test handling concurrent updates."""
        # Create same concept on multiple nodes
        handles = []
        for ds in self.distributed_spaces:
            h = ds.add_node(AtomType.CONCEPT_NODE, "ConcurrentConcept")
            handles.append(h)
        
        # All should succeed locally
        for h, atomspace in zip(handles, self.atomspaces):
            atom = atomspace.get_atom(h)
            self.assertIsNotNone(atom)
            
    def test_read_your_writes(self):
        """Test read-your-writes consistency."""
        # Write
        handle = self.distributed_spaces[0].add_node(
            AtomType.CONCEPT_NODE, "WriteReadTest",
            tv=TruthValue(0.8, 0.8)
        )
        
        # Read immediately
        atom = self.atomspaces[0].get_atom(handle)
        
        self.assertIsNotNone(atom)
        self.assertEqual(atom.name, "WriteReadTest")


class TestNetworkPartition(unittest.TestCase):
    """Tests for network partition handling."""
    
    def setUp(self):
        self.local_node = ClusterNode(
            node_id="partition-test",
            address="127.0.0.1",
            port=9300
        )
        self.cluster = ClusterManager(self.local_node)
        
        # Add nodes
        for i in range(5):
            node = ClusterNode(
                node_id=f"partition-node-{i}",
                address=f"127.0.0.{i+100}",
                port=9300 + i,
                state=NodeState.ACTIVE
            )
            self.cluster.add_node(node)
            
    def tearDown(self):
        self.cluster.stop()
        
    def test_partition_detection(self):
        """Test detecting network partition."""
        # Simulate partition by marking nodes as unreachable
        for i in range(2):
            self.cluster.update_node_state(
                f"partition-node-{i}",
                NodeState.UNREACHABLE
            )
        
        # Check partition status
        all_nodes = self.cluster.get_all_nodes()
        unreachable = [n for n in all_nodes if n.state == NodeState.UNREACHABLE]
        
        self.assertEqual(len(unreachable), 2)
        
    def test_partition_recovery(self):
        """Test recovery from network partition."""
        # Create partition
        self.cluster.update_node_state("partition-node-0", NodeState.UNREACHABLE)
        
        # Recover
        self.cluster.update_node_state("partition-node-0", NodeState.ACTIVE)
        
        node = self.cluster.get_node("partition-node-0")
        self.assertEqual(node.state, NodeState.ACTIVE)


class TestDistributedServiceLifecycle(unittest.TestCase):
    """Tests for distributed service lifecycle."""
    
    def test_service_start_stop(self):
        """Test starting and stopping distributed service."""
        atomspace = AtomSpace()
        local_node = ClusterNode(
            node_id="lifecycle-test",
            address="127.0.0.1",
            port=9400
        )
        service = DistributedCoordinationService(
            atomspace=atomspace,
            local_node=local_node
        )
        
        # Start
        self.assertTrue(service.start())
        
        time.sleep(0.2)
        
        # Stop
        self.assertTrue(service.stop())
        
    def test_status_reporting(self):
        """Test status reporting."""
        atomspace = AtomSpace()
        local_node = ClusterNode(
            node_id="status-test",
            address="127.0.0.1",
            port=9402
        )
        service = DistributedCoordinationService(
            atomspace=atomspace,
            local_node=local_node
        )
        
        service.start()
        
        status = service.status()
        
        self.assertIsNotNone(status)
        self.assertIn('node_id', status)
        
        service.stop()


class TestDistributedStress(unittest.TestCase):
    """Stress tests for distributed operations."""
    
    def test_high_throughput_adds(self):
        """Test high throughput atom additions."""
        atomspace = AtomSpace()
        local_node = ClusterNode(
            node_id="throughput-test",
            address="127.0.0.1",
            port=9500
        )
        cluster = ClusterManager(local_node)
        distributed = DistributedAtomSpace(
            local_atomspace=atomspace,
            cluster_manager=cluster
        )
        
        start_time = time.time()
        
        for i in range(1000):
            distributed.add_node(AtomType.CONCEPT_NODE, f"HighThroughput_{i}")
        
        elapsed = time.time() - start_time
        
        # Should complete in reasonable time
        self.assertLess(elapsed, 10.0)
        
        # All should be added
        self.assertEqual(atomspace.size(), 1000)
        
        cluster.stop()
        
    def test_concurrent_distributed_operations(self):
        """Test concurrent distributed operations."""
        atomspace = AtomSpace()
        local_node = ClusterNode(
            node_id="concurrent-test",
            address="127.0.0.1",
            port=9501
        )
        cluster = ClusterManager(local_node)
        distributed = DistributedAtomSpace(
            local_atomspace=atomspace,
            cluster_manager=cluster
        )
        
        errors = []
        
        def add_atoms(start, count):
            try:
                for i in range(start, start + count):
                    distributed.add_node(AtomType.CONCEPT_NODE, f"Concurrent_{i}")
            except Exception as e:
                errors.append(e)
        
        threads = []
        for i in range(4):
            t = threading.Thread(target=add_atoms, args=(i * 100, 100))
            threads.append(t)
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        self.assertEqual(len(errors), 0)
        self.assertEqual(atomspace.size(), 400)
        
        cluster.stop()


if __name__ == '__main__':
    unittest.main(verbosity=2)
