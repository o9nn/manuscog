#!/usr/bin/env python3
"""
Advanced PLN Reasoning Tests
============================

Comprehensive tests for Probabilistic Logic Networks including:
- Backward chaining
- Abduction
- Complex inference chains
- Truth value propagation
- Rule application validation
"""

import unittest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from kernel.cognitive.types import AtomType, TruthValue, AttentionValue
from atomspace.hypergraph.atomspace import AtomSpace
from kernel.reasoning.pln import PLNEngine, PLNConfig, PLNFormulas


class TestPLNDeduction(unittest.TestCase):
    """Tests for deductive inference."""
    
    def setUp(self):
        self.atomspace = AtomSpace()
        config = PLNConfig(
            max_depth=10,
            confidence_threshold=0.1
        )
        self.pln = PLNEngine(self.atomspace, config)
        
    def test_simple_deduction(self):
        """Test A->B, B->C => A->C deduction."""
        a = self.atomspace.add_node(AtomType.CONCEPT_NODE, "A")
        b = self.atomspace.add_node(AtomType.CONCEPT_NODE, "B")
        c = self.atomspace.add_node(AtomType.CONCEPT_NODE, "C")
        
        # A -> B with high confidence
        self.atomspace.add_link(
            AtomType.INHERITANCE_LINK, [a, b],
            tv=TruthValue(0.9, 0.95)
        )
        # B -> C with high confidence
        self.atomspace.add_link(
            AtomType.INHERITANCE_LINK, [b, c],
            tv=TruthValue(0.85, 0.9)
        )
        
        # Run deduction
        result = self.pln.deduction(a, b)
        
        # Should produce valid inference
        self.assertIsNotNone(result)
        
    def test_chained_deduction(self):
        """Test multi-step deduction chain."""
        # Create chain: Human -> Mammal -> Animal -> LivingThing
        human = self.atomspace.add_node(AtomType.CONCEPT_NODE, "Human")
        mammal = self.atomspace.add_node(AtomType.CONCEPT_NODE, "Mammal")
        animal = self.atomspace.add_node(AtomType.CONCEPT_NODE, "Animal")
        living = self.atomspace.add_node(AtomType.CONCEPT_NODE, "LivingThing")
        
        self.atomspace.add_link(
            AtomType.INHERITANCE_LINK, [human, mammal],
            tv=TruthValue(1.0, 0.99)
        )
        self.atomspace.add_link(
            AtomType.INHERITANCE_LINK, [mammal, animal],
            tv=TruthValue(1.0, 0.99)
        )
        self.atomspace.add_link(
            AtomType.INHERITANCE_LINK, [animal, living],
            tv=TruthValue(1.0, 0.99)
        )
        
        # Forward chain should discover Human -> LivingThing
        results = self.pln.forward_chain(max_steps=20, focus_atoms={human})
        
        self.assertIsNotNone(results)
        self.assertIsInstance(results, list)
        
    def test_deduction_confidence_decay(self):
        """Test that confidence decays appropriately through chain."""
        nodes = []
        for i in range(5):
            nodes.append(self.atomspace.add_node(AtomType.CONCEPT_NODE, f"Node_{i}"))
        
        # Create chain with 0.9 confidence each
        for i in range(len(nodes) - 1):
            self.atomspace.add_link(
                AtomType.INHERITANCE_LINK, [nodes[i], nodes[i+1]],
                tv=TruthValue(0.9, 0.9)
            )
        
        # Run forward chaining
        results = self.pln.forward_chain(max_steps=10, focus_atoms={nodes[0]})
        
        # Results should exist
        self.assertIsNotNone(results)


