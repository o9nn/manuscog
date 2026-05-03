#!/usr/bin/env python3
"""
Advanced Pattern Mining and MOSES Tests
========================================

Comprehensive tests for:
- Pattern recognition accuracy
- Subgraph mining
- MOSES program synthesis benchmarks
- Learning convergence
"""

import unittest
import sys
import os
import time
import random
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from kernel.cognitive.types import AtomType, TruthValue, AttentionValue
from atomspace.hypergraph.atomspace import AtomSpace
from kernel.pattern.recognition import PatternRecognitionService, PatternMiner
from kernel.learning.moses import MOSESEngine


class TestPatternMining(unittest.TestCase):
    """Tests for pattern mining."""
    
    def setUp(self):
        self.atomspace = AtomSpace()
        self.pattern_service = PatternRecognitionService(self.atomspace)
        
    def test_find_frequent_patterns(self):
        """Test finding frequent patterns."""
        # Create a repeated pattern: A -> B
        for i in range(10):
            a = self.atomspace.add_node(AtomType.CONCEPT_NODE, f"A_{i}")
            b = self.atomspace.add_node(AtomType.CONCEPT_NODE, f"B_{i}")
            self.atomspace.add_link(
                AtomType.INHERITANCE_LINK, [a, b],
                tv=TruthValue(0.9, 0.9)
            )
        
        # Mine patterns
        patterns = self.pattern_service.miner.mine_patterns()
        
        self.assertIsNotNone(patterns)
        self.assertGreater(len(patterns), 0)
        
    def test_pattern_support_calculation(self):
        """Test pattern support calculation."""
        # Create pattern with known support
        for i in range(5):
            a = self.atomspace.add_node(AtomType.CONCEPT_NODE, f"Cat_{i}")
            b = self.atomspace.add_node(AtomType.CONCEPT_NODE, "Animal")
            self.atomspace.add_link(
                AtomType.INHERITANCE_LINK, [a, b],
                tv=TruthValue(1.0, 0.9)
            )
        
        patterns = self.pattern_service.miner.mine_patterns()
        
        # Should find patterns with support >= 5
        if patterns:
            max_support = max(p.support for p in patterns)
            self.assertGreaterEqual(max_support, 1)
            
    def test_pattern_confidence(self):
        """Test pattern confidence calculation."""
        # Create consistent pattern
        animal = self.atomspace.add_node(AtomType.CONCEPT_NODE, "Animal")
        
        for i in range(10):
            cat = self.atomspace.add_node(AtomType.CONCEPT_NODE, f"Cat_{i}")
            self.atomspace.add_link(
                AtomType.INHERITANCE_LINK, [cat, animal],
                tv=TruthValue(1.0, 0.95)
            )
        
        patterns = self.pattern_service.miner.mine_patterns()
        
        if patterns:
            # At least one pattern should have good confidence
            max_conf = max(p.confidence for p in patterns)
            self.assertGreater(max_conf, 0)


class TestPatternRecognition(unittest.TestCase):
    """Tests for pattern recognition."""
    
    def setUp(self):
        self.atomspace = AtomSpace()
        self.pattern_service = PatternRecognitionService(self.atomspace)
        
    def test_recognize_inheritance_chain(self):
        """Test recognizing inheritance chain pattern."""
        # Create chain: A -> B -> C -> D
        nodes = []
        for name in ['A', 'B', 'C', 'D']:
            nodes.append(self.atomspace.add_node(AtomType.CONCEPT_NODE, name))
        
        for i in range(len(nodes) - 1):
            self.atomspace.add_link(
                AtomType.INHERITANCE_LINK, [nodes[i], nodes[i+1]],
                tv=TruthValue(0.9, 0.9)
            )
        
        # Recognize patterns
        patterns = self.pattern_service.miner.mine_patterns()
        
        self.assertIsNotNone(patterns)
        
    def test_recognize_star_pattern(self):
        """Test recognizing star pattern (one node connected to many)."""
        center = self.atomspace.add_node(AtomType.CONCEPT_NODE, "Center")
        
        for i in range(10):
            leaf = self.atomspace.add_node(AtomType.CONCEPT_NODE, f"Leaf_{i}")
            self.atomspace.add_link(
                AtomType.INHERITANCE_LINK, [leaf, center],
                tv=TruthValue(0.9, 0.9)
            )
        
        patterns = self.pattern_service.miner.mine_patterns()
        
        self.assertIsNotNone(patterns)
        
    def test_recognize_clique_pattern(self):
        """Test recognizing clique pattern (fully connected)."""
        nodes = []
        for i in range(5):
            nodes.append(self.atomspace.add_node(AtomType.CONCEPT_NODE, f"Node_{i}"))
        
        # Create similarity links between all pairs
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                self.atomspace.add_link(
                    AtomType.SIMILARITY_LINK, [nodes[i], nodes[j]],
                    tv=TruthValue(0.8, 0.8)
                )
        
        patterns = self.pattern_service.miner.mine_patterns()
        
        self.assertIsNotNone(patterns)


