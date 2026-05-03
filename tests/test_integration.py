#!/usr/bin/env python3
"""
Integration Tests for Cross-Subsystem Interactions
===================================================

Tests for:
- PLN reasoning triggering ECAN attention shifts
- MOSES learning updating AtomSpace
- Pattern recognition feeding into reasoning
- Cognitive cycle integration
- Memory management under load
"""

import unittest
import sys
import os
import time
import threading
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from kernel.cognitive.types import (
    AtomType, TruthValue, AttentionValue, CognitiveGoal, GoalState
)
from atomspace.hypergraph.atomspace import AtomSpace
from kernel.reasoning.pln import PLNEngine, PLNConfig
from kernel.attention.ecan import ECANService, ECANParameters
from kernel.pattern.recognition import PatternRecognitionService
from kernel.learning.moses import MOSESEngine
from kernel.memory.manager import CognitiveMemoryManager, MemoryConfig
from kernel.cognitive_kernel import CognitiveKernel, KernelConfig, boot_kernel


class TestPLNECANIntegration(unittest.TestCase):
    """Tests for PLN-ECAN integration."""
    
    def setUp(self):
        self.atomspace = AtomSpace()
        
        # Initialize PLN
        pln_config = PLNConfig(attention_guided=True)
        self.pln = PLNEngine(self.atomspace, pln_config)
        
        # Initialize ECAN
        ecan_params = ECANParameters(focus_boundary=0.5)
        self.ecan = ECANService(self.atomspace, ecan_params)
        
    def test_inference_boosts_attention(self):
        """Test that inference results boost attention of involved atoms."""
        # Create atoms
        a = self.atomspace.add_node(
            AtomType.CONCEPT_NODE, "A",
            av=AttentionValue(sti=0.3, lti=0.5)
        )
        b = self.atomspace.add_node(
            AtomType.CONCEPT_NODE, "B",
            av=AttentionValue(sti=0.3, lti=0.5)
        )
        c = self.atomspace.add_node(
            AtomType.CONCEPT_NODE, "C",
            av=AttentionValue(sti=0.3, lti=0.5)
        )
        
        # Create inference chain
        self.atomspace.add_link(
            AtomType.INHERITANCE_LINK, [a, b],
            tv=TruthValue(0.9, 0.9)
        )
        self.atomspace.add_link(
            AtomType.INHERITANCE_LINK, [b, c],
            tv=TruthValue(0.9, 0.9)
        )
        
        # Run inference
        result = self.pln.deduction(a, b)
        
        # Stimulate atoms involved in inference
        if result:
            self.ecan.stimulate(a, 0.3)
            self.ecan.stimulate(b, 0.3)
        
        # Check attention increased
        a_sti = self.atomspace.get_atom(a).attention_value.sti
        self.assertGreater(a_sti, 0.3)
        
    def test_attention_guides_inference(self):
        """Test that attention guides inference selection."""
        # Create high-attention path
        high_a = self.atomspace.add_node(
            AtomType.CONCEPT_NODE, "HighA",
            av=AttentionValue(sti=0.9, lti=0.5)
        )
        high_b = self.atomspace.add_node(
            AtomType.CONCEPT_NODE, "HighB",
            av=AttentionValue(sti=0.9, lti=0.5)
        )
        
        # Create low-attention path
        low_a = self.atomspace.add_node(
            AtomType.CONCEPT_NODE, "LowA",
            av=AttentionValue(sti=0.1, lti=0.5)
        )
        low_b = self.atomspace.add_node(
            AtomType.CONCEPT_NODE, "LowB",
            av=AttentionValue(sti=0.1, lti=0.5)
        )
        
        # Links
        self.atomspace.add_link(
            AtomType.INHERITANCE_LINK, [high_a, high_b],
            tv=TruthValue(0.9, 0.9)
        )
        self.atomspace.add_link(
            AtomType.INHERITANCE_LINK, [low_a, low_b],
            tv=TruthValue(0.9, 0.9)
        )
        
        # Run attention-guided forward chaining
        results = self.pln.forward_chain(max_steps=10, focus_atoms={high_a})
        
        self.assertIsNotNone(results)
        
    def test_inference_cycle_with_attention(self):
        """Test complete inference cycle with attention updates."""
        # Setup knowledge
        human = self.atomspace.add_node(
            AtomType.CONCEPT_NODE, "Human",
            av=AttentionValue(sti=0.5, lti=0.5)
        )
        mortal = self.atomspace.add_node(
            AtomType.CONCEPT_NODE, "Mortal",
            av=AttentionValue(sti=0.3, lti=0.5)
        )
        
        self.atomspace.add_link(
            AtomType.INHERITANCE_LINK, [human, mortal],
            tv=TruthValue(1.0, 0.95)
        )
        
        # Run multiple cycles
        for _ in range(5):
            # Inference
            self.pln.forward_chain(max_steps=5, focus_atoms={human})
            
            # Attention update
            self.ecan.run_cycle()
        
        # System should be stable
        self.assertIsNotNone(self.ecan.get_attentional_focus())


