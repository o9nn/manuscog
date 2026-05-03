"""
OpenCog Inferno AGI - Economic Attention Networks (ECAN)
========================================================

ECAN implements attention allocation as an economic system where:
- Atoms have "wealth" (attention value)
- Atoms pay "rent" to stay in memory
- Useful atoms earn "wages"
- Attention spreads through Hebbian links

This is a kernel-level service that manages cognitive resource
allocation, determining what the system "thinks about".
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
from collections import defaultdict
import heapq

from kernel.cognitive.types import (
    Atom, Node, Link, AtomHandle, AtomType,
    TruthValue, AttentionValue, AttentionService,
    CognitiveContext, LRUCache
)
from atomspace.hypergraph.atomspace import AtomSpace


# =============================================================================
# ECAN CONFIGURATION
# =============================================================================

@dataclass
class ECANConfig:
    """Configuration for the ECAN attention service."""
    attention_budget: float = 100.0
    focus_boundary: float = 0.5
    decay_rate: float = 0.99
    max_focus_size: int = 100


# =============================================================================
# ATTENTION ECONOMICS PARAMETERS
# =============================================================================

@dataclass
class ECANParameters:
    """
    Parameters controlling the attention economy.
    """
    # Attention fund parameters
    total_stimulus: float = 1000.0      # Total stimulus available per cycle
    stimulus_per_atom: float = 0.1      # Default stimulus per atom
    
    # Rent parameters
    rent_rate: float = 0.01             # Base rent rate per cycle
    rent_focus_multiplier: float = 2.0  # Extra rent for focus atoms
    
    # Wage parameters
    wage_rate: float = 0.1              # Base wage for useful atoms
    inference_wage: float = 0.5         # Wage for atoms used in inference
    
    # Spreading parameters
    spread_decay: float = 0.9           # Decay factor for spreading
    spread_threshold: float = 0.1       # Min STI to spread from
    max_spread_distance: int = 3        # Max hops for spreading
    hebbian_strength: float = 0.5       # Strength of Hebbian spreading
    
    # Focus parameters
    focus_boundary: float = 0.5         # STI threshold for attentional focus
    max_focus_size: int = 100           # Maximum atoms in focus
    
    # Decay parameters
    sti_decay_rate: float = 0.99        # STI decay per cycle
    lti_decay_rate: float = 0.999       # LTI decay per cycle
    
    # Importance parameters
    importance_update_rate: float = 0.1  # Rate of importance updates
    
    @classmethod
    def default(cls) -> 'ECANParameters':
        return cls()
    
    @classmethod
    def aggressive(cls) -> 'ECANParameters':
        """More aggressive forgetting and focusing."""
        return cls(
            rent_rate=0.05,
            sti_decay_rate=0.95,
            focus_boundary=0.6,
            max_focus_size=50
        )
    
    @classmethod
    def conservative(cls) -> 'ECANParameters':
        """More conservative, slower forgetting."""
        return cls(
            rent_rate=0.005,
            sti_decay_rate=0.995,
            focus_boundary=0.4,
            max_focus_size=200
        )


# =============================================================================
# ATTENTION BANK
# =============================================================================

class AttentionBank:
    """
    Manages the "economy" of attention.
    
    Tracks total attention in the system and manages
    stimulus/rent/wage transactions.
    """
    
    def __init__(self, params: ECANParameters):
        self.params = params
        
        # Attention funds
        self.stimulus_pool: float = params.total_stimulus
        self.rent_collected: float = 0.0
        self.wages_paid: float = 0.0
        
        # Tracking
        self.total_sti: float = 0.0
        self.total_lti: float = 0.0
        
        # Statistics
        self.stats = {
            'stimulus_distributed': 0.0,
            'rent_collected': 0.0,
            'wages_paid': 0.0,
            'cycles': 0
        }
        
        self._lock = threading.Lock()
    
    def distribute_stimulus(self, amount: float) -> float:
        """Distribute stimulus from the pool."""
        with self._lock:
            actual = min(amount, self.stimulus_pool)
            self.stimulus_pool -= actual
            self.stats['stimulus_distributed'] += actual
            return actual
    
    def collect_rent(self, amount: float):
        """Collect rent from atoms."""
        with self._lock:
            self.rent_collected += amount
            self.stats['rent_collected'] += amount
    
    def pay_wage(self, amount: float) -> float:
        """Pay wage to useful atoms."""
        with self._lock:
            # Wages come from rent collected
            actual = min(amount, self.rent_collected)
            self.rent_collected -= actual
            self.wages_paid += actual
            self.stats['wages_paid'] += actual
            return actual
    
    def cycle_reset(self):
        """Reset for new attention cycle."""
        with self._lock:
            # Recycle rent into stimulus pool
            self.stimulus_pool = min(
                self.params.total_stimulus,
                self.stimulus_pool + self.rent_collected * 0.5
            )
            self.rent_collected = 0.0
            self.wages_paid = 0.0
            self.stats['cycles'] += 1
    
    def update_totals(self, sti: float, lti: float):
        """Update total attention tracking."""
        with self._lock:
            self.total_sti = sti
            self.total_lti = lti
    
    def get_stats(self) -> Dict[str, Any]:
        """Get attention bank statistics."""
        with self._lock:
            return {
                **self.stats,
                'stimulus_pool': self.stimulus_pool,
                'rent_collected': self.rent_collected,
                'total_sti': self.total_sti,
                'total_lti': self.total_lti
            }


# =============================================================================
# HEBBIAN LINK MANAGER
# =============================================================================

class HebbianLinkManager:
    """
    Manages Hebbian links for attention spreading.
    
    Hebbian links represent "neurons that fire together wire together" -
    atoms that are co-activated become linked.
    """
    
    def __init__(self, atomspace: AtomSpace, params: ECANParameters):
        self.atomspace = atomspace
        self.params = params
        
        # Co-activation tracking
        self._coactivation_counts: Dict[Tuple[AtomHandle, AtomHandle], int] = defaultdict(int)
        self._activation_window: List[Set[AtomHandle]] = []
        self._window_size = 10
        
        self._lock = threading.Lock()
    
    def record_activation(self, handles: Set[AtomHandle]):
        """Record a set of co-activated atoms."""
        with self._lock:
            self._activation_window.append(handles)
            if len(self._activation_window) > self._window_size:
                self._activation_window.pop(0)
            
            # Update co-activation counts
            handles_list = list(handles)
            for i, h1 in enumerate(handles_list):
                for h2 in handles_list[i+1:]:
                    key = (min(h1.uuid, h2.uuid), max(h1.uuid, h2.uuid))
                    # Create proper tuple key
                    if h1.uuid < h2.uuid:
                        key = (h1, h2)
                    else:
                        key = (h2, h1)
                    self._coactivation_counts[key] += 1
    
    def update_hebbian_links(self, threshold: int = 3):
        """
        Create or strengthen Hebbian links based on co-activation.
        """
        with self._lock:
            for (h1, h2), count in list(self._coactivation_counts.items()):
                if count >= threshold:
                    # Check if Hebbian link exists
                    existing = self.atomspace.match_pattern(
                        AtomType.HEBBIAN_LINK,
                        [h1, h2]
                    )
                    
                    # Calculate strength based on co-activation
                    strength = min(1.0, count / (threshold * 2))
                    tv = TruthValue(strength, 0.8, count)
                    
                    if existing:
                        # Strengthen existing link
                        self.atomspace.merge_truth_value(existing[0].handle, tv)
                    else:
                        # Create new Hebbian link
                        self.atomspace.add_link(
                            AtomType.HEBBIAN_LINK,
                            [h1, h2],
                            tv=tv
                        )
                    
                    # Reset count
                    self._coactivation_counts[(h1, h2)] = 0
    
    def get_hebbian_neighbors(
        self,
        handle: AtomHandle,
        min_strength: float = 0.1
    ) -> List[Tuple[AtomHandle, float]]:
        """Get atoms connected via Hebbian links."""
        neighbors = []
        
        for link in self.atomspace.get_incoming(handle):
            if link.atom_type == AtomType.HEBBIAN_LINK:
                if link.truth_value.strength >= min_strength:
                    for h in link.outgoing:
                        if h != handle:
                            neighbors.append((h, link.truth_value.strength))
        
        return neighbors


# =============================================================================
# IMPORTANCE DIFFUSION
# =============================================================================

class ImportanceDiffusion:
    """
    Handles spreading of attention through the hypergraph.
    """
    
    def __init__(
        self,
        atomspace: AtomSpace,
        params: ECANParameters,
        hebbian_manager: HebbianLinkManager
    ):
        self.atomspace = atomspace
        self.params = params
        self.hebbian_manager = hebbian_manager
    
    def spread_importance(
        self,
        source: AtomHandle,
        amount: float,
        visited: Optional[Set[AtomHandle]] = None,
        depth: int = 0
    ) -> int:
        """
        Spread importance from a source atom.
        
        Returns number of atoms affected.
        """
        if visited is None:
            visited = set()
        
        if depth >= self.params.max_spread_distance:
            return 0
        
        if source in visited:
            return 0
        
        visited.add(source)
        
        source_atom = self.atomspace.get_atom(source)
        if not source_atom:
            return 0
        
        if source_atom.attention_value.sti < self.params.spread_threshold:
            return 0
        
        affected = 0
        spread_amount = amount * self.params.spread_decay
        
        # Spread through structural links
        for link in self.atomspace.get_incoming(source):
            link_weight = self._get_link_weight(link)
            
            for target in link.outgoing:
                if target != source and target not in visited:
                    target_amount = spread_amount * link_weight / len(link.outgoing)
                    if target_amount > 0.001:
                        self.atomspace.stimulate(target, target_amount)
                        affected += 1
                        affected += self.spread_importance(
                            target, target_amount, visited, depth + 1
                        )
        
        # Spread through Hebbian links
        hebbian_neighbors = self.hebbian_manager.get_hebbian_neighbors(source)
        for target, strength in hebbian_neighbors:
            if target not in visited:
                target_amount = spread_amount * strength * self.params.hebbian_strength
                if target_amount > 0.001:
                    self.atomspace.stimulate(target, target_amount)
                    affected += 1
        
        return affected
    
    def _get_link_weight(self, link: Link) -> float:
        """Get weight for spreading through a link."""
        # Weight based on link type and truth value
        base_weight = 1.0
        
        if link.atom_type == AtomType.INHERITANCE_LINK:
            base_weight = 0.8
        elif link.atom_type == AtomType.SIMILARITY_LINK:
            base_weight = 0.6
        elif link.atom_type == AtomType.IMPLICATION_LINK:
            base_weight = 0.7
        elif link.atom_type == AtomType.HEBBIAN_LINK:
            base_weight = self.params.hebbian_strength
        
        return base_weight * link.truth_value.strength


# =============================================================================
# ATTENTIONAL FOCUS
# =============================================================================

class AttentionalFocus:
    """
    Manages the attentional focus - the set of atoms currently
    being "thought about".
    """
    
    def __init__(self, atomspace: AtomSpace, params: ECANParameters):
        self.atomspace = atomspace
        self.params = params
        
        # Focus set
        self._focus: Set[AtomHandle] = set()
        self._focus_history: List[Set[AtomHandle]] = []
        self._history_size = 100
        
        # Priority queue for focus management
        self._priority_queue: List[Tuple[float, AtomHandle]] = []
        
        self._lock = threading.RLock()
    
    def update_focus(self) -> Set[AtomHandle]:
        """
        Update the attentional focus based on current STI values.
        """
        with self._lock:
            # Get top atoms by STI
            top_atoms = self.atomspace.get_top_attention(
                self.params.max_focus_size * 2
            )
            
            new_focus = set()
            for sti, atom in top_atoms:
                if sti >= self.params.focus_boundary:
                    new_focus.add(atom.handle)
                    if len(new_focus) >= self.params.max_focus_size:
                        break
            
            # Record history
            if self._focus != new_focus:
                self._focus_history.append(self._focus.copy())
                if len(self._focus_history) > self._history_size:
                    self._focus_history.pop(0)
            
            self._focus = new_focus
            return new_focus.copy()
    
    def get_focus(self) -> Set[AtomHandle]:
        """Get current attentional focus."""
        with self._lock:
            return self._focus.copy()
    
    def is_in_focus(self, handle: AtomHandle) -> bool:
        """Check if an atom is in focus."""
        with self._lock:
            return handle in self._focus
    
    def get_focus_atoms(self) -> List[Atom]:
        """Get atoms in focus."""
        with self._lock:
            atoms = []
            for handle in self._focus:
                atom = self.atomspace.get_atom(handle)
                if atom:
                    atoms.append(atom)
            return atoms
    
    def get_focus_history(self, n: int = 10) -> List[Set[AtomHandle]]:
        """Get recent focus history."""
        with self._lock:
            return self._focus_history[-n:]
    
    def force_focus(self, handle: AtomHandle):
        """Force an atom into focus."""
        with self._lock:
            atom = self.atomspace.get_atom(handle)
            if atom:
                # Boost STI to ensure focus
                new_sti = max(atom.attention_value.sti, self.params.focus_boundary + 0.1)
                new_av = AttentionValue(
                    sti=new_sti,
                    lti=atom.attention_value.lti,
                    vlti=atom.attention_value.vlti
                )
                self.atomspace.set_attention_value(handle, new_av)
                self._focus.add(handle)


# =============================================================================
# ECAN SERVICE
# =============================================================================

class ECANService(AttentionService):
    """
    Economic Attention Networks service.
    
    This is the main attention allocation service for the cognitive kernel.
    It implements attention as an economic system with stimulus, rent, and wages.
    """
    
    def __init__(
        self,
        atomspace: AtomSpace,
        params: Optional[ECANParameters] = None
    ):
        self.atomspace = atomspace
        self.params = params or ECANParameters.default()
        
        # Components
        self.bank = AttentionBank(self.params)
        self.hebbian_manager = HebbianLinkManager(atomspace, self.params)
        self.diffusion = ImportanceDiffusion(atomspace, self.params, self.hebbian_manager)
        self.focus = AttentionalFocus(atomspace, self.params)
        
        # Service state
        self._running = False
        self._attention_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        
        # Cycle timing
        self.cycle_interval = 0.1  # seconds
        
        # Statistics
        self.stats = {
            'cycles': 0,
            'atoms_stimulated': 0,
            'rent_events': 0,
            'wage_events': 0,
            'spread_events': 0
        }
        
        # Callbacks
        self._on_focus_change: List[Callable[[Set[AtomHandle]], None]] = []
    
    # =========================================================================
    # SERVICE INTERFACE
    # =========================================================================
    
    @property
    def service_name(self) -> str:
        return "ecan_attention_service"
    
    def start(self) -> bool:
        """Start the attention service."""
        if self._running:
            return False
        
        self._running = True
        self._attention_thread = threading.Thread(
            target=self._attention_loop,
            daemon=True,
            name="ecan-attention"
        )
        self._attention_thread.start()
        return True
    
    def stop(self) -> bool:
        """Stop the attention service."""
        if not self._running:
            return False
        
        self._running = False
        if self._attention_thread:
            self._attention_thread.join(timeout=2.0)
        return True
    
    def status(self) -> Dict[str, Any]:
        """Get service status."""
        return {
            'running': self._running,
            'stats': self.stats.copy(),
            'bank_stats': self.bank.get_stats(),
            'focus_size': len(self.focus.get_focus()),
            'params': {
                'focus_boundary': self.params.focus_boundary,
                'max_focus_size': self.params.max_focus_size,
                'sti_decay_rate': self.params.sti_decay_rate
            }
        }
    
    # =========================================================================
    # ATTENTION SERVICE INTERFACE
    # =========================================================================
    
    def get_attentional_focus(self) -> Set[AtomHandle]:
        """Get atoms currently in attentional focus."""
        return self.focus.get_focus()
    
    def stimulate(self, handle: AtomHandle, amount: float) -> bool:
        """Stimulate an atom's attention."""
        # Get stimulus from bank
        actual = self.bank.distribute_stimulus(amount)
        if actual <= 0:
            return False
        
        result = self.atomspace.stimulate(handle, actual)
        if result:
            self.stats['atoms_stimulated'] += 1
        return result
    
    def spread_attention(self) -> int:
        """Spread attention through the hypergraph."""
        focus_atoms = self.focus.get_focus()
        total_affected = 0
        
        for handle in focus_atoms:
            atom = self.atomspace.get_atom(handle)
            if atom:
                spread_amount = atom.attention_value.sti * 0.1
                affected = self.diffusion.spread_importance(handle, spread_amount)
                total_affected += affected
        
        self.stats['spread_events'] += 1
        return total_affected
    
    # =========================================================================
    # ATTENTION CYCLE
    # =========================================================================
    
    def run_cycle(self):
        """Run one attention cycle."""
        with self._lock:
            # 1. Collect rent from all atoms
            self._collect_rent()
            
            # 2. Apply attention decay
            self._apply_decay()
            
            # 3. Spread attention from focus
            self.spread_attention()
            
            # 4. Update Hebbian links
            self._update_hebbian()
            
            # 5. Update attentional focus
            old_focus = self.focus.get_focus()
            new_focus = self.focus.update_focus()
            
            # 6. Notify focus change
            if old_focus != new_focus:
                self._notify_focus_change(new_focus)
            
            # 7. Reset bank for next cycle
            self.bank.cycle_reset()
            
            self.stats['cycles'] += 1
    
    def _collect_rent(self):
        """Collect rent from atoms."""
        total_rent = 0.0
        
        for atom in self.atomspace:
            if atom.attention_value.vlti:
                continue  # VLTI atoms don't pay rent
            
            # Calculate rent based on STI
            rent = self.params.rent_rate
            if self.focus.is_in_focus(atom.handle):
                rent *= self.params.rent_focus_multiplier
            
            # Deduct rent from STI
            new_sti = atom.attention_value.sti - rent
            new_av = AttentionValue(
                sti=new_sti,
                lti=atom.attention_value.lti,
                vlti=atom.attention_value.vlti
            )
            self.atomspace.set_attention_value(atom.handle, new_av)
            
            total_rent += rent
        
        self.bank.collect_rent(total_rent)
        self.stats['rent_events'] += 1
    
    def _apply_decay(self):
        """Apply attention decay."""
        self.atomspace.decay_attention(self.params.sti_decay_rate)
    
    def _update_hebbian(self):
        """Update Hebbian links based on co-activation."""
        # Record current focus as co-activation
        focus = self.focus.get_focus()
        if focus:
            self.hebbian_manager.record_activation(focus)
        
        # Periodically update Hebbian links
        if self.stats['cycles'] % 10 == 0:
            self.hebbian_manager.update_hebbian_links()
    
    def _attention_loop(self):
        """Background attention loop."""
        while self._running:
            try:
                self.run_cycle()
            except Exception as e:
                pass  # Log in production
            
            time.sleep(self.cycle_interval)
    
    # =========================================================================
    # WAGE SYSTEM
    # =========================================================================
    
    def pay_wage(self, handle: AtomHandle, reason: str = "useful"):
        """Pay wage to a useful atom."""
        wage = self.params.wage_rate
        if reason == "inference":
            wage = self.params.inference_wage
        
        actual = self.bank.pay_wage(wage)
        if actual > 0:
            self.atomspace.stimulate(handle, actual)
            self.stats['wage_events'] += 1
    
    def reward_inference_atoms(self, handles: List[AtomHandle]):
        """Reward atoms that participated in inference."""
        for handle in handles:
            self.pay_wage(handle, "inference")
    
    # =========================================================================
    # IMPORTANCE UPDATES
    # =========================================================================
    
    def boost_importance(
        self,
        handle: AtomHandle,
        sti_boost: float = 0.0,
        lti_boost: float = 0.0
    ):
        """Boost an atom's importance."""
        atom = self.atomspace.get_atom(handle)
        if not atom:
            return
        
        new_av = AttentionValue(
            sti=min(1.0, atom.attention_value.sti + sti_boost),
            lti=min(1.0, atom.attention_value.lti + lti_boost),
            vlti=atom.attention_value.vlti
        )
        self.atomspace.set_attention_value(handle, new_av)
    
    def set_vlti(self, handle: AtomHandle, vlti: bool = True):
        """Set or unset VLTI (Very Long-Term Importance) flag."""
        atom = self.atomspace.get_atom(handle)
        if not atom:
            return
        
        new_av = AttentionValue(
            sti=atom.attention_value.sti,
            lti=atom.attention_value.lti,
            vlti=vlti
        )
        self.atomspace.set_attention_value(handle, new_av)
    
    # =========================================================================
    # CALLBACKS
    # =========================================================================
    
    def on_focus_change(self, callback: Callable[[Set[AtomHandle]], None]):
        """Register callback for focus changes."""
        self._on_focus_change.append(callback)
    
    def _notify_focus_change(self, new_focus: Set[AtomHandle]):
        """Notify callbacks of focus change."""
        for callback in self._on_focus_change:
            try:
                callback(new_focus)
            except:
                pass
    
    # =========================================================================
    # GOAL-DIRECTED ATTENTION
    # =========================================================================
    
    def focus_on_goal(self, goal_handle: AtomHandle, spread: bool = True):
        """
        Direct attention toward a goal.
        """
        # Force goal into focus
        self.focus.force_focus(goal_handle)
        
        # Stimulate goal
        self.stimulate(goal_handle, self.params.stimulus_per_atom * 10)
        
        # Spread attention to related atoms
        if spread:
            self.diffusion.spread_importance(
                goal_handle,
                self.params.stimulus_per_atom * 5
            )
    
    def defocus(self, handle: AtomHandle):
        """
        Remove attention from an atom.
        """
        atom = self.atomspace.get_atom(handle)
        if atom:
            new_av = AttentionValue(
                sti=0.0,
                lti=atom.attention_value.lti,
                vlti=atom.attention_value.vlti
            )
            self.atomspace.set_attention_value(handle, new_av)


