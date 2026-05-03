"""
OpenCog Inferno AGI - Pattern Matching Engine
=============================================

The pattern matcher provides query capabilities over the AtomSpace,
supporting:
- Variable binding and unification
- Pattern-based atom retrieval
- Constraint satisfaction
- Graph pattern matching

This is essential for both reasoning (finding inference premises)
and learning (finding patterns in data).
"""

from __future__ import annotations
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from typing import Dict, List, Optional, Set, Tuple, Any, Callable, Iterator
from dataclasses import dataclass, field
from enum import Enum, auto
import threading
import time
from collections import defaultdict

from kernel.cognitive.types import (
    Atom, Node, Link, AtomHandle, AtomType,
    TruthValue, AttentionValue, Pattern, BindingSet
)
from atomspace.hypergraph.atomspace import AtomSpace


# =============================================================================
# PATTERN TYPES
# =============================================================================

class VariableNode(Node):
    """
    A variable node for pattern matching.
    Variables can be bound to any atom during matching.
    """
    
    def __init__(
        self,
        name: str,
        type_constraint: Optional[AtomType] = None,
        value_constraint: Optional[Callable[[Atom], bool]] = None
    ):
        super().__init__(
            atom_type=AtomType.VARIABLE_NODE,
            name=name
        )
        self.type_constraint = type_constraint
        self.value_constraint = value_constraint
    
    def matches(self, atom: Atom) -> bool:
        """Check if an atom can bind to this variable."""
        if self.type_constraint and atom.atom_type != self.type_constraint:
            return False
        if self.value_constraint and not self.value_constraint(atom):
            return False
        return True


@dataclass
class PatternLink:
    """
    A pattern link that can contain variables.
    """
    atom_type: AtomType
    outgoing: List[Any]  # Can be AtomHandle, VariableNode, or nested PatternLink
    type_constraint: Optional[AtomType] = None
    truth_constraint: Optional[Callable[[TruthValue], bool]] = None
    
    def get_variables(self) -> List[VariableNode]:
        """Get all variables in this pattern."""
        variables = []
        for item in self.outgoing:
            if isinstance(item, VariableNode):
                variables.append(item)
            elif isinstance(item, PatternLink):
                variables.extend(item.get_variables())
        return variables


@dataclass
class QueryPattern:
    """
    A complete query pattern with variables and constraints.
    """
    root: PatternLink
    variables: Dict[str, VariableNode] = field(default_factory=dict)
    constraints: List[Callable[[Dict[str, Atom]], bool]] = field(default_factory=list)
    
    @classmethod
    def create(cls, pattern_link: PatternLink) -> 'QueryPattern':
        """Create a query pattern from a pattern link."""
        variables = {}
        for var in pattern_link.get_variables():
            variables[var.name] = var
        return cls(root=pattern_link, variables=variables)
    
    def add_constraint(self, constraint: Callable[[Dict[str, Atom]], bool]):
        """Add a constraint on variable bindings."""
        self.constraints.append(constraint)


@dataclass
class MatchResult:
    """Result of a pattern match."""
    bindings: Dict[str, Atom]
    matched_atoms: List[Atom]
    confidence: float = 1.0
    
    def get_binding(self, var_name: str) -> Optional[Atom]:
        """Get the binding for a variable."""
        return self.bindings.get(var_name)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'bindings': {k: v.handle.uuid for k, v in self.bindings.items()},
            'matched_count': len(self.matched_atoms),
            'confidence': self.confidence
        }


# =============================================================================
# UNIFICATION ENGINE
# =============================================================================