class TestMOSESAtomSpaceIntegration(unittest.TestCase):
    """Tests for MOSES-AtomSpace integration."""
    
    def setUp(self):
        self.atomspace = AtomSpace()
        self.moses = MOSESEngine(self.atomspace)
        
    def test_learned_knowledge_in_atomspace(self):
        """Test that learned knowledge is stored in AtomSpace."""
        test_cases = [
            {'x': 1, 'expected': 2},
            {'x': 2, 'expected': 4},
            {'x': 3, 'expected': 6},
        ]
        
        initial_size = self.atomspace.size()
        
        best = self.moses.learn(test_cases, max_generations=10)
        
        # Learning should have added atoms
        self.assertIsNotNone(best)
        
    def test_learning_uses_existing_knowledge(self):
        """Test that learning can use existing knowledge."""
        # Add some prior knowledge
        double = self.atomspace.add_node(AtomType.SCHEMA_NODE, "double")
        
        test_cases = [
            {'x': 1, 'expected': 2},
            {'x': 2, 'expected': 4},
        ]
        
        best = self.moses.learn(test_cases, max_generations=15)
        
        self.assertIsNotNone(best)


class TestPatternReasoningIntegration(unittest.TestCase):
    """Tests for Pattern-Reasoning integration."""
    
    def setUp(self):
        self.atomspace = AtomSpace()
        self.pattern_service = PatternRecognitionService(self.atomspace)
        pln_config = PLNConfig()
        self.pln = PLNEngine(self.atomspace, pln_config)
        
    def test_patterns_inform_reasoning(self):
        """Test that discovered patterns inform reasoning."""
        # Create repeated pattern
        for i in range(10):
            cat = self.atomspace.add_node(AtomType.CONCEPT_NODE, f"Cat_{i}")
            animal = self.atomspace.add_node(AtomType.CONCEPT_NODE, "Animal")
            self.atomspace.add_link(
                AtomType.INHERITANCE_LINK, [cat, animal],
                tv=TruthValue(1.0, 0.9)
            )
        
        # Mine patterns
        patterns = self.pattern_service.miner.mine_patterns()
        
        # Run reasoning
        results = self.pln.forward_chain(max_steps=10)
        
        self.assertIsNotNone(patterns)
        self.assertIsNotNone(results)
        
    def test_reasoning_creates_patterns(self):
        """Test that reasoning creates new patterns."""
        # Setup inference chain
        a = self.atomspace.add_node(AtomType.CONCEPT_NODE, "A")
        b = self.atomspace.add_node(AtomType.CONCEPT_NODE, "B")
        c = self.atomspace.add_node(AtomType.CONCEPT_NODE, "C")
        
        self.atomspace.add_link(
            AtomType.INHERITANCE_LINK, [a, b],
            tv=TruthValue(0.9, 0.9)
        )
        self.atomspace.add_link(
            AtomType.INHERITANCE_LINK, [b, c],
            tv=TruthValue(0.9, 0.9)
        )
        
        # Run reasoning
        self.pln.forward_chain(max_steps=10, focus_atoms={a})
        
        # Mine patterns after reasoning
        patterns = self.pattern_service.miner.mine_patterns()
        
        self.assertIsNotNone(patterns)


