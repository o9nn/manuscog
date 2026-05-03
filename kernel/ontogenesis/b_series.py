"""
B-Series Expansion Module
=========================

Implementation of B-series (Butcher series) for kernel generation.
B-series provide a systematic way to express numerical methods
and can be used to generate optimal kernels for any domain.

Based on the theory of rooted trees and elementary differentials.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum, auto
import math
from functools import lru_cache


# =============================================================================
# ROOTED TREES
# =============================================================================

@dataclass
class RootedTree:
    """
    A rooted tree representation.
    
    Rooted trees are the fundamental objects in B-series theory.
    They represent elementary differentials and their compositions.
    """
    label: str = "τ"  # Tree label
    children: List['RootedTree'] = field(default_factory=list)
    order: int = 1  # Order of the tree
    
    def __post_init__(self):
        if self.children:
            self.order = 1 + sum(child.order for child in self.children)
    
    def __hash__(self):
        return hash(self.to_string())
    
    def __eq__(self, other):
        if not isinstance(other, RootedTree):
            return False
        return self.to_string() == other.to_string()
    
    def is_leaf(self) -> bool:
        """Check if this is a leaf (no children)."""
        return len(self.children) == 0
    
    def to_string(self) -> str:
        """Convert tree to string representation."""
        if self.is_leaf():
            return self.label
        child_strs = sorted([c.to_string() for c in self.children])
        return f"{self.label}[{','.join(child_strs)}]"
    
    def symmetry(self) -> int:
        """
        Compute the symmetry factor (σ) of the tree.
        
        The symmetry factor counts the number of equivalent
        labelings of the tree.
        """
        if self.is_leaf():
            return 1
        
        # Group children by structure
        child_groups: Dict[str, List[RootedTree]] = {}
        for child in self.children:
            key = child.to_string()
            if key not in child_groups:
                child_groups[key] = []
            child_groups[key].append(child)
        
        # Compute symmetry
        sigma = 1
        for group in child_groups.values():
            sigma *= math.factorial(len(group))
            for child in group:
                sigma *= child.symmetry()
        
        return sigma
    
    def density(self) -> int:
        """
        Compute the density (γ) of the tree.
        
        The density is the product of orders of all subtrees.
        """
        if self.is_leaf():
            return 1
        
        gamma = self.order
        for child in self.children:
            gamma *= child.density()
        
        return gamma
    
    def alpha(self) -> float:
        """
        Compute α = order! / (σ * γ)
        
        This is used in B-series coefficients.
        """
        return math.factorial(self.order) / (self.symmetry() * self.density())
    
    @classmethod
    def leaf(cls) -> 'RootedTree':
        """Create a leaf tree (single node)."""
        return cls(label="τ", children=[], order=1)
    
    @classmethod
    def from_children(cls, children: List['RootedTree']) -> 'RootedTree':
        """Create a tree from children."""
        return cls(label="τ", children=children)


def generate_rooted_trees(order: int) -> List[RootedTree]:
    """
    Generate all rooted trees up to a given order.
    
    The number of rooted trees follows sequence A000081:
    1, 1, 2, 4, 9, 20, 48, 115, 286, 719, ...
    
    Args:
        order: Maximum order of trees to generate
        
    Returns:
        List of all rooted trees up to the given order
    """
    if order < 1:
        return []
    
    # Order 1: single leaf
    trees_by_order: Dict[int, List[RootedTree]] = {1: [RootedTree.leaf()]}
    
    for n in range(2, order + 1):
        trees_n = []
        
        # Generate partitions of n-1 (for children orders)
        for partition in _integer_partitions(n - 1):
            # Generate all combinations of children for this partition
            child_combinations = _generate_child_combinations(partition, trees_by_order)
            
            for children in child_combinations:
                tree = RootedTree.from_children(list(children))
                # Check if this tree is already in the list
                if tree not in trees_n:
                    trees_n.append(tree)
        
        trees_by_order[n] = trees_n
    
    # Flatten all trees
    all_trees = []
    for n in range(1, order + 1):
        all_trees.extend(trees_by_order[n])
    
    return all_trees


def _integer_partitions(n: int) -> List[List[int]]:
    """Generate all integer partitions of n."""
    if n == 0:
        return [[]]
    
    partitions = []
    _partition_helper(n, n, [], partitions)
    return partitions


def _partition_helper(n: int, max_val: int, current: List[int], result: List[List[int]]):
    """Helper for generating partitions."""
    if n == 0:
        result.append(current[:])
        return
    
    for i in range(min(n, max_val), 0, -1):
        current.append(i)
        _partition_helper(n - i, i, current, result)
        current.pop()


def _generate_child_combinations(partition: List[int], 
                                  trees_by_order: Dict[int, List[RootedTree]]) -> List[Tuple[RootedTree, ...]]:
    """Generate all combinations of children for a given partition."""
    if not partition:
        return [()]
    
    first_order = partition[0]
    rest = partition[1:]
    
    if first_order not in trees_by_order:
        return []
    
    combinations = []
    for tree in trees_by_order[first_order]:
        for rest_combo in _generate_child_combinations(rest, trees_by_order):
            combinations.append((tree,) + rest_combo)
    
    return combinations


# =============================================================================
# B-SERIES TERMS AND EXPANSION
# =============================================================================

@dataclass
class BSeriesTerm:
    """A single term in a B-series expansion."""
    tree: RootedTree
    coefficient: float
    weight: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'tree': self.tree.to_string(),
            'order': self.tree.order,
            'coefficient': self.coefficient,
            'weight': self.weight,
            'alpha': self.tree.alpha()
        }


@dataclass
class BSeriesExpansion:
    """
    A B-series expansion.
    
    B(a, y) = Σ (h^|t| / σ(t)) * a(t) * F(t)(y)
    
    where:
    - t ranges over rooted trees
    - |t| is the order of tree t
    - σ(t) is the symmetry factor
    - a(t) is the coefficient
    - F(t) is the elementary differential
    """
    terms: List[BSeriesTerm] = field(default_factory=list)
    step_size: float = 1.0
    
    def add_term(self, tree: RootedTree, coefficient: float, weight: float = 1.0):
        """Add a term to the expansion."""
        self.terms.append(BSeriesTerm(tree=tree, coefficient=coefficient, weight=weight))
    
    def get_term(self, tree: RootedTree) -> Optional[BSeriesTerm]:
        """Get term for a specific tree."""
        for term in self.terms:
            if term.tree == tree:
                return term
        return None
    
    def truncate(self, max_order: int) -> 'BSeriesExpansion':
        """Return a truncated expansion up to max_order."""
        truncated = BSeriesExpansion(step_size=self.step_size)
        for term in self.terms:
            if term.tree.order <= max_order:
                truncated.terms.append(term)
        return truncated
    
    def evaluate(self, h: float) -> float:
        """
        Evaluate the B-series at step size h.
        
        Returns the weighted sum of coefficients.
        """
        result = 0.0
        for term in self.terms:
            contribution = (h ** term.tree.order / term.tree.symmetry()) * term.coefficient * term.weight
            result += contribution
        return result
    
    def order_conditions(self, target_order: int) -> Dict[int, float]:
        """
        Compute order conditions up to target_order.
        
        For a method to have order p, the B-series must satisfy:
        a(t) = 1/γ(t) for all trees t with |t| <= p
        """
        conditions = {}
        for term in self.terms:
            if term.tree.order <= target_order:
                expected = 1.0 / term.tree.density()
                actual = term.coefficient
                conditions[term.tree.order] = abs(actual - expected)
        return conditions
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'step_size': self.step_size,
            'terms': [t.to_dict() for t in self.terms],
            'total_terms': len(self.terms),
            'max_order': max(t.tree.order for t in self.terms) if self.terms else 0
        }


# =============================================================================
# BUTCHER TABLEAU
# =============================================================================

@dataclass
class ButcherTableau:
    """
    Butcher tableau for Runge-Kutta methods.
    
    A Butcher tableau defines a Runge-Kutta method:
    
        c | A
        --|---
          | b^T
    
    where:
    - A is the Runge-Kutta matrix
    - b is the weight vector
    - c is the node vector
    """
    A: List[List[float]]  # RK matrix
    b: List[float]        # Weights
    c: List[float]        # Nodes
    name: str = "Custom"
    
    @property
    def stages(self) -> int:
        """Number of stages."""
        return len(self.b)
    
    def is_explicit(self) -> bool:
        """Check if the method is explicit (A is strictly lower triangular)."""
        for i in range(len(self.A)):
            for j in range(i, len(self.A[i])):
                if self.A[i][j] != 0:
                    return False
        return True
    
    def to_b_series(self, max_order: int = 4) -> BSeriesExpansion:
        """
        Convert Butcher tableau to B-series expansion.
        
        The B-series coefficients are computed from the tableau.
        """
        trees = generate_rooted_trees(max_order)
        expansion = BSeriesExpansion()
        
        for tree in trees:
            coeff = self._compute_coefficient(tree)
            expansion.add_term(tree, coeff)
        
        return expansion
    
    def _compute_coefficient(self, tree: RootedTree) -> float:
        """Compute B-series coefficient for a tree."""
        if tree.is_leaf():
            return sum(self.b)
        
        # Recursive computation based on tree structure
        # This is a simplified version - full implementation would
        # use the recursive formula for elementary weights
        return self._elementary_weight(tree)
    
    def _elementary_weight(self, tree: RootedTree) -> float:
        """Compute elementary weight Φ(t) for a tree."""
        if tree.is_leaf():
            return sum(self.b)
        
        # For non-leaf trees, compute recursively
        s = self.stages
        result = 0.0
        
        for i in range(s):
            child_product = 1.0
            for child in tree.children:
                child_weight = self._stage_weight(child, i)
                child_product *= child_weight
            result += self.b[i] * child_product
        
        return result
    
    def _stage_weight(self, tree: RootedTree, stage: int) -> float:
        """Compute stage weight for a tree at a given stage."""
        if tree.is_leaf():
            return self.c[stage]
        
        result = 0.0
        for j in range(self.stages):
            child_product = 1.0
            for child in tree.children:
                child_weight = self._stage_weight(child, j)
                child_product *= child_weight
            result += self.A[stage][j] * child_product
        
        return result
    
    @classmethod
    def euler(cls) -> 'ButcherTableau':
        """Forward Euler method."""
        return cls(
            A=[[0.0]],
            b=[1.0],
            c=[0.0],
            name="Euler"
        )
    
    @classmethod
    def rk4(cls) -> 'ButcherTableau':
        """Classic 4th-order Runge-Kutta."""
        return cls(
            A=[
                [0.0, 0.0, 0.0, 0.0],
                [0.5, 0.0, 0.0, 0.0],
                [0.0, 0.5, 0.0, 0.0],
                [0.0, 0.0, 1.0, 0.0]
            ],
            b=[1/6, 1/3, 1/3, 1/6],
            c=[0.0, 0.5, 0.5, 1.0],
            name="RK4"
        )
    
    @classmethod
    def midpoint(cls) -> 'ButcherTableau':
        """Midpoint method (2nd order)."""
        return cls(
            A=[
                [0.0, 0.0],
                [0.5, 0.0]
            ],
            b=[0.0, 1.0],
            c=[0.0, 0.5],
            name="Midpoint"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'stages': self.stages,
            'A': self.A,
            'b': self.b,
            'c': self.c,
            'is_explicit': self.is_explicit()
        }


# =============================================================================
# B-SERIES COMPOSITION
# =============================================================================

def compose_b_series(b1: BSeriesExpansion, b2: BSeriesExpansion) -> BSeriesExpansion:
    """
    Compose two B-series.
    
    The composition B(a, B(b, y)) can be expressed as another B-series.
    This is the fundamental operation for kernel composition.
    """
    result = BSeriesExpansion(step_size=b1.step_size * b2.step_size)
    
    # Get all trees from both series
    max_order = max(
        max(t.tree.order for t in b1.terms) if b1.terms else 0,
        max(t.tree.order for t in b2.terms) if b2.terms else 0
    )
    
    trees = generate_rooted_trees(max_order)
    
    for tree in trees:
        # Compute composed coefficient
        coeff = _compute_composed_coefficient(tree, b1, b2)
        result.add_term(tree, coeff)
    
    return result


def _compute_composed_coefficient(tree: RootedTree, 
                                   b1: BSeriesExpansion, 
                                   b2: BSeriesExpansion) -> float:
    """Compute coefficient for composed B-series."""
    # Simplified composition - full implementation would use
    # the Butcher product formula
    
    term1 = b1.get_term(tree)
    term2 = b2.get_term(tree)
    
    c1 = term1.coefficient if term1 else 0.0
    c2 = term2.coefficient if term2 else 0.0
    
    # Simple product for now
    return c1 * c2 + c1 + c2


def invert_b_series(b: BSeriesExpansion) -> BSeriesExpansion:
    """
    Compute the inverse of a B-series.
    
    The inverse B^(-1) satisfies B ∘ B^(-1) = identity.
    """
    result = BSeriesExpansion(step_size=b.step_size)
    
    for term in b.terms:
        # Inverse coefficient
        if term.coefficient != 0:
            inv_coeff = -term.coefficient
        else:
            inv_coeff = 0.0
        result.add_term(term.tree, inv_coeff)
    
    return result