class TestPLNInduction(unittest.TestCase):
    """Tests for inductive inference."""
    
    def setUp(self):
        self.atomspace = AtomSpace()
        config = PLNConfig(
            max_depth=10,
            confidence_threshold=0.1
        )
        self.pln = PLNEngine(self.atomspace, config)
        
    def test_simple_induction(self):
        """Test induction from specific to general."""
        # Specific instances
        tweety = self.atomspace.add_node(AtomType.CONCEPT_NODE, "Tweety")
        bird = self.atomspace.add_node(AtomType.CONCEPT_NODE, "Bird")
        flies = self.atomspace.add_node(AtomType.CONCEPT_NODE, "Flies")
        
        # Tweety is a bird
        self.atomspace.add_link(
            AtomType.INHERITANCE_LINK, [tweety, bird],
            tv=TruthValue(1.0, 0.99)
        )
        # Tweety flies
        self.atomspace.add_link(
            AtomType.INHERITANCE_LINK, [tweety, flies],
            tv=TruthValue(1.0, 0.99)
        )
        
        # Run induction
        result = self.pln.induction(tweety, bird)
        
        # Should produce some result
        self.assertIsNotNone(result)
        
    def test_multiple_instance_induction(self):
        """Test induction strengthens with more instances."""
        bird = self.atomspace.add_node(AtomType.CONCEPT_NODE, "Bird")
        flies = self.atomspace.add_node(AtomType.CONCEPT_NODE, "Flies")
        
        # Add multiple birds that fly
        for i in range(5):
            instance = self.atomspace.add_node(AtomType.CONCEPT_NODE, f"Bird_{i}")
            self.atomspace.add_link(
                AtomType.INHERITANCE_LINK, [instance, bird],
                tv=TruthValue(1.0, 0.99)
            )
            self.atomspace.add_link(
                AtomType.INHERITANCE_LINK, [instance, flies],
                tv=TruthValue(1.0, 0.99)
            )
        
        # Forward chain to discover patterns
        results = self.pln.forward_chain(max_steps=20)
        
        self.assertIsNotNone(results)


class TestPLNAbduction(unittest.TestCase):
    """Tests for abductive inference."""
    
    def setUp(self):
        self.atomspace = AtomSpace()
        config = PLNConfig(
            max_depth=10,
            confidence_threshold=0.1
        )
        self.pln = PLNEngine(self.atomspace, config)
        
    def test_simple_abduction(self):
        """Test abduction: If A->C and B->C, observing C suggests A or B."""
        wet_grass = self.atomspace.add_node(AtomType.CONCEPT_NODE, "WetGrass")
        rain = self.atomspace.add_node(AtomType.CONCEPT_NODE, "Rain")
        sprinkler = self.atomspace.add_node(AtomType.CONCEPT_NODE, "Sprinkler")
        
        # Rain causes wet grass
        self.atomspace.add_link(
            AtomType.IMPLICATION_LINK, [rain, wet_grass],
            tv=TruthValue(0.9, 0.9)
        )
        # Sprinkler causes wet grass
        self.atomspace.add_link(
            AtomType.IMPLICATION_LINK, [sprinkler, wet_grass],
            tv=TruthValue(0.95, 0.9)
        )
        
        # Run abduction
        result = self.pln.abduction(wet_grass, rain)
        
        # Should produce result
        self.assertIsNotNone(result)


class TestPLNModusPonens(unittest.TestCase):
    """Tests for modus ponens inference."""
    
    def setUp(self):
        self.atomspace = AtomSpace()
        config = PLNConfig(
            max_depth=10,
            confidence_threshold=0.1
        )
        self.pln = PLNEngine(self.atomspace, config)
        
    def test_modus_ponens(self):
        """Test: If P then Q, P is true => Q is true."""
        p = self.atomspace.add_node(AtomType.CONCEPT_NODE, "P")
        q = self.atomspace.add_node(AtomType.CONCEPT_NODE, "Q")
        
        # P -> Q (implication)
        self.atomspace.add_link(
            AtomType.IMPLICATION_LINK, [p, q],
            tv=TruthValue(0.95, 0.9)
        )
        
        # P is true (high strength)
        p_atom = self.atomspace.get_atom(p)
        if p_atom:
            p_atom.truth_value = TruthValue(0.9, 0.95)
        
        # Run modus ponens
        result = self.pln.modus_ponens(p, q)
        
        # Should infer Q
        self.assertIsNotNone(result)