# =============================================================================
# ATTENTION-BASED SELECTION
# =============================================================================

class AttentionBasedSelector:
    """
    Utility for selecting atoms based on attention.
    Used by other cognitive processes to select what to work on.
    """
    
    def __init__(self, atomspace: AtomSpace, ecan: ECANService):
        self.atomspace = atomspace
        self.ecan = ecan
    
    def select_by_attention(
        self,
        candidates: List[AtomHandle],
        n: int = 1,
        temperature: float = 1.0
    ) -> List[AtomHandle]:
        """
        Select atoms probabilistically based on attention.
        Higher temperature = more random, lower = more deterministic.
        """
        if not candidates:
            return []
        
        # Get attention values
        weights = []
        for handle in candidates:
            atom = self.atomspace.get_atom(handle)
            if atom:
                # Use softmax-like weighting
                weight = math.exp(atom.attention_value.sti / temperature)
                weights.append((handle, weight))
            else:
                weights.append((handle, 0.0))
        
        # Normalize weights
        total = sum(w for _, w in weights)
        if total <= 0:
            # Uniform selection if no attention
            return random.sample(candidates, min(n, len(candidates)))
        
        weights = [(h, w / total) for h, w in weights]
        
        # Weighted selection
        selected = []
        remaining = weights.copy()
        
        for _ in range(min(n, len(candidates))):
            if not remaining:
                break
            
            r = random.random()
            cumulative = 0.0
            
            for i, (handle, weight) in enumerate(remaining):
                cumulative += weight
                if r <= cumulative:
                    selected.append(handle)
                    remaining.pop(i)
                    # Renormalize
                    total = sum(w for _, w in remaining)
                    if total > 0:
                        remaining = [(h, w / total) for h, w in remaining]
                    break
        
        return selected
    
    def select_from_focus(self, n: int = 1) -> List[AtomHandle]:
        """Select atoms from the attentional focus."""
        focus = list(self.ecan.get_attentional_focus())
        return self.select_by_attention(focus, n)
    
    def select_by_type_and_attention(
        self,
        atom_type: AtomType,
        n: int = 1
    ) -> List[AtomHandle]:
        """Select atoms of a specific type based on attention."""
        atoms = self.atomspace.get_atoms_by_type(atom_type)
        handles = [a.handle for a in atoms]
        return self.select_by_attention(handles, n)


# Export
__all__ = [
    'ECANConfig',
    'ECANParameters',
    'AttentionBank',
    'HebbianLinkManager',
    'ImportanceDiffusion',
    'AttentionalFocus',
    'ECANService',
    'AttentionBasedSelector',
]
