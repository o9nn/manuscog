"""
OpenCog Inferno AGI - MOSES-Inspired Learning System
====================================================

MOSES (Meta-Optimizing Semantic Evolutionary Search) is a program
learning system that evolves programs to solve problems.

This implementation provides:
- Program representation in the AtomSpace
- Evolutionary operators (mutation, crossover)
- Fitness evaluation
- Deme management (population subgroups)
- Integration with the cognitive kernel

MOSES learns by evolving programs that maximize a fitness function,
guided by attention allocation and probabilistic reasoning.
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
import copy
from collections import defaultdict

from kernel.cognitive.types import (
    Atom, Node, Link, AtomHandle, AtomType,
    TruthValue, AttentionValue, LearningService
)
from atomspace.hypergraph.atomspace import AtomSpace


# =============================================================================
# PROGRAM REPRESENTATION
# =============================================================================

class ProgramNodeType(Enum):
    """Types of nodes in program trees."""
    # Logical operators
    AND = auto()
    OR = auto()
    NOT = auto()
    
    # Arithmetic operators
    PLUS = auto()
    MINUS = auto()
    TIMES = auto()
    DIVIDE = auto()
    
    # Comparison operators
    GREATER = auto()
    LESS = auto()
    EQUAL = auto()
    
    # Control flow
    IF = auto()
    
    # Terminals
    INPUT = auto()      # Input variable
    CONSTANT = auto()   # Constant value
    
    # Special
    SCHEMA = auto()     # Reference to another schema


@dataclass
class ProgramNode:
    """A node in a program tree."""
    node_type: ProgramNodeType
    value: Any = None           # For constants and inputs
    children: List['ProgramNode'] = field(default_factory=list)
    
    def copy(self) -> 'ProgramNode':
        """Deep copy the program node."""
        return ProgramNode(
            node_type=self.node_type,
            value=self.value,
            children=[c.copy() for c in self.children]
        )
    
    def size(self) -> int:
        """Get the size of the subtree."""
        return 1 + sum(c.size() for c in self.children)
    
    def depth(self) -> int:
        """Get the depth of the subtree."""
        if not self.children:
            return 1
        return 1 + max(c.depth() for c in self.children)
    
    def to_string(self) -> str:
        """Convert to string representation."""
        if self.node_type == ProgramNodeType.CONSTANT:
            return str(self.value)
        elif self.node_type == ProgramNodeType.INPUT:
            return f"${self.value}"
        elif not self.children:
            return self.node_type.name
        else:
            children_str = ", ".join(c.to_string() for c in self.children)
            return f"{self.node_type.name}({children_str})"
    
    def evaluate(self, inputs: Dict[str, Any]) -> Any:
        """Evaluate the program with given inputs."""
        if self.node_type == ProgramNodeType.CONSTANT:
            return self.value
        elif self.node_type == ProgramNodeType.INPUT:
            return inputs.get(self.value, 0)
        elif self.node_type == ProgramNodeType.AND:
            return all(c.evaluate(inputs) for c in self.children)
        elif self.node_type == ProgramNodeType.OR:
            return any(c.evaluate(inputs) for c in self.children)
        elif self.node_type == ProgramNodeType.NOT:
            return not self.children[0].evaluate(inputs) if self.children else False
        elif self.node_type == ProgramNodeType.PLUS:
            return sum(c.evaluate(inputs) for c in self.children)
        elif self.node_type == ProgramNodeType.MINUS:
            if len(self.children) >= 2:
                return self.children[0].evaluate(inputs) - self.children[1].evaluate(inputs)
            return 0
        elif self.node_type == ProgramNodeType.TIMES:
            result = 1
            for c in self.children:
                result *= c.evaluate(inputs)
            return result
        elif self.node_type == ProgramNodeType.DIVIDE:
            if len(self.children) >= 2:
                divisor = self.children[1].evaluate(inputs)
                if divisor != 0:
                    return self.children[0].evaluate(inputs) / divisor
            return 0
        elif self.node_type == ProgramNodeType.GREATER:
            if len(self.children) >= 2:
                return self.children[0].evaluate(inputs) > self.children[1].evaluate(inputs)
            return False
        elif self.node_type == ProgramNodeType.LESS:
            if len(self.children) >= 2:
                return self.children[0].evaluate(inputs) < self.children[1].evaluate(inputs)
            return False
        elif self.node_type == ProgramNodeType.EQUAL:
            if len(self.children) >= 2:
                return self.children[0].evaluate(inputs) == self.children[1].evaluate(inputs)
            return False
        elif self.node_type == ProgramNodeType.IF:
            if len(self.children) >= 3:
                cond = self.children[0].evaluate(inputs)
                return self.children[1].evaluate(inputs) if cond else self.children[2].evaluate(inputs)
            return 0
        return 0


@dataclass
class Program:
    """A complete program with metadata."""
    program_id: str = field(default_factory=lambda: f"prog_{random.randint(0, 99999):05d}")
    root: Optional[ProgramNode] = None
    fitness: float = 0.0
    complexity: float = 0.0
    generation: int = 0
    parent_ids: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    
    def copy(self) -> 'Program':
        """Create a copy of this program."""
        return Program(
            program_id=f"prog_{random.randint(0, 99999):05d}",
            root=self.root.copy() if self.root else None,
            fitness=0.0,  # Reset fitness for new program
            complexity=self.complexity,
            generation=self.generation + 1,
            parent_ids=[self.program_id]
        )
    
    def evaluate(self, inputs: Dict[str, Any]) -> Any:
        """Evaluate the program."""
        if self.root:
            return self.root.evaluate(inputs)
        return None
    
    def calculate_complexity(self) -> float:
        """Calculate program complexity."""
        if not self.root:
            return 0.0
        self.complexity = self.root.size() + self.root.depth() * 0.5
        return self.complexity


# =============================================================================
# EVOLUTIONARY OPERATORS
# =============================================================================

class MutationOperator:
    """Mutation operators for program evolution."""
    
    def __init__(self, input_vars: List[str], constant_range: Tuple[float, float] = (-10, 10)):
        self.input_vars = input_vars
        self.constant_range = constant_range
    
    def mutate(self, program: Program, mutation_rate: float = 0.1) -> Program:
        """Apply mutation to a program."""
        new_prog = program.copy()
        if new_prog.root:
            self._mutate_node(new_prog.root, mutation_rate)
        return new_prog
    
    def _mutate_node(self, node: ProgramNode, rate: float):
        """Recursively mutate nodes."""
        if random.random() < rate:
            # Apply mutation
            mutation_type = random.choice(['change_op', 'change_value', 'grow', 'shrink'])
            
            if mutation_type == 'change_op' and node.node_type not in [ProgramNodeType.CONSTANT, ProgramNodeType.INPUT]:
                # Change operator
                similar_ops = self._get_similar_operators(node.node_type)
                if similar_ops:
                    node.node_type = random.choice(similar_ops)
            
            elif mutation_type == 'change_value':
                if node.node_type == ProgramNodeType.CONSTANT:
                    node.value = random.uniform(*self.constant_range)
                elif node.node_type == ProgramNodeType.INPUT:
                    node.value = random.choice(self.input_vars)
            
            elif mutation_type == 'grow' and len(node.children) < 3:
                # Add a child
                new_child = self._random_terminal()
                node.children.append(new_child)
            
            elif mutation_type == 'shrink' and node.children:
                # Remove a child
                node.children.pop(random.randrange(len(node.children)))
        
        # Recurse to children
        for child in node.children:
            self._mutate_node(child, rate)
    
    def _get_similar_operators(self, op: ProgramNodeType) -> List[ProgramNodeType]:
        """Get operators similar to the given one."""
        logical = [ProgramNodeType.AND, ProgramNodeType.OR, ProgramNodeType.NOT]
        arithmetic = [ProgramNodeType.PLUS, ProgramNodeType.MINUS, ProgramNodeType.TIMES, ProgramNodeType.DIVIDE]
        comparison = [ProgramNodeType.GREATER, ProgramNodeType.LESS, ProgramNodeType.EQUAL]
        
        if op in logical:
            return logical
        elif op in arithmetic:
            return arithmetic
        elif op in comparison:
            return comparison
        return []
    
    def _random_terminal(self) -> ProgramNode:
        """Create a random terminal node."""
        if random.random() < 0.5:
            return ProgramNode(
                node_type=ProgramNodeType.CONSTANT,
                value=random.uniform(*self.constant_range)
            )
        else:
            return ProgramNode(
                node_type=ProgramNodeType.INPUT,
                value=random.choice(self.input_vars)
            )


class CrossoverOperator:
    """Crossover operators for program evolution."""
    
    def crossover(self, parent1: Program, parent2: Program) -> Tuple[Program, Program]:
        """Perform crossover between two programs."""
        child1 = parent1.copy()
        child2 = parent2.copy()
        
        if child1.root and child2.root:
            # Select random subtrees
            nodes1 = self._collect_nodes(child1.root)
            nodes2 = self._collect_nodes(child2.root)
            
            if nodes1 and nodes2:
                # Select crossover points
                point1 = random.choice(nodes1)
                point2 = random.choice(nodes2)
                
                # Swap subtrees
                if point1['parent'] and point2['parent']:
                    idx1 = point1['index']
                    idx2 = point2['index']
                    
                    # Swap
                    temp = point1['parent'].children[idx1]
                    point1['parent'].children[idx1] = point2['parent'].children[idx2]
                    point2['parent'].children[idx2] = temp
        
        child1.parent_ids = [parent1.program_id, parent2.program_id]
        child2.parent_ids = [parent1.program_id, parent2.program_id]
        
        return child1, child2
    
    def _collect_nodes(self, node: ProgramNode, parent: ProgramNode = None, index: int = 0) -> List[Dict]:
        """Collect all nodes with their parent references."""
        result = [{'node': node, 'parent': parent, 'index': index}]
        for i, child in enumerate(node.children):
            result.extend(self._collect_nodes(child, node, i))
        return result


# =============================================================================
# DEME MANAGEMENT
# =============================================================================

@dataclass
class Deme:
    """
    A deme is a subpopulation of programs.
    
    MOSES uses multiple demes to maintain diversity and
    explore different regions of the program space.
    """
    deme_id: str = field(default_factory=lambda: f"deme_{random.randint(0, 9999):04d}")
    programs: List[Program] = field(default_factory=list)
    best_fitness: float = float('-inf')
    best_program: Optional[Program] = None
    generation: int = 0
    stagnation_count: int = 0
    created_at: float = field(default_factory=time.time)
    
    def add_program(self, program: Program):
        """Add a program to the deme."""
        self.programs.append(program)
        if program.fitness > self.best_fitness:
            self.best_fitness = program.fitness
            self.best_program = program
    
    def select_parents(self, n: int = 2, tournament_size: int = 3) -> List[Program]:
        """Select parents using tournament selection."""
        parents = []
        for _ in range(n):
            tournament = random.sample(self.programs, min(tournament_size, len(self.programs)))
            winner = max(tournament, key=lambda p: p.fitness)
            parents.append(winner)
        return parents
    
    def cull(self, keep_ratio: float = 0.5):
        """Remove low-fitness programs."""
        if len(self.programs) <= 2:
            return
        
        self.programs.sort(key=lambda p: p.fitness, reverse=True)
        keep_count = max(2, int(len(self.programs) * keep_ratio))
        self.programs = self.programs[:keep_count]


class DemeManager:
    """Manages multiple demes for diverse exploration."""
    
    def __init__(
        self,
        num_demes: int = 4,
        deme_size: int = 50,
        migration_rate: float = 0.1
    ):
        self.num_demes = num_demes
        self.deme_size = deme_size
        self.migration_rate = migration_rate
        
        self.demes: List[Deme] = []
        self._lock = threading.Lock()
    
    def initialize_demes(self, seed_programs: List[Program]):
        """Initialize demes with seed programs."""
        with self._lock:
            self.demes = [Deme() for _ in range(self.num_demes)]
            
            # Distribute seed programs
            for i, prog in enumerate(seed_programs):
                deme_idx = i % self.num_demes
                self.demes[deme_idx].add_program(prog)
    
    def migrate(self):
        """Migrate best programs between demes."""
        with self._lock:
            if len(self.demes) < 2:
                return
            
            # Collect best programs from each deme
            migrants = []
            for deme in self.demes:
                if deme.best_program and random.random() < self.migration_rate:
                    migrants.append(deme.best_program.copy())
            
            # Distribute migrants to other demes
            for migrant in migrants:
                target_deme = random.choice(self.demes)
                target_deme.add_program(migrant)
    
    def get_best_overall(self) -> Optional[Program]:
        """Get the best program across all demes."""
        best = None
        best_fitness = float('-inf')
        
        for deme in self.demes:
            if deme.best_program and deme.best_fitness > best_fitness:
                best = deme.best_program
                best_fitness = deme.best_fitness
        
        return best
    
    def get_deme(self, deme_id: str) -> Optional[Deme]:
        """Get a deme by ID."""
        for deme in self.demes:
            if deme.deme_id == deme_id:
                return deme
        return None


# =============================================================================
# FITNESS EVALUATION
# =============================================================================

class FitnessEvaluator:
    """Evaluates program fitness."""
    
    def __init__(
        self,
        fitness_fn: Callable[[Program, List[Dict[str, Any]]], float],
        test_cases: List[Dict[str, Any]],
        complexity_penalty: float = 0.01
    ):
        self.fitness_fn = fitness_fn
        self.test_cases = test_cases
        self.complexity_penalty = complexity_penalty
    
    def evaluate(self, program: Program) -> float:
        """Evaluate a program's fitness."""
        try:
            # Base fitness from fitness function
            base_fitness = self.fitness_fn(program, self.test_cases)
            
            # Apply complexity penalty
            program.calculate_complexity()
            penalty = self.complexity_penalty * program.complexity
            
            program.fitness = base_fitness - penalty
            return program.fitness
        except Exception as e:
            program.fitness = float('-inf')
            return program.fitness
    
    def evaluate_batch(self, programs: List[Program]) -> List[float]:
        """Evaluate multiple programs."""
        return [self.evaluate(p) for p in programs]