class UnificationEngine:
    """
    Implements unification for pattern matching.
    
    Unification finds substitutions that make two terms identical.
    """
    
    def __init__(self, atomspace: AtomSpace):
        self.atomspace = atomspace
    
    def unify(
        self,
        pattern: Any,
        atom: Atom,
        bindings: Dict[str, Atom] = None
    ) -> Optional[Dict[str, Atom]]:
        """
        Attempt to unify a pattern with an atom.
        
        Returns bindings if successful, None otherwise.
        """
        if bindings is None:
            bindings = {}
        
        # Variable case
        if isinstance(pattern, VariableNode):
            return self._unify_variable(pattern, atom, bindings)
        
        # Handle case (concrete atom reference)
        if isinstance(pattern, AtomHandle):
            pattern_atom = self.atomspace.get_atom(pattern)
            if pattern_atom and self._atoms_equal(pattern_atom, atom):
                return bindings
            return None
        
        # Pattern link case
        if isinstance(pattern, PatternLink):
            return self._unify_pattern_link(pattern, atom, bindings)
        
        # Direct atom comparison
        if isinstance(pattern, Atom):
            if self._atoms_equal(pattern, atom):
                return bindings
            return None
        
        return None
    
    def _unify_variable(
        self,
        var: VariableNode,
        atom: Atom,
        bindings: Dict[str, Atom]
    ) -> Optional[Dict[str, Atom]]:
        """Unify a variable with an atom."""
        # Check if variable is already bound
        if var.name in bindings:
            existing = bindings[var.name]
            if self._atoms_equal(existing, atom):
                return bindings
            return None
        
        # Check variable constraints
        if not var.matches(atom):
            return None
        
        # Create new binding
        new_bindings = bindings.copy()
        new_bindings[var.name] = atom
        return new_bindings
    
    def _unify_pattern_link(
        self,
        pattern: PatternLink,
        atom: Atom,
        bindings: Dict[str, Atom]
    ) -> Optional[Dict[str, Atom]]:
        """Unify a pattern link with an atom."""
        # Must be a link
        if not isinstance(atom, Link):
            return None
        
        # Check type
        if pattern.atom_type != atom.atom_type:
            return None
        
        # Check arity
        if len(pattern.outgoing) != len(atom.outgoing):
            return None
        
        # Check truth constraint
        if pattern.truth_constraint and not pattern.truth_constraint(atom.truth_value):
            return None
        
        # Unify each outgoing element
        current_bindings = bindings.copy()
        for pattern_elem, atom_handle in zip(pattern.outgoing, atom.outgoing):
            target_atom = self.atomspace.get_atom(atom_handle)
            if not target_atom:
                return None
            
            result = self.unify(pattern_elem, target_atom, current_bindings)
            if result is None:
                return None
            current_bindings = result
        
        return current_bindings
    
    def _atoms_equal(self, atom1: Atom, atom2: Atom) -> bool:
        """Check if two atoms are equal."""
        if atom1.handle == atom2.handle:
            return True
        
        if atom1.atom_type != atom2.atom_type:
            return False
        
        if isinstance(atom1, Node) and isinstance(atom2, Node):
            return atom1.name == atom2.name
        
        if isinstance(atom1, Link) and isinstance(atom2, Link):
            if len(atom1.outgoing) != len(atom2.outgoing):
                return False
            return all(h1 == h2 for h1, h2 in zip(atom1.outgoing, atom2.outgoing))
        
        return False


# =============================================================================
# PATTERN MATCHER
# =============================================================================

