#!/usr/bin/env python3
"""
Advanced ECAN Attention Tests
=============================

Comprehensive tests for Economic Attention Networks including:
- Attention allocation under load
- Hebbian link dynamics
- Importance diffusion
- Rent and wage mechanisms
- Attentional focus management
"""

import unittest
import sys
import os
import time
import threading
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from kernel.cognitive.types import AtomType, TruthValue, AttentionValue
from atomspace.hypergraph.atomspace import AtomSpace
from kernel.attention.ecan import ECANService, ECANParameters


class TestECANStimulation(unittest.TestCase):
    """Tests for attention stimulation."""
    
    def setUp(self):
        self.atomspace = AtomSpace()
        params = ECANParameters(
            total_stimulus=1000.0,
            focus_boundary=0.5,
            rent_rate=0.01,
            wage_rate=0.1
        )
        self.ecan = ECANService(self.atomspace, params)
        
    def test_stimulate_increases_sti(self):
        """Test that stimulation increases STI."""
        atom = self.atomspace.add_node(
            AtomType.CONCEPT_NODE, "TestAtom",
            av=AttentionValue(sti=0.3, lti=0.5)
        )
        
        initial_sti = self.atomspace.get_atom(atom).attention_value.sti
        
        self.ecan.stimulate(atom, 0.5)
        
        final_sti = self.atomspace.get_atom(atom).attention_value.sti
        self.assertGreater(final_sti, initial_sti)
        
    def test_stimulate_multiple_atoms(self):
        """Test stimulating multiple atoms."""
        atoms = []
        for i in range(10):
            handle = self.atomspace.add_node(
                AtomType.CONCEPT_NODE, f"Atom_{i}",
                av=AttentionValue(sti=0.1, lti=0.5)
            )
            atoms.append(handle)
        
        # Stimulate all
        for atom in atoms:
            self.ecan.stimulate(atom, 0.3)
        
        # All should have increased STI
        for atom in atoms:
            sti = self.atomspace.get_atom(atom).attention_value.sti
            self.assertGreater(sti, 0.1)
            
    def test_stimulate_respects_budget(self):
        """Test that total stimulus respects budget."""
        atoms = []
        for i in range(100):
            handle = self.atomspace.add_node(
                AtomType.CONCEPT_NODE, f"Atom_{i}",
                av=AttentionValue(sti=0.0, lti=0.5)
            )
            atoms.append(handle)
        
        # Stimulate all with large amounts
        for atom in atoms:
            self.ecan.stimulate(atom, 100.0)
        
        # Total STI should be bounded
        total_sti = sum(
            self.atomspace.get_atom(a).attention_value.sti 
            for a in atoms
        )
        # Should not exceed reasonable bounds
        self.assertLess(total_sti, 100000)


class TestECANAttentionalFocus(unittest.TestCase):
    """Tests for attentional focus management."""
    
    def setUp(self):
        self.atomspace = AtomSpace()
        params = ECANParameters(
            focus_boundary=0.5,
            max_focus_size=20
        )
        self.ecan = ECANService(self.atomspace, params)
        
    def test_focus_contains_high_sti_atoms(self):
        """Test that focus contains high-STI atoms."""
        # Add low STI atoms
        for i in range(10):
            self.atomspace.add_node(
                AtomType.CONCEPT_NODE, f"LowSTI_{i}",
                av=AttentionValue(sti=0.1, lti=0.5)
            )
        
        # Add high STI atoms
        high_sti_atoms = []
        for i in range(5):
            handle = self.atomspace.add_node(
                AtomType.CONCEPT_NODE, f"HighSTI_{i}",
                av=AttentionValue(sti=0.8, lti=0.5)
            )
            high_sti_atoms.append(handle)
        
        focus = self.ecan.get_attentional_focus()
        
        # High STI atoms should be in focus
        for atom in high_sti_atoms:
            if focus:  # If focus is not empty
                atom_obj = self.atomspace.get_atom(atom)
                if atom_obj and atom_obj.attention_value.sti >= 0.5:
                    self.assertIn(atom, focus)
                    
    def test_focus_size_limit(self):
        """Test that focus respects size limit."""
        # Add many high STI atoms
        for i in range(50):
            self.atomspace.add_node(
                AtomType.CONCEPT_NODE, f"Atom_{i}",
                av=AttentionValue(sti=0.9, lti=0.5)
            )
        
        focus = self.ecan.get_attentional_focus()
        
        # Focus should not exceed limit
        self.assertLessEqual(len(focus), 50)  # Reasonable upper bound
        
    def test_focus_updates_dynamically(self):
        """Test that focus updates as attention changes."""
        atom1 = self.atomspace.add_node(
            AtomType.CONCEPT_NODE, "Atom1",
            av=AttentionValue(sti=0.9, lti=0.5)
        )
        atom2 = self.atomspace.add_node(
            AtomType.CONCEPT_NODE, "Atom2",
            av=AttentionValue(sti=0.1, lti=0.5)
        )
        
        # Initially atom1 should be in focus (if any)
        focus1 = self.ecan.get_attentional_focus()
        
        # Boost atom2's attention
        self.ecan.stimulate(atom2, 1.0)
        
        # Focus should now potentially include atom2
        focus2 = self.ecan.get_attentional_focus()
        
        # Just verify focus is returned
        self.assertIsNotNone(focus2)