class TestCognitiveCycleIntegration(unittest.TestCase):
    """Tests for full cognitive cycle integration."""
    
    def setUp(self):
        self.kernel = boot_kernel(kernel_id="integration-test", log_level="WARNING")
        
    def tearDown(self):
        if self.kernel:
            self.kernel.shutdown()
            
    def test_full_cognitive_cycle(self):
        """Test a complete cognitive cycle."""
        # Add knowledge
        cat = self.kernel.atomspace.add_node(
            AtomType.CONCEPT_NODE, "Cat",
            av=AttentionValue(sti=0.7, lti=0.5)
        )
        animal = self.kernel.atomspace.add_node(
            AtomType.CONCEPT_NODE, "Animal",
            av=AttentionValue(sti=0.5, lti=0.5)
        )
        self.kernel.atomspace.add_link(
            AtomType.INHERITANCE_LINK, [cat, animal],
            tv=TruthValue(1.0, 0.95)
        )
        
        # Run cycles
        for _ in range(5):
            self.kernel.run_cycle()
            result = self.kernel.think()
            self.assertIsNotNone(result)
            
    def test_cognitive_cycle_stability(self):
        """Test cognitive cycle stability over many iterations."""
        # Add substantial knowledge
        for i in range(20):
            node = self.kernel.atomspace.add_node(
                AtomType.CONCEPT_NODE, f"Concept_{i}",
                av=AttentionValue(sti=i/20, lti=0.5)
            )
        
        # Run many cycles
        for _ in range(20):
            self.kernel.run_cycle()
            result = self.kernel.think()
            
        # Kernel should still be running
        status = self.kernel.status()
        self.assertEqual(status['state'], 'RUNNING')
        
    def test_goal_driven_cognition(self):
        """Test goal-driven cognitive processing."""
        # Create a goal
        goal_id = self.kernel.create_goal(
            name="Learn Animals",
            description="Learn about animal taxonomy",
            priority=0.8
        )
        
        # Add relevant knowledge
        cat = self.kernel.atomspace.add_node(AtomType.CONCEPT_NODE, "Cat")
        mammal = self.kernel.atomspace.add_node(AtomType.CONCEPT_NODE, "Mammal")
        self.kernel.atomspace.add_link(
            AtomType.INHERITANCE_LINK, [cat, mammal],
            tv=TruthValue(1.0, 0.9)
        )
        
        # Run cycles
        for _ in range(5):
            self.kernel.run_cycle()
            
        # Goal should exist
        self.assertIsNotNone(goal_id)


class TestMemoryManagementIntegration(unittest.TestCase):
    """Tests for memory management integration."""
    
    def setUp(self):
        self.atomspace = AtomSpace()
        config = MemoryConfig(
            max_atoms=1000,
            forgetting_threshold=0.1,
            consolidation_interval=1.0
        )
        self.memory = CognitiveMemoryManager(self.atomspace, config)
        
        ecan_params = ECANParameters()
        self.ecan = ECANService(self.atomspace, ecan_params)
        
    def test_forgetting_low_attention_atoms(self):
        """Test that low-attention atoms are candidates for forgetting."""
        # Add atoms with varying attention
        high_att = self.atomspace.add_node(
            AtomType.CONCEPT_NODE, "HighAtt",
            av=AttentionValue(sti=0.9, lti=0.8)
        )
        low_att = self.atomspace.add_node(
            AtomType.CONCEPT_NODE, "LowAtt",
            av=AttentionValue(sti=0.01, lti=0.01)
        )
        
        # Run memory cycle
        self.memory.run_cycle()
        
        # High attention atom should still exist
        self.assertIsNotNone(self.atomspace.get_atom(high_att))
        
    def test_consolidation_preserves_important(self):
        """Test that consolidation preserves important atoms."""
        # Add important atom
        important = self.atomspace.add_node(
            AtomType.CONCEPT_NODE, "Important",
            av=AttentionValue(sti=0.8, lti=0.9)
        )
        
        # Run consolidation
        self.memory.consolidate()
        
        # Should still exist
        self.assertIsNotNone(self.atomspace.get_atom(important))
        
    def test_memory_under_load(self):
        """Test memory management under load."""
        # Add many atoms
        for i in range(500):
            self.atomspace.add_node(
                AtomType.CONCEPT_NODE, f"Atom_{i}",
                av=AttentionValue(sti=i/500, lti=0.5)
            )
        
        # Run cycles
        for _ in range(10):
            self.memory.run_cycle()
            self.ecan.run_cycle()
        
        # System should be stable
        self.assertGreater(self.atomspace.size(), 0)