def accuracy_fitness(program: Program, test_cases: List[Dict[str, Any]]) -> float:
    """Fitness function based on accuracy."""
    if not test_cases:
        return 0.0
    
    correct = 0
    for case in test_cases:
        inputs = {k: v for k, v in case.items() if k != 'expected'}
        expected = case.get('expected')
        
        try:
            result = program.evaluate(inputs)
            if result == expected:
                correct += 1
            elif isinstance(expected, (int, float)) and isinstance(result, (int, float)):
                # Partial credit for close answers
                diff = abs(result - expected)
                if diff < 0.1:
                    correct += 0.9
                elif diff < 1.0:
                    correct += 0.5
        except:
            pass
    
    return correct / len(test_cases)


# =============================================================================
# MOSES LEARNING ENGINE
# =============================================================================

class MOSESEngine(LearningService):
    """
    MOSES-inspired program learning engine.
    
    This is the main learning service for the cognitive kernel,
    implementing evolutionary program synthesis.
    """
    
    def __init__(
        self,
        atomspace: AtomSpace,
        input_vars: List[str] = None,
        population_size: int = 100,
        num_demes: int = 4,
        max_generations: int = 100
    ):
        self.atomspace = atomspace
        self.input_vars = input_vars or ['x', 'y', 'z']
        self.population_size = population_size
        self.num_demes = num_demes
        self.max_generations = max_generations
        
        # Components
        self.mutation_op = MutationOperator(self.input_vars)
        self.crossover_op = CrossoverOperator()
        self.deme_manager = DemeManager(num_demes, population_size // num_demes)
        
        # Current learning task
        self._evaluator: Optional[FitnessEvaluator] = None
        self._current_generation = 0
        
        # Service state
        self._running = False
        self._learning_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        
        # Statistics
        self.stats = {
            'generations': 0,
            'programs_evaluated': 0,
            'best_fitness': float('-inf'),
            'learning_tasks': 0
        }
        
        # Callbacks
        self._on_generation_complete: List[Callable[[int, Program], None]] = []
        self._on_solution_found: List[Callable[[Program], None]] = []
    
    # =========================================================================
    # SERVICE INTERFACE
    # =========================================================================
    
    @property
    def service_name(self) -> str:
        return "moses_learning_engine"
    
    def start(self) -> bool:
        """Start the learning service."""
        if self._running:
            return False
        self._running = True
        return True
    
    def stop(self) -> bool:
        """Stop the learning service."""
        self._running = False
        if self._learning_thread:
            self._learning_thread.join(timeout=2.0)
        return True
    
    def status(self) -> Dict[str, Any]:
        """Get service status."""
        return {
            'running': self._running,
            'stats': self.stats.copy(),
            'current_generation': self._current_generation,
            'num_demes': len(self.deme_manager.demes)
        }
    
    # =========================================================================
    # LEARNING SERVICE INTERFACE
    # =========================================================================
    
    def learn_pattern(self, examples: List[Atom]) -> Optional[Atom]:
        """Learn a pattern from examples (simplified)."""
        # Convert atoms to test cases
        test_cases = self._atoms_to_test_cases(examples)
        if not test_cases:
            return None
        
        # Run learning
        best = self.learn(test_cases, max_generations=50)
        
        if best and best.fitness > 0.8:
            # Convert program to atom
            return self._program_to_atom(best)
        
        return None
    
    def reinforce(self, handle: AtomHandle, reward: float) -> bool:
        """Reinforce an atom based on reward."""
        atom = self.atomspace.get_atom(handle)
        if not atom:
            return False
        
        # Boost attention based on reward
        new_av = atom.attention_value.stimulate(reward * 0.1)
        self.atomspace.set_attention_value(handle, new_av)
        
        # Strengthen truth value
        if reward > 0:
            new_tv = TruthValue(
                strength=min(1.0, atom.truth_value.strength + reward * 0.1),
                confidence=min(1.0, atom.truth_value.confidence + 0.01),
                count=atom.truth_value.count + 1
            )
            self.atomspace.set_truth_value(handle, new_tv)
        
        return True
    
    # =========================================================================
    # LEARNING OPERATIONS
    # =========================================================================
    
    def learn(
        self,
        test_cases: List[Dict[str, Any]],
        fitness_fn: Callable[[Program, List[Dict[str, Any]]], float] = None,
        max_generations: int = None
    ) -> Optional[Program]:
        """
        Learn a program from test cases.
        """
        if fitness_fn is None:
            fitness_fn = accuracy_fitness
        
        if max_generations is None:
            max_generations = self.max_generations
        
        self.stats['learning_tasks'] += 1
        
        # Create evaluator
        self._evaluator = FitnessEvaluator(fitness_fn, test_cases)
        
        # Initialize population
        seed_programs = self._create_initial_population()
        self.deme_manager.initialize_demes(seed_programs)
        
        # Evaluate initial population
        for deme in self.deme_manager.demes:
            self._evaluator.evaluate_batch(deme.programs)
        
        # Evolution loop
        for gen in range(max_generations):
            self._current_generation = gen
            self.stats['generations'] += 1
            
            # Evolve each deme
            for deme in self.deme_manager.demes:
                self._evolve_deme(deme)
            
            # Migration
            if gen % 10 == 0:
                self.deme_manager.migrate()
            
            # Get best
            best = self.deme_manager.get_best_overall()
            if best:
                self.stats['best_fitness'] = max(self.stats['best_fitness'], best.fitness)
                
                # Notify callbacks
                self._notify_generation_complete(gen, best)
                
                # Check for solution
                if best.fitness >= 0.99:
                    self._notify_solution_found(best)
                    return best
        
        return self.deme_manager.get_best_overall()
    
    def _evolve_deme(self, deme: Deme):
        """Evolve a single deme for one generation."""
        new_programs = []
        
        # Elitism: keep best programs
        deme.programs.sort(key=lambda p: p.fitness, reverse=True)
        elite_count = max(1, len(deme.programs) // 10)
        new_programs.extend([p.copy() for p in deme.programs[:elite_count]])
        
        # Generate new programs
        while len(new_programs) < self.deme_manager.deme_size:
            if random.random() < 0.7:
                # Crossover
                parents = deme.select_parents(2)
                if len(parents) >= 2:
                    child1, child2 = self.crossover_op.crossover(parents[0], parents[1])
                    new_programs.append(child1)
                    if len(new_programs) < self.deme_manager.deme_size:
                        new_programs.append(child2)
            else:
                # Mutation only
                parent = deme.select_parents(1)[0]
                child = self.mutation_op.mutate(parent)
                new_programs.append(child)
        
        # Evaluate new programs
        self._evaluator.evaluate_batch(new_programs)
        self.stats['programs_evaluated'] += len(new_programs)
        
        # Update deme
        deme.programs = new_programs
        deme.generation += 1
        
        # Update best
        for prog in new_programs:
            if prog.fitness > deme.best_fitness:
                deme.best_fitness = prog.fitness
                deme.best_program = prog
                deme.stagnation_count = 0
            else:
                deme.stagnation_count += 1
    
    def _create_initial_population(self) -> List[Program]:
        """Create initial random population."""
        programs = []
        
        for _ in range(self.population_size):
            prog = Program()
            prog.root = self._random_program(max_depth=4)
            programs.append(prog)
        
        return programs
    
    def _random_program(self, max_depth: int = 4, current_depth: int = 0) -> ProgramNode:
        """Generate a random program tree."""
        if current_depth >= max_depth or (current_depth > 0 and random.random() < 0.3):
            # Terminal
            return self.mutation_op._random_terminal()
        
        # Non-terminal
        ops = [
            (ProgramNodeType.AND, 2),
            (ProgramNodeType.OR, 2),
            (ProgramNodeType.NOT, 1),
            (ProgramNodeType.PLUS, 2),
            (ProgramNodeType.MINUS, 2),
            (ProgramNodeType.TIMES, 2),
            (ProgramNodeType.GREATER, 2),
            (ProgramNodeType.LESS, 2),
            (ProgramNodeType.IF, 3),
        ]
        
        op, arity = random.choice(ops)
        children = [self._random_program(max_depth, current_depth + 1) for _ in range(arity)]
        
        return ProgramNode(node_type=op, children=children)
    
    # =========================================================================
    # ATOMSPACE INTEGRATION
    # =========================================================================
    
    def _atoms_to_test_cases(self, atoms: List[Atom]) -> List[Dict[str, Any]]:
        """Convert atoms to test cases."""
        test_cases = []
        
        for atom in atoms:
            if isinstance(atom, Link) and atom.atom_type == AtomType.EVALUATION_LINK:
                # Extract input-output pairs from evaluation links
                case = {}
                # Simplified extraction
                test_cases.append(case)
        
        return test_cases
    
    def _program_to_atom(self, program: Program) -> Optional[Atom]:
        """Convert a learned program to an atom in the AtomSpace."""
        if not program.root:
            return None
        
        # Create schema node
        schema_name = f"LearnedSchema_{program.program_id}"
        schema_handle = self.atomspace.add_node(
            AtomType.GROUNDED_SCHEMA_NODE,
            schema_name,
            tv=TruthValue(program.fitness, 0.8),
            av=AttentionValue(sti=0.5, lti=0.7)
        )
        
        # Store program representation in metadata
        schema = self.atomspace.get_atom(schema_handle)
        if schema:
            schema.metadata['program'] = program.root.to_string()
            schema.metadata['fitness'] = program.fitness
            schema.metadata['complexity'] = program.complexity
        
        return schema
    
    def load_program_from_atom(self, handle: AtomHandle) -> Optional[Program]:
        """Load a program from an atom."""
        atom = self.atomspace.get_atom(handle)
        if not atom or 'program' not in atom.metadata:
            return None
        
        # Would need a parser to reconstruct from string
        # Simplified: return None for now
        return None
    
    # =========================================================================
    # CALLBACKS
    # =========================================================================
    
    def on_generation_complete(self, callback: Callable[[int, Program], None]):
        """Register callback for generation completion."""
        self._on_generation_complete.append(callback)
    
    def on_solution_found(self, callback: Callable[[Program], None]):
        """Register callback for solution found."""
        self._on_solution_found.append(callback)
    
    def _notify_generation_complete(self, generation: int, best: Program):
        """Notify callbacks of generation completion."""
        for callback in self._on_generation_complete:
            try:
                callback(generation, best)
            except:
                pass
    
    def _notify_solution_found(self, program: Program):
        """Notify callbacks of solution found."""
        for callback in self._on_solution_found:
            try:
                callback(program)
            except:
                pass


# =============================================================================
# HEBBIAN LEARNING
# =============================================================================

class HebbianLearner:
    """
    Implements Hebbian learning for association strengthening.
    
    "Neurons that fire together wire together."
    """
    
    def __init__(self, atomspace: AtomSpace, learning_rate: float = 0.1):
        self.atomspace = atomspace
        self.learning_rate = learning_rate
    
    def learn_association(
        self,
        atom1: AtomHandle,
        atom2: AtomHandle,
        strength: float = 1.0
    ):
        """Strengthen association between two atoms."""
        # Find or create Hebbian link
        existing = self.atomspace.match_pattern(
            AtomType.HEBBIAN_LINK,
            [atom1, atom2]
        )
        
        if existing:
            # Strengthen existing link
            link = existing[0]
            new_strength = min(1.0, link.truth_value.strength + self.learning_rate * strength)
            new_tv = TruthValue(new_strength, link.truth_value.confidence, link.truth_value.count + 1)
            self.atomspace.set_truth_value(link.handle, new_tv)
        else:
            # Create new link
            tv = TruthValue(self.learning_rate * strength, 0.5, 1)
            self.atomspace.add_link(AtomType.HEBBIAN_LINK, [atom1, atom2], tv=tv)
    
    def decay_associations(self, decay_rate: float = 0.99):
        """Apply decay to all Hebbian links."""
        for link in self.atomspace.get_atoms_by_type(AtomType.HEBBIAN_LINK):
            new_strength = link.truth_value.strength * decay_rate
            if new_strength < 0.01:
                # Remove very weak links
                self.atomspace.remove_atom(link.handle)
            else:
                new_tv = TruthValue(new_strength, link.truth_value.confidence, link.truth_value.count)
                self.atomspace.set_truth_value(link.handle, new_tv)


# Export
__all__ = [
    'ProgramNodeType',
    'ProgramNode',
    'Program',
    'MutationOperator',
    'CrossoverOperator',
    'Deme',
    'DemeManager',
    'FitnessEvaluator',
    'accuracy_fitness',
    'MOSESEngine',
    'HebbianLearner',
]