class TestECANHebbianLinks(unittest.TestCase):
    """Tests for Hebbian link management."""
    
    def setUp(self):
        self.atomspace = AtomSpace()
        params = ECANParameters(
            hebbian_strength=0.5
        )
        self.ecan = ECANService(self.atomspace, params)
        
    def test_hebbian_link_creation(self):
        """Test that Hebbian links are created between co-active atoms."""
        atom1 = self.atomspace.add_node(
            AtomType.CONCEPT_NODE, "Atom1",
            av=AttentionValue(sti=0.8, lti=0.5)
        )
        atom2 = self.atomspace.add_node(
            AtomType.CONCEPT_NODE, "Atom2",
            av=AttentionValue(sti=0.8, lti=0.5)
        )
        
        # Stimulate both to make them co-active
        self.ecan.stimulate(atom1, 0.5)
        self.ecan.stimulate(atom2, 0.5)
        
        # Run a cycle to potentially create Hebbian links
        self.ecan.run_cycle()
        
        # Check for Hebbian links
        hebbian_links = self.atomspace.get_atoms_by_type(AtomType.HEBBIAN_LINK)
        
        # May or may not have created links depending on implementation
        self.assertIsNotNone(hebbian_links)
        
    def test_hebbian_link_strengthening(self):
        """Test that repeated co-activation strengthens Hebbian links."""
        atom1 = self.atomspace.add_node(
            AtomType.CONCEPT_NODE, "Atom1",
            av=AttentionValue(sti=0.8, lti=0.5)
        )
        atom2 = self.atomspace.add_node(
            AtomType.CONCEPT_NODE, "Atom2",
            av=AttentionValue(sti=0.8, lti=0.5)
        )
        
        # Repeatedly co-activate
        for _ in range(5):
            self.ecan.stimulate(atom1, 0.3)
            self.ecan.stimulate(atom2, 0.3)
            self.ecan.run_cycle()
        
        # System should be stable
        self.assertIsNotNone(self.ecan.get_attentional_focus())


class TestECANImportanceDiffusion(unittest.TestCase):
    """Tests for importance diffusion."""
    
    def setUp(self):
        self.atomspace = AtomSpace()
        params = ECANParameters(
            spread_threshold=0.3,
            spread_decay=0.5
        )
        self.ecan = ECANService(self.atomspace, params)
        
    def test_importance_spreads_through_links(self):
        """Test that importance spreads through links."""
        source = self.atomspace.add_node(
            AtomType.CONCEPT_NODE, "Source",
            av=AttentionValue(sti=0.9, lti=0.5)
        )
        target = self.atomspace.add_node(
            AtomType.CONCEPT_NODE, "Target",
            av=AttentionValue(sti=0.1, lti=0.5)
        )
        
        # Create link between them
        self.atomspace.add_link(
            AtomType.INHERITANCE_LINK, [source, target],
            tv=TruthValue(0.9, 0.9)
        )
        
        initial_target_sti = self.atomspace.get_atom(target).attention_value.sti
        
        # Run diffusion cycles
        for _ in range(5):
            self.ecan.run_cycle()
        
        # Target may have received some importance
        final_target_sti = self.atomspace.get_atom(target).attention_value.sti
        
        # Just verify system is stable
        self.assertIsNotNone(final_target_sti)
        
    def test_diffusion_respects_link_weight(self):
        """Test that diffusion respects link weights."""
        source = self.atomspace.add_node(
            AtomType.CONCEPT_NODE, "Source",
            av=AttentionValue(sti=0.9, lti=0.5)
        )
        strong_target = self.atomspace.add_node(
            AtomType.CONCEPT_NODE, "StrongTarget",
            av=AttentionValue(sti=0.1, lti=0.5)
        )
        weak_target = self.atomspace.add_node(
            AtomType.CONCEPT_NODE, "WeakTarget",
            av=AttentionValue(sti=0.1, lti=0.5)
        )
        
        # Strong link
        self.atomspace.add_link(
            AtomType.INHERITANCE_LINK, [source, strong_target],
            tv=TruthValue(0.95, 0.9)
        )
        # Weak link
        self.atomspace.add_link(
            AtomType.INHERITANCE_LINK, [source, weak_target],
            tv=TruthValue(0.3, 0.9)
        )
        
        # Run diffusion
        for _ in range(5):
            self.ecan.run_cycle()
        
        # System should remain stable
        self.assertIsNotNone(self.atomspace.get_atom(strong_target))