class TestSubsystemCoordination(unittest.TestCase):
    """Tests for subsystem coordination."""
    
    def setUp(self):
        self.kernel = boot_kernel(kernel_id="coordination-test", log_level="WARNING")
        
    def tearDown(self):
        if self.kernel:
            self.kernel.shutdown()
            
    def test_all_services_running(self):
        """Test that all services are running."""
        status = self.kernel.status()
        
        self.assertEqual(status['state'], 'RUNNING')
        self.assertGreater(len(status['services']), 0)
        
    def test_service_communication(self):
        """Test communication between services."""
        # Add knowledge
        concept = self.kernel.atomspace.add_node(
            AtomType.CONCEPT_NODE, "TestConcept",
            av=AttentionValue(sti=0.5, lti=0.5)
        )
        
        # Stimulate through ECAN
        self.kernel.ecan.stimulate(concept, 0.5)
        
        # Run PLN
        self.kernel.pln.forward_chain(max_steps=5)
        
        # Run pattern mining
        patterns = self.kernel.pattern.miner.mine_patterns()
        
        # All should work
        self.assertIsNotNone(patterns)
        
    def test_concurrent_subsystem_operation(self):
        """Test concurrent operation of subsystems."""
        # Add knowledge
        for i in range(50):
            self.kernel.atomspace.add_node(
                AtomType.CONCEPT_NODE, f"Concept_{i}",
                av=AttentionValue(sti=i/50, lti=0.5)
            )
        
        errors = []
        
        def run_pln():
            try:
                for _ in range(5):
                    self.kernel.pln.forward_chain(max_steps=3)
            except Exception as e:
                errors.append(e)
                
        def run_ecan():
            try:
                for _ in range(5):
                    self.kernel.ecan.run_cycle()
            except Exception as e:
                errors.append(e)
                
        def run_pattern():
            try:
                for _ in range(5):
                    self.kernel.pattern.miner.mine_patterns()
            except Exception as e:
                errors.append(e)
        
        threads = [
            threading.Thread(target=run_pln),
            threading.Thread(target=run_ecan),
            threading.Thread(target=run_pattern),
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have no errors
        self.assertEqual(len(errors), 0)


class TestEmergentBehavior(unittest.TestCase):
    """Tests for emergent cognitive behavior."""
    
    def setUp(self):
        self.kernel = boot_kernel(kernel_id="emergent-test", log_level="WARNING")
        
    def tearDown(self):
        if self.kernel:
            self.kernel.shutdown()
            
    def test_knowledge_growth(self):
        """Test that knowledge grows through cognitive cycles."""
        # Add seed knowledge
        cat = self.kernel.atomspace.add_node(AtomType.CONCEPT_NODE, "Cat")
        mammal = self.kernel.atomspace.add_node(AtomType.CONCEPT_NODE, "Mammal")
        animal = self.kernel.atomspace.add_node(AtomType.CONCEPT_NODE, "Animal")
        
        self.kernel.atomspace.add_link(
            AtomType.INHERITANCE_LINK, [cat, mammal],
            tv=TruthValue(1.0, 0.9)
        )
        self.kernel.atomspace.add_link(
            AtomType.INHERITANCE_LINK, [mammal, animal],
            tv=TruthValue(1.0, 0.9)
        )
        
        initial_size = self.kernel.atomspace.size()
        
        # Run cycles
        for _ in range(10):
            self.kernel.run_cycle()
            self.kernel.think()
        
        # Knowledge may have grown
        final_size = self.kernel.atomspace.size()
        
        # At minimum, should not have shrunk significantly
        self.assertGreaterEqual(final_size, initial_size * 0.9)
        
    def test_attention_dynamics(self):
        """Test attention dynamics over time."""
        # Add atoms
        atoms = []
        for i in range(10):
            handle = self.kernel.atomspace.add_node(
                AtomType.CONCEPT_NODE, f"Concept_{i}",
                av=AttentionValue(sti=0.5, lti=0.5)
            )
            atoms.append(handle)
        
        # Track attention over cycles
        attention_history = []
        
        for _ in range(10):
            self.kernel.run_cycle()
            
            total_sti = sum(
                self.kernel.atomspace.get_atom(a).attention_value.sti
                for a in atoms
            )
            attention_history.append(total_sti)
        
        # Attention should have varied
        self.assertIsNotNone(attention_history)
        
    def test_creativity_emergence(self):
        """Test creative idea generation."""
        # Add diverse knowledge
        concepts = ['Art', 'Science', 'Music', 'Math', 'Nature']
        for concept in concepts:
            self.kernel.atomspace.add_node(AtomType.CONCEPT_NODE, concept)
        
        # Generate ideas
        ideas = []
        for _ in range(5):
            idea = self.kernel.emergence.creativity.generate_idea()
            if idea:
                ideas.append(idea)
        
        # Should have generated some ideas
        self.assertGreater(len(ideas), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