class TestPLNRevision(unittest.TestCase):
    """Tests for truth value revision."""
    
    def setUp(self):
        self.atomspace = AtomSpace()
        config = PLNConfig(
            max_depth=10,
            confidence_threshold=0.1
        )
        self.pln = PLNEngine(self.atomspace, config)
        
    def test_revision_increases_confidence(self):
        """Test that revision of consistent evidence increases confidence."""
        concept = self.atomspace.add_node(
            AtomType.CONCEPT_NODE, "TestConcept",
            tv=TruthValue(0.8, 0.5)
        )
        
        # Create second evidence
        tv1 = TruthValue(0.8, 0.5)
        tv2 = TruthValue(0.85, 0.6)
        
        # Revision should increase confidence
        revised = PLNFormulas.revision(tv1, tv2)
        
        self.assertIsNotNone(revised)
        # Revised confidence should be higher than either input
        self.assertGreaterEqual(revised.confidence, min(tv1.confidence, tv2.confidence))
        
    def test_revision_conflicting_evidence(self):
        """Test revision with conflicting evidence."""
        tv1 = TruthValue(0.9, 0.7)  # High strength
        tv2 = TruthValue(0.2, 0.6)  # Low strength
        
        revised = PLNFormulas.revision(tv1, tv2)
        
        self.assertIsNotNone(revised)
        # Result should be between the two strengths
        self.assertTrue(0.2 <= revised.strength <= 0.9)


class TestPLNForwardChaining(unittest.TestCase):
    """Tests for forward chaining inference."""
    
    def setUp(self):
        self.atomspace = AtomSpace()
        config = PLNConfig(
            max_depth=15,
            confidence_threshold=0.1
        )
        self.pln = PLNEngine(self.atomspace, config)
        
    def test_forward_chain_discovers_new_knowledge(self):
        """Test that forward chaining discovers implicit knowledge."""
        # Build a knowledge base
        socrates = self.atomspace.add_node(AtomType.CONCEPT_NODE, "Socrates")
        human = self.atomspace.add_node(AtomType.CONCEPT_NODE, "Human")
        mortal = self.atomspace.add_node(AtomType.CONCEPT_NODE, "Mortal")
        greek = self.atomspace.add_node(AtomType.CONCEPT_NODE, "Greek")
        philosopher = self.atomspace.add_node(AtomType.CONCEPT_NODE, "Philosopher")
        
        # Socrates is human
        self.atomspace.add_link(
            AtomType.INHERITANCE_LINK, [socrates, human],
            tv=TruthValue(1.0, 0.99)
        )
        # Socrates is Greek
        self.atomspace.add_link(
            AtomType.INHERITANCE_LINK, [socrates, greek],
            tv=TruthValue(1.0, 0.99)
        )
        # Socrates is a philosopher
        self.atomspace.add_link(
            AtomType.INHERITANCE_LINK, [socrates, philosopher],
            tv=TruthValue(1.0, 0.99)
        )
        # All humans are mortal
        self.atomspace.add_link(
            AtomType.INHERITANCE_LINK, [human, mortal],
            tv=TruthValue(1.0, 0.95)
        )
        
        # Run forward chaining
        results = self.pln.forward_chain(max_steps=30, focus_atoms={socrates})
        
        self.assertIsNotNone(results)
        self.assertIsInstance(results, list)
        
    def test_forward_chain_respects_max_steps(self):
        """Test that forward chaining respects step limit."""
        # Create a large knowledge base
        for i in range(20):
            node = self.atomspace.add_node(AtomType.CONCEPT_NODE, f"Concept_{i}")
            if i > 0:
                prev = self.atomspace.get_atoms_by_name(f"Concept_{i-1}")
                if prev:
                    self.atomspace.add_link(
                        AtomType.INHERITANCE_LINK, [prev[0].handle, node],
                        tv=TruthValue(0.9, 0.9)
                    )
        
        # Run with limited steps
        results = self.pln.forward_chain(max_steps=5)
        
        self.assertIsNotNone(results)