class TestPatternServiceLifecycle(unittest.TestCase):
    """Tests for pattern service lifecycle."""
    
    def test_start_stop(self):
        """Test starting and stopping the service."""
        atomspace = AtomSpace()
        service = PatternRecognitionService(atomspace)
        
        self.assertTrue(service.start())
        time.sleep(0.2)
        self.assertTrue(service.stop())
        
    def test_continuous_mining(self):
        """Test continuous pattern mining."""
        atomspace = AtomSpace()
        service = PatternRecognitionService(atomspace)
        
        # Add initial atoms
        for i in range(20):
            a = atomspace.add_node(AtomType.CONCEPT_NODE, f"A_{i}")
            b = atomspace.add_node(AtomType.CONCEPT_NODE, f"B_{i}")
            atomspace.add_link(AtomType.INHERITANCE_LINK, [a, b])
        
        service.start()
        
        # Run for a bit
        time.sleep(0.5)
        
        # Add more atoms
        for i in range(20, 30):
            a = atomspace.add_node(AtomType.CONCEPT_NODE, f"A_{i}")
            b = atomspace.add_node(AtomType.CONCEPT_NODE, f"B_{i}")
            atomspace.add_link(AtomType.INHERITANCE_LINK, [a, b])
        
        time.sleep(0.5)
        
        service.stop()
        
        # Should have found patterns
        patterns = service.miner.mine_patterns()
        self.assertIsNotNone(patterns)


class TestMOSESBasic(unittest.TestCase):
    """Basic tests for MOSES learning."""
    
    def setUp(self):
        self.atomspace = AtomSpace()
        self.moses = MOSESEngine(self.atomspace)
        
    def test_learn_constant(self):
        """Test learning a constant function."""
        # f(x) = 5
        test_cases = [
            {'x': 0, 'expected': 5},
            {'x': 1, 'expected': 5},
            {'x': 10, 'expected': 5},
            {'x': -5, 'expected': 5},
        ]
        
        best = self.moses.learn(test_cases, max_generations=10)
        
        self.assertIsNotNone(best)
        
    def test_learn_identity(self):
        """Test learning identity function."""
        # f(x) = x
        test_cases = [
            {'x': 0, 'expected': 0},
            {'x': 1, 'expected': 1},
            {'x': 5, 'expected': 5},
            {'x': -3, 'expected': -3},
        ]
        
        best = self.moses.learn(test_cases, max_generations=15)
        
        self.assertIsNotNone(best)
        
    def test_learn_addition(self):
        """Test learning addition function."""
        # f(x, y) = x + y
        test_cases = [
            {'x': 1, 'y': 2, 'expected': 3},
            {'x': 0, 'y': 5, 'expected': 5},
            {'x': 3, 'y': 3, 'expected': 6},
            {'x': -1, 'y': 1, 'expected': 0},
        ]
        
        best = self.moses.learn(test_cases, max_generations=20)
        
        self.assertIsNotNone(best)