class PatternMatcher:
    """
    Main pattern matching engine for the AtomSpace.
    
    Supports:
    - Variable binding
    - Type constraints
    - Value constraints
    - Recursive pattern matching
    """
    
    def __init__(self, atomspace: AtomSpace):
        self.atomspace = atomspace
        self.unifier = UnificationEngine(atomspace)
        
        # Statistics
        self.stats = {
            'queries': 0,
            'matches_found': 0,
            'atoms_examined': 0
        }
    
    def match(
        self,
        pattern: QueryPattern,
        limit: int = 100
    ) -> List[MatchResult]:
        """
        Find all matches for a pattern in the AtomSpace.
        """
        self.stats['queries'] += 1
        results = []
        
        # Get candidate atoms based on pattern type
        candidates = self._get_candidates(pattern.root)
        
        for atom in candidates:
            self.stats['atoms_examined'] += 1
            
            # Attempt unification
            bindings = self.unifier.unify(pattern.root, atom, {})
            
            if bindings is not None:
                # Check additional constraints
                if self._check_constraints(bindings, pattern.constraints):
                    # Convert handle bindings to atoms
                    atom_bindings = {}
                    for var_name, bound_atom in bindings.items():
                        atom_bindings[var_name] = bound_atom
                    
                    result = MatchResult(
                        bindings=atom_bindings,
                        matched_atoms=[atom],
                        confidence=atom.truth_value.confidence
                    )
                    results.append(result)
                    self.stats['matches_found'] += 1
                    
                    if len(results) >= limit:
                        break
        
        return results
    
    def match_pattern_link(
        self,
        atom_type: AtomType,
        outgoing_pattern: List[Optional[AtomHandle]] = None,
        limit: int = 100
    ) -> List[Link]:
        """
        Simple pattern matching for links.
        None in outgoing_pattern matches any atom.
        """
        self.stats['queries'] += 1
        results = []
        
        for link in self.atomspace.get_atoms_by_type(atom_type):
            if not isinstance(link, Link):
                continue
            
            self.stats['atoms_examined'] += 1
            
            if outgoing_pattern is None:
                results.append(link)
            elif len(link.outgoing) == len(outgoing_pattern):
                match = True
                for i, pattern_handle in enumerate(outgoing_pattern):
                    if pattern_handle is not None and link.outgoing[i] != pattern_handle:
                        match = False
                        break
                if match:
                    results.append(link)
            
            if len(results) >= limit:
                break
        
        self.stats['matches_found'] += len(results)
        return results
    
    def find_by_predicate(
        self,
        predicate_name: str,
        argument_patterns: List[Optional[AtomHandle]] = None,
        limit: int = 100
    ) -> List[Tuple[Link, List[Atom]]]:
        """
        Find evaluation links with a specific predicate.
        """
        self.stats['queries'] += 1
        results = []
        
        # Find the predicate node
        predicate = self.atomspace.get_node(AtomType.PREDICATE_NODE, predicate_name)
        if not predicate:
            return results
        
        # Find evaluation links with this predicate
        for link in self.atomspace.get_incoming(predicate.handle):
            if link.atom_type != AtomType.EVALUATION_LINK:
                continue
            
            if len(link.outgoing) < 2:
                continue
            
            # Get the argument list
            list_handle = link.outgoing[1]
            list_link = self.atomspace.get_atom(list_handle)
            
            if not isinstance(list_link, Link):
                continue
            
            # Check argument patterns
            if argument_patterns is not None:
                if len(list_link.outgoing) != len(argument_patterns):
                    continue
                
                match = True
                for i, pattern in enumerate(argument_patterns):
                    if pattern is not None and list_link.outgoing[i] != pattern:
                        match = False
                        break
                
                if not match:
                    continue
            
            # Get argument atoms
            arguments = [
                self.atomspace.get_atom(h) 
                for h in list_link.outgoing
            ]
            
            results.append((link, arguments))
            self.stats['matches_found'] += 1
            
            if len(results) >= limit:
                break
        
        return results
    
    def find_inheritance_chain(
        self,
        start: AtomHandle,
        end: AtomHandle,
        max_depth: int = 10
    ) -> Optional[List[Link]]:
        """
        Find an inheritance chain from start to end.
        """
        self.stats['queries'] += 1
        
        visited = set()
        queue = [(start, [])]
        
        while queue:
            current, path = queue.pop(0)
            
            if current == end:
                return path
            
            if current in visited or len(path) >= max_depth:
                continue
            
            visited.add(current)
            self.stats['atoms_examined'] += 1
            
            # Find inheritance links from current
            for link in self.atomspace.get_incoming(current):
                if link.atom_type == AtomType.INHERITANCE_LINK:
                    if len(link.outgoing) >= 2 and link.outgoing[0] == current:
                        next_handle = link.outgoing[1]
                        if next_handle not in visited:
                            queue.append((next_handle, path + [link]))
        
        return None
    
    def find_similar_atoms(
        self,
        atom: Atom,
        threshold: float = 0.5,
        limit: int = 10
    ) -> List[Tuple[Atom, float]]:
        """
        Find atoms similar to the given atom.
        """
        self.stats['queries'] += 1
        results = []
        
        # Find similarity links involving this atom
        for link in self.atomspace.get_incoming(atom.handle):
            if link.atom_type == AtomType.SIMILARITY_LINK:
                if link.truth_value.strength >= threshold:
                    # Get the other atom
                    for h in link.outgoing:
                        if h != atom.handle:
                            other = self.atomspace.get_atom(h)
                            if other:
                                results.append((other, link.truth_value.strength))
        
        # Sort by similarity
        results.sort(key=lambda x: -x[1])
        return results[:limit]
    
    def _get_candidates(self, pattern: PatternLink) -> List[Atom]:
        """Get candidate atoms for matching."""
        return self.atomspace.get_atoms_by_type(pattern.atom_type)
    
    def _check_constraints(
        self,
        bindings: Dict[str, Atom],
        constraints: List[Callable[[Dict[str, Atom]], bool]]
    ) -> bool:
        """Check if bindings satisfy all constraints."""
        for constraint in constraints:
            try:
                if not constraint(bindings):
                    return False
            except Exception:
                return False
        return True


# =============================================================================
# QUERY BUILDER
# =============================================================================