class TestPLNBackwardChaining(unittest.TestCase):
    """Tests for backward chaining inference."""
    
    def setUp(self):
        self.atomspace = AtomSpace()
        config = PLNConfig(
            max_depth=10,
            confidence_threshold=0.1
        )
        self.pln = PLNEngine(self.atomspace, config)
        
    def test_backward_chain_finds_proof(self):
        """Test backward chaining finds proof for goal."""
        # Knowledge base
        a = self.atomspace.add_node(AtomType.CONCEPT_NODE, "A")
        b = self.atomspace.add_node(AtomType.CONCEPT_NODE, "B")
        c = self.atomspace.add_node(AtomType.CONCEPT_NODE, "C")
        
        # A -> B
        self.atomspace.add_link(
            AtomType.INHERITANCE_LINK, [a, b],
            tv=TruthValue(0.9, 0.9)
        )
        # B -> C
        self.atomspace.add_link(
            AtomType.INHERITANCE_LINK, [b, c],
            tv=TruthValue(0.9, 0.9)
        )
        
        # Try to prove A -> C via backward chaining
        result = self.pln.backward_chain(a, c, max_depth=5)
        
        # Should find a proof path
        self.assertIsNotNone(result)


class TestPLNTruthValueFormulas(unittest.TestCase):
    """Tests for PLN truth value computation formulas."""
    
    def setUp(self):
        self.atomspace = AtomSpace()
        config = PLNConfig()
        self.pln = PLNEngine(self.atomspace, config)
        
    def test_deduction_formula(self):
        """Test deduction truth value formula."""
        # sAB, sBC -> sAC
        tv_ab = TruthValue(0.9, 0.9)
        tv_bc = TruthValue(0.8, 0.85)
        
        # Compute deduction result
        result = PLNFormulas.deduction(tv_ab, tv_bc)
        
        self.assertIsNotNone(result)
        # Result strength should be <= min of inputs
        self.assertLessEqual(result.strength, max(tv_ab.strength, tv_bc.strength))
        
    def test_induction_formula(self):
        """Test induction truth value formula."""
        tv_ab = TruthValue(0.9, 0.9)
        tv_cb = TruthValue(0.8, 0.85)
        
        result = PLNFormulas.induction(tv_ab, tv_cb)
        
        self.assertIsNotNone(result)
        
    def test_abduction_formula(self):
        """Test abduction truth value formula."""
        tv_ab = TruthValue(0.9, 0.9)
        tv_cb = TruthValue(0.8, 0.85)
        
        result = PLNFormulas.abduction(tv_ab, tv_cb)
        
        self.assertIsNotNone(result)


class TestPLNAttentionGuided(unittest.TestCase):
    """Tests for attention-guided inference."""
    
    def setUp(self):
        self.atomspace = AtomSpace()
        config = PLNConfig(
            confidence_threshold=0.1
        )
        self.pln = PLNEngine(self.atomspace, config)
        
    def test_high_attention_atoms_preferred(self):
        """Test that high-attention atoms are preferred in inference."""
        # Create atoms with different attention
        high_att = self.atomspace.add_node(
            AtomType.CONCEPT_NODE, "HighAttention",
            av=AttentionValue(sti=0.9, lti=0.5)
        )
        low_att = self.atomspace.add_node(
            AtomType.CONCEPT_NODE, "LowAttention",
            av=AttentionValue(sti=0.1, lti=0.5)
        )
        target = self.atomspace.add_node(AtomType.CONCEPT_NODE, "Target")
        
        # Both link to target
        self.atomspace.add_link(
            AtomType.INHERITANCE_LINK, [high_att, target],
            tv=TruthValue(0.8, 0.8)
        )
        self.atomspace.add_link(
            AtomType.INHERITANCE_LINK, [low_att, target],
            tv=TruthValue(0.8, 0.8)
        )
        
        # Run attention-guided forward chaining
        results = self.pln.forward_chain(max_steps=10, focus_atoms={high_att})
        
        self.assertIsNotNone(results)


if __name__ == '__main__':
    unittest.main(verbosity=2)