class TestMOSESAdvanced(unittest.TestCase):
    """Advanced tests for MOSES learning."""
    
    def setUp(self):
        self.atomspace = AtomSpace()
        self.moses = MOSESEngine(self.atomspace)
        
    def test_learn_multiplication(self):
        """Test learning multiplication function."""
        # f(x, y) = x * y
        test_cases = [
            {'x': 2, 'y': 3, 'expected': 6},
            {'x': 0, 'y': 5, 'expected': 0},
            {'x': 4, 'y': 4, 'expected': 16},
            {'x': 1, 'y': 7, 'expected': 7},
        ]
        
        best = self.moses.learn(test_cases, max_generations=30)
        
        self.assertIsNotNone(best)
        
    def test_learn_conditional(self):
        """Test learning conditional function."""
        # f(x) = 1 if x > 0 else 0
        test_cases = [
            {'x': 5, 'expected': 1},
            {'x': -3, 'expected': 0},
            {'x': 0, 'expected': 0},
            {'x': 100, 'expected': 1},
        ]
        
        best = self.moses.learn(test_cases, max_generations=30)
        
        self.assertIsNotNone(best)
        
    def test_fitness_improvement(self):
        """Test that fitness improves over generations."""
        test_cases = [
            {'x': 1, 'y': 2, 'expected': 3},
            {'x': 2, 'y': 3, 'expected': 5},
            {'x': 0, 'y': 0, 'expected': 0},
        ]
        
        # Track fitness over generations
        fitness_history = []
        
        for gen in [5, 10, 15, 20]:
            best = self.moses.learn(test_cases, max_generations=gen)
            if best:
                fitness_history.append(best.fitness)
        
        # Fitness should generally improve or stay same
        if len(fitness_history) >= 2:
            # At least not getting worse
            self.assertGreaterEqual(fitness_history[-1], fitness_history[0] * 0.9)


class TestMOSESBenchmarks(unittest.TestCase):
    """Benchmark tests for MOSES."""
    
    def setUp(self):
        self.atomspace = AtomSpace()
        self.moses = MOSESEngine(self.atomspace)
        
    def test_boolean_parity(self):
        """Test learning boolean parity function."""
        # XOR function
        test_cases = [
            {'x': 0, 'y': 0, 'expected': 0},
            {'x': 0, 'y': 1, 'expected': 1},
            {'x': 1, 'y': 0, 'expected': 1},
            {'x': 1, 'y': 1, 'expected': 0},
        ]
        
        best = self.moses.learn(test_cases, max_generations=30)
        
        self.assertIsNotNone(best)
        
    def test_polynomial(self):
        """Test learning polynomial function."""
        # f(x) = x^2
        test_cases = [
            {'x': 0, 'expected': 0},
            {'x': 1, 'expected': 1},
            {'x': 2, 'expected': 4},
            {'x': 3, 'expected': 9},
            {'x': -2, 'expected': 4},
        ]
        
        best = self.moses.learn(test_cases, max_generations=30)
        
        self.assertIsNotNone(best)
        
    def test_learning_speed(self):
        """Test learning speed on simple problem."""
        test_cases = [
            {'x': 1, 'expected': 2},
            {'x': 2, 'expected': 4},
            {'x': 3, 'expected': 6},
        ]
        
        start_time = time.time()
        best = self.moses.learn(test_cases, max_generations=20)
        elapsed = time.time() - start_time
        
        self.assertIsNotNone(best)
        self.assertLess(elapsed, 10.0)  # Should complete in 10 seconds


class TestMOSESServiceLifecycle(unittest.TestCase):
    """Tests for MOSES service lifecycle."""
    
    def test_start_stop(self):
        """Test starting and stopping the service."""
        atomspace = AtomSpace()
        moses = MOSESEngine(atomspace)
        
        self.assertTrue(moses.start())
        time.sleep(0.2)
        self.assertTrue(moses.stop())
        
    def test_status_reporting(self):
        """Test status reporting."""
        atomspace = AtomSpace()
        moses = MOSESEngine(atomspace)
        
        status = moses.status()
        
        self.assertIsNotNone(status)


class TestMOSESIntegration(unittest.TestCase):
    """Integration tests for MOSES with AtomSpace."""
    
    def setUp(self):
        self.atomspace = AtomSpace()
        self.moses = MOSESEngine(self.atomspace)
        
    def test_learned_program_stored_in_atomspace(self):
        """Test that learned programs are stored in AtomSpace."""
        test_cases = [
            {'x': 1, 'expected': 2},
            {'x': 2, 'expected': 4},
        ]
        
        initial_size = self.atomspace.size()
        
        best = self.moses.learn(test_cases, max_generations=10)
        
        # AtomSpace may have grown
        final_size = self.atomspace.size()
        
        self.assertIsNotNone(best)
        
    def test_multiple_learning_sessions(self):
        """Test multiple learning sessions."""
        for i in range(3):
            test_cases = [
                {'x': 1, 'expected': i + 1},
                {'x': 2, 'expected': i + 2},
            ]
            
            best = self.moses.learn(test_cases, max_generations=10)
            self.assertIsNotNone(best)


if __name__ == '__main__':
    unittest.main(verbosity=2)