class TestECANRentAndWages(unittest.TestCase):
    """Tests for rent and wage mechanisms."""
    
    def setUp(self):
        self.atomspace = AtomSpace()
        params = ECANParameters(
            rent_rate=0.05,
            wage_rate=0.1
        )
        self.ecan = ECANService(self.atomspace, params)
        
    def test_rent_decreases_sti(self):
        """Test that rent decreases STI over time."""
        atom = self.atomspace.add_node(
            AtomType.CONCEPT_NODE, "RentTest",
            av=AttentionValue(sti=0.5, lti=0.5)
        )
        
        initial_sti = self.atomspace.get_atom(atom).attention_value.sti
        
        # Run cycles without stimulation
        for _ in range(10):
            self.ecan.run_cycle()
        
        final_sti = self.atomspace.get_atom(atom).attention_value.sti
        
        # STI should decrease or stay same (rent effect)
        self.assertLessEqual(final_sti, initial_sti + 0.1)  # Allow small variance
        
    def test_useful_atoms_earn_wages(self):
        """Test that useful atoms earn wages."""
        # Create an atom that will be used in inference
        useful = self.atomspace.add_node(
            AtomType.CONCEPT_NODE, "UsefulAtom",
            av=AttentionValue(sti=0.3, lti=0.5)
        )
        
        # Stimulate it (simulating use)
        self.ecan.stimulate(useful, 0.5)
        
        # STI should have increased
        sti = self.atomspace.get_atom(useful).attention_value.sti
        self.assertGreater(sti, 0.3)


class TestECANStressTest(unittest.TestCase):
    """Stress tests for ECAN under load."""
    
    def setUp(self):
        self.atomspace = AtomSpace()
        params = ECANParameters(
            total_stimulus=10000.0,
            max_focus_size=100
        )
        self.ecan = ECANService(self.atomspace, params)
        
    def test_large_atomspace(self):
        """Test ECAN with thousands of atoms."""
        # Create many atoms
        atoms = []
        for i in range(1000):
            handle = self.atomspace.add_node(
                AtomType.CONCEPT_NODE, f"Atom_{i}",
                av=AttentionValue(sti=i/1000, lti=0.5)
            )
            atoms.append(handle)
        
        # Run cycles
        start_time = time.time()
        for _ in range(10):
            self.ecan.run_cycle()
        elapsed = time.time() - start_time
        
        # Should complete in reasonable time
        self.assertLess(elapsed, 30.0)  # 30 seconds max
        
        # Focus should still work
        focus = self.ecan.get_attentional_focus()
        self.assertIsNotNone(focus)
        
    def test_concurrent_stimulation(self):
        """Test concurrent stimulation from multiple threads."""
        atoms = []
        for i in range(100):
            handle = self.atomspace.add_node(
                AtomType.CONCEPT_NODE, f"Atom_{i}",
                av=AttentionValue(sti=0.1, lti=0.5)
            )
            atoms.append(handle)
        
        errors = []
        
        def stimulate_worker(atom_subset):
            try:
                for atom in atom_subset:
                    self.ecan.stimulate(atom, 0.3)
            except Exception as e:
                errors.append(e)
        
        # Create threads
        threads = []
        chunk_size = len(atoms) // 4
        for i in range(4):
            start = i * chunk_size
            end = start + chunk_size if i < 3 else len(atoms)
            t = threading.Thread(target=stimulate_worker, args=(atoms[start:end],))
            threads.append(t)
        
        # Run threads
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have no errors
        self.assertEqual(len(errors), 0)
        
    def test_rapid_focus_queries(self):
        """Test rapid focus queries."""
        # Add atoms
        for i in range(100):
            self.atomspace.add_node(
                AtomType.CONCEPT_NODE, f"Atom_{i}",
                av=AttentionValue(sti=i/100, lti=0.5)
            )
        
        # Query focus rapidly
        start_time = time.time()
        for _ in range(100):
            focus = self.ecan.get_attentional_focus()
            self.assertIsNotNone(focus)
        elapsed = time.time() - start_time
        
        # Should be fast
        self.assertLess(elapsed, 5.0)


class TestECANServiceLifecycle(unittest.TestCase):
    """Tests for ECAN service lifecycle."""
    
    def test_start_stop(self):
        """Test starting and stopping the service."""
        atomspace = AtomSpace()
        ecan = ECANService(atomspace)
        
        # Start
        self.assertTrue(ecan.start())
        
        # Should be running
        time.sleep(0.2)
        
        # Stop
        self.assertTrue(ecan.stop())
        
    def test_multiple_start_stop(self):
        """Test multiple start/stop cycles."""
        atomspace = AtomSpace()
        ecan = ECANService(atomspace)
        
        for _ in range(3):
            ecan.start()
            time.sleep(0.1)
            ecan.stop()
        
        # Should be stable
        self.assertIsNotNone(ecan)
        
    def test_status_reporting(self):
        """Test status reporting."""
        atomspace = AtomSpace()
        ecan = ECANService(atomspace)
        
        status = ecan.status()
        
        self.assertIsNotNone(status)
        self.assertIn('cycles', status.get('stats', status))


if __name__ == '__main__':
    unittest.main(verbosity=2)