class QueryBuilder:
    """
    Fluent interface for building queries.
    """
    
    def __init__(self, atomspace: AtomSpace):
        self.atomspace = atomspace
        self._variables: Dict[str, VariableNode] = {}
        self._pattern: Optional[PatternLink] = None
        self._constraints: List[Callable[[Dict[str, Atom]], bool]] = []
    
    def var(
        self,
        name: str,
        type_constraint: Optional[AtomType] = None
    ) -> VariableNode:
        """Create or get a variable."""
        if name not in self._variables:
            self._variables[name] = VariableNode(name, type_constraint)
        return self._variables[name]
    
    def inheritance(
        self,
        child: Any,
        parent: Any
    ) -> 'QueryBuilder':
        """Set pattern to inheritance link."""
        self._pattern = PatternLink(
            atom_type=AtomType.INHERITANCE_LINK,
            outgoing=[child, parent]
        )
        return self
    
    def similarity(
        self,
        atom1: Any,
        atom2: Any
    ) -> 'QueryBuilder':
        """Set pattern to similarity link."""
        self._pattern = PatternLink(
            atom_type=AtomType.SIMILARITY_LINK,
            outgoing=[atom1, atom2]
        )
        return self
    
    def evaluation(
        self,
        predicate: Any,
        arguments: List[Any]
    ) -> 'QueryBuilder':
        """Set pattern to evaluation link."""
        list_pattern = PatternLink(
            atom_type=AtomType.LIST_LINK,
            outgoing=arguments
        )
        self._pattern = PatternLink(
            atom_type=AtomType.EVALUATION_LINK,
            outgoing=[predicate, list_pattern]
        )
        return self
    
    def where(
        self,
        constraint: Callable[[Dict[str, Atom]], bool]
    ) -> 'QueryBuilder':
        """Add a constraint."""
        self._constraints.append(constraint)
        return self
    
    def where_strength_gt(self, var_name: str, threshold: float) -> 'QueryBuilder':
        """Add constraint: variable's truth strength > threshold."""
        def constraint(bindings):
            atom = bindings.get(var_name)
            return atom and atom.truth_value.strength > threshold
        self._constraints.append(constraint)
        return self
    
    def where_confidence_gt(self, var_name: str, threshold: float) -> 'QueryBuilder':
        """Add constraint: variable's confidence > threshold."""
        def constraint(bindings):
            atom = bindings.get(var_name)
            return atom and atom.truth_value.confidence > threshold
        self._constraints.append(constraint)
        return self
    
    def build(self) -> QueryPattern:
        """Build the query pattern."""
        if not self._pattern:
            raise ValueError("No pattern specified")
        
        query = QueryPattern(
            root=self._pattern,
            variables=self._variables.copy(),
            constraints=self._constraints.copy()
        )
        return query
    
    def execute(self, limit: int = 100) -> List[MatchResult]:
        """Build and execute the query."""
        pattern = self.build()
        matcher = PatternMatcher(self.atomspace)
        return matcher.match(pattern, limit)


# =============================================================================
# GRAPH PATTERN MATCHING
# =============================================================================

class GraphPatternMatcher:
    """
    Advanced pattern matching for graph patterns.
    
    Supports matching complex subgraph patterns in the AtomSpace.
    """
    
    def __init__(self, atomspace: AtomSpace):
        self.atomspace = atomspace
        self.pattern_matcher = PatternMatcher(atomspace)
    
    def match_subgraph(
        self,
        pattern_atoms: List[Atom],
        pattern_links: List[PatternLink]
    ) -> List[Dict[str, Atom]]:
        """
        Match a subgraph pattern.
        
        pattern_atoms: List of atoms (or variables) in the pattern
        pattern_links: List of links connecting the atoms
        """
        if not pattern_links:
            return []
        
        # Start with the first link
        first_link = pattern_links[0]
        first_matches = self.pattern_matcher.match(
            QueryPattern.create(first_link)
        )
        
        if not first_matches:
            return []
        
        # Extend matches with remaining links
        results = [m.bindings for m in first_matches]
        
        for link_pattern in pattern_links[1:]:
            new_results = []
            
            for bindings in results:
                # Create query with existing bindings
                query = QueryPattern.create(link_pattern)
                
                # Try to extend this binding
                matches = self.pattern_matcher.match(query)
                
                for match in matches:
                    # Check consistency with existing bindings
                    consistent = True
                    merged = bindings.copy()
                    
                    for var_name, atom in match.bindings.items():
                        if var_name in merged:
                            if merged[var_name].handle != atom.handle:
                                consistent = False
                                break
                        else:
                            merged[var_name] = atom
                    
                    if consistent:
                        new_results.append(merged)
            
            results = new_results
            if not results:
                break
        
        return results
    
    def find_paths(
        self,
        start: AtomHandle,
        end: AtomHandle,
        link_types: List[AtomType] = None,
        max_length: int = 5
    ) -> List[List[Link]]:
        """
        Find all paths between two atoms.
        """
        if link_types is None:
            link_types = [AtomType.INHERITANCE_LINK, AtomType.SIMILARITY_LINK]
        
        paths = []
        visited = set()
        
        def dfs(current: AtomHandle, path: List[Link]):
            if current == end:
                paths.append(path.copy())
                return
            
            if len(path) >= max_length or current in visited:
                return
            
            visited.add(current)
            
            for link in self.atomspace.get_incoming(current):
                if link.atom_type not in link_types:
                    continue
                
                for next_handle in link.outgoing:
                    if next_handle != current:
                        path.append(link)
                        dfs(next_handle, path)
                        path.pop()
            
            visited.remove(current)
        
        dfs(start, [])
        return paths


# Export
__all__ = [
    'VariableNode',
    'PatternLink',
    'QueryPattern',
    'MatchResult',
    'UnificationEngine',
    'PatternMatcher',
    'QueryBuilder',
    'GraphPatternMatcher',
]
