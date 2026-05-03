"""
Numerical Hierarchy Module
==========================

Implementation of Eric Schwarz's numerical hierarchy:
1 - Hieroglyphic Monad (Unity)
2 - Dual Complementarity (Actual-Virtual)
3 - Triadic System (Being-Becoming-Relation)
4 - Self-Stabilizing Cycle (Four-phase development)
7 - Triad Production (Seven-step developmental sequence)
9 - Ennead Meta-System (Creativity-Stability-Drift)
11 - Evolutionary Helix (Long-term transformation)

Each number represents a fundamental organizational principle.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime
import math


# =============================================================================
# THE ONE - HIEROGLYPHIC MONAD
# =============================================================================

class HieroglyphicMonad:
    """
    The 1 - Unity Principle
    
    The undifferentiated source from which all organization emerges.
    Represents the fundamental unity underlying all complexity.
    """
    
    def __init__(self):
        self.unity_field = 1.0
        self.manifestation_level = 0
        self._manifestations: Dict[int, float] = {}
    
    def manifest_at_level(self, level: int) -> float:
        """
        Manifest unity at a specific organizational level.
        
        The monad manifests differently at each level while
        remaining fundamentally one.
        """
        if level not in self._manifestations:
            # Unity manifests as 1/level at each level
            # Higher levels have more differentiated manifestation
            self._manifestations[level] = self.unity_field / max(1, level)
        
        self.manifestation_level = level
        return self._manifestations[level]
    
    def get_unity_measure(self) -> float:
        """Get the current unity measure."""
        return self.unity_field
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'unity_field': self.unity_field,
            'manifestation_level': self.manifestation_level,
            'manifestations': self._manifestations
        }


# =============================================================================
# THE TWO - DUAL COMPLEMENTARITY
# =============================================================================

class DualPole(Enum):
    """The two complementary poles."""
    ACTUAL = auto()    # Manifest, concrete, realized
    VIRTUAL = auto()   # Potential, abstract, possible


@dataclass
class DualState:
    """State of the dual complementarity."""
    actual: float = 0.5
    virtual: float = 0.5
    tension: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'actual': self.actual,
            'virtual': self.virtual,
            'tension': self.tension
        }


class DualComplementarity:
    """
    The 2 - Actual-Virtual Dialectics
    
    The fundamental duality from which all organization arises.
    Actual and Virtual are complementary, not opposed.
    """
    
    def __init__(self):
        self.state = DualState()
        self._history: List[DualState] = []
    
    def update(self, actual_input: float, virtual_input: float) -> DualState:
        """Update the dual state based on inputs."""
        # Store history
        self._history.append(DualState(
            actual=self.state.actual,
            virtual=self.state.virtual,
            tension=self.state.tension
        ))
        
        # Normalize inputs
        total = actual_input + virtual_input
        if total > 0:
            self.state.actual = actual_input / total
            self.state.virtual = virtual_input / total
        
        # Compute tension (difference from equilibrium)
        self.state.tension = abs(self.state.actual - self.state.virtual)
        
        return self.state
    
    def resolve_tension(self, system_state: Dict[str, Any]) -> DualState:
        """Resolve tension based on system state."""
        # Extract relevant factors
        stability = system_state.get('stability', 0.5)
        change_pressure = system_state.get('change_pressure', 0.5)
        
        # Stability favors actual, change favors virtual
        self.state.actual = 0.5 + (stability - 0.5) * 0.3
        self.state.virtual = 0.5 + (change_pressure - 0.5) * 0.3
        
        # Normalize
        total = self.state.actual + self.state.virtual
        self.state.actual /= total
        self.state.virtual /= total
        
        self.state.tension = abs(self.state.actual - self.state.virtual)
        
        return self.state
    
    def get_dominant_pole(self) -> DualPole:
        """Get the currently dominant pole."""
        return DualPole.ACTUAL if self.state.actual > self.state.virtual else DualPole.VIRTUAL
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'state': self.state.to_dict(),
            'dominant_pole': self.get_dominant_pole().name,
            'history_length': len(self._history)
        }


# =============================================================================
# THE THREE - TRIADIC SYSTEM
# =============================================================================

class TriadicElement(Enum):
    """The three fundamental elements."""
    BEING = auto()      # What is (static aspect)
    BECOMING = auto()   # What changes (dynamic aspect)
    RELATION = auto()   # How they connect (relational aspect)


@dataclass
class TriadicState:
    """State of the triadic system."""
    being: float = 0.33
    becoming: float = 0.33
    relation: float = 0.34
    equilibrium: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'being': self.being,
            'becoming': self.becoming,
            'relation': self.relation,
            'equilibrium': self.equilibrium
        }


class TriadicSystem:
    """
    The 3 - Being-Becoming-Relation
    
    The fundamental triad from which complex organization emerges.
    Being (structure), Becoming (process), Relation (connection).
    """
    
    def __init__(self):
        self.state = TriadicState()
        self._history: List[TriadicState] = []
    
    def update(self, being_input: float, becoming_input: float, 
               relation_input: float) -> TriadicState:
        """Update the triadic state."""
        # Store history
        self._history.append(TriadicState(
            being=self.state.being,
            becoming=self.state.becoming,
            relation=self.state.relation,
            equilibrium=self.state.equilibrium
        ))
        
        # Normalize inputs
        total = being_input + becoming_input + relation_input
        if total > 0:
            self.state.being = being_input / total
            self.state.becoming = becoming_input / total
            self.state.relation = relation_input / total
        
        # Compute equilibrium (how close to equal distribution)
        ideal = 1/3
        deviation = (
            abs(self.state.being - ideal) +
            abs(self.state.becoming - ideal) +
            abs(self.state.relation - ideal)
        ) / 3
        self.state.equilibrium = 1.0 - deviation
        
        return self.state
    
    def compute_equilibrium(self, system_state: Dict[str, Any]) -> TriadicState:
        """Compute equilibrium based on system state."""
        # Extract relevant factors
        structure = system_state.get('structure', 0.33)
        process = system_state.get('process', 0.33)
        connection = system_state.get('connection', 0.34)
        
        return self.update(structure, process, connection)
    
    def get_dominant_element(self) -> TriadicElement:
        """Get the currently dominant element."""
        max_val = max(self.state.being, self.state.becoming, self.state.relation)
        if max_val == self.state.being:
            return TriadicElement.BEING
        elif max_val == self.state.becoming:
            return TriadicElement.BECOMING
        else:
            return TriadicElement.RELATION
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'state': self.state.to_dict(),
            'dominant_element': self.get_dominant_element().name
        }


# =============================================================================
# THE FOUR - SELF-STABILIZING CYCLE
# =============================================================================

class CyclePhase(Enum):
    """The four phases of the self-stabilizing cycle."""
    EMERGENCE = auto()      # New patterns emerge
    DIFFERENTIATION = auto() # Patterns differentiate
    INTEGRATION = auto()     # Patterns integrate
    STABILIZATION = auto()   # System stabilizes


@dataclass
class CycleState:
    """State of the self-stabilizing cycle."""
    current_phase: CyclePhase = CyclePhase.EMERGENCE
    phase_progress: float = 0.0
    cycle_count: int = 0
    stability_index: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'current_phase': self.current_phase.name,
            'phase_progress': self.phase_progress,
            'cycle_count': self.cycle_count,
            'stability_index': self.stability_index
        }


class SelfStabilizingCycle:
    """
    The 4 - Four-Phase Development
    
    The fundamental cycle of organizational development:
    Emergence → Differentiation → Integration → Stabilization
    """
    
    def __init__(self):
        self.state = CycleState()
        self._phase_durations: Dict[CyclePhase, float] = {
            CyclePhase.EMERGENCE: 0.0,
            CyclePhase.DIFFERENTIATION: 0.0,
            CyclePhase.INTEGRATION: 0.0,
            CyclePhase.STABILIZATION: 0.0
        }
    
    def advance_phase(self, system_state: Dict[str, Any]) -> CycleState:
        """Advance the cycle based on system state."""
        # Get phase-specific inputs
        novelty = system_state.get('novelty', 0.0)
        complexity = system_state.get('complexity', 0.0)
        coherence = system_state.get('coherence', 0.0)
        stability = system_state.get('stability', 0.0)
        
        # Progress based on current phase
        if self.state.current_phase == CyclePhase.EMERGENCE:
            self.state.phase_progress += novelty * 0.1
            if self.state.phase_progress >= 1.0:
                self._transition_to(CyclePhase.DIFFERENTIATION)
        
        elif self.state.current_phase == CyclePhase.DIFFERENTIATION:
            self.state.phase_progress += complexity * 0.1
            if self.state.phase_progress >= 1.0:
                self._transition_to(CyclePhase.INTEGRATION)
        
        elif self.state.current_phase == CyclePhase.INTEGRATION:
            self.state.phase_progress += coherence * 0.1
            if self.state.phase_progress >= 1.0:
                self._transition_to(CyclePhase.STABILIZATION)
        
        elif self.state.current_phase == CyclePhase.STABILIZATION:
            self.state.phase_progress += stability * 0.1
            if self.state.phase_progress >= 1.0:
                self._transition_to(CyclePhase.EMERGENCE)
                self.state.cycle_count += 1
        
        # Update stability index
        self.state.stability_index = self._compute_stability_index()
        
        return self.state
    
    def _transition_to(self, phase: CyclePhase):
        """Transition to a new phase."""
        self._phase_durations[self.state.current_phase] = self.state.phase_progress
        self.state.current_phase = phase
        self.state.phase_progress = 0.0
    
    def _compute_stability_index(self) -> float:
        """Compute overall stability index."""
        # Stability increases with completed cycles and phase balance
        cycle_factor = min(1.0, self.state.cycle_count / 10)
        
        # Balance factor based on phase durations
        durations = list(self._phase_durations.values())
        if sum(durations) > 0:
            avg_duration = sum(durations) / len(durations)
            variance = sum((d - avg_duration) ** 2 for d in durations) / len(durations)
            balance_factor = 1.0 / (1.0 + variance)
        else:
            balance_factor = 0.5
        
        return (cycle_factor + balance_factor) / 2
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'state': self.state.to_dict(),
            'phase_durations': {p.name: d for p, d in self._phase_durations.items()}
        }


# =============================================================================
# THE SEVEN - TRIAD PRODUCTION
# =============================================================================

class ProductionStep(Enum):
    """The seven steps of triad production."""
    THESIS = auto()          # Initial position
    ANTITHESIS = auto()      # Counter-position
    SYNTHESIS = auto()       # Integration
    PROJECTION = auto()      # Externalization
    REFLECTION = auto()      # Internalization
    TRANSFORMATION = auto()  # Change
    TRANSCENDENCE = auto()   # Going beyond


class TriadProductionProcess:
    """
    The 7 - Seven-Step Developmental Sequence
    
    The process by which new triads are produced through
    dialectical development.
    """
    
    def __init__(self):
        self.current_step = ProductionStep.THESIS
        self.step_index = 0
        self.production_count = 0
        self._step_values: Dict[ProductionStep, float] = {
            step: 0.0 for step in ProductionStep
        }
    
    def advance(self, input_value: float) -> ProductionStep:
        """Advance the production process."""
        # Update current step value
        self._step_values[self.current_step] += input_value * 0.1
        
        # Check for transition
        if self._step_values[self.current_step] >= 1.0:
            self._step_values[self.current_step] = 1.0
            self.step_index = (self.step_index + 1) % 7
            self.current_step = list(ProductionStep)[self.step_index]
            
            if self.step_index == 0:
                self.production_count += 1
        
        return self.current_step
    
    def get_production_progress(self) -> float:
        """Get overall production progress."""
        return sum(self._step_values.values()) / 7
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'current_step': self.current_step.name,
            'step_index': self.step_index,
            'production_count': self.production_count,
            'step_values': {s.name: v for s, v in self._step_values.items()},
            'progress': self.get_production_progress()
        }


# =============================================================================
# THE NINE - ENNEAD META-SYSTEM
# =============================================================================

class EnneadAspect(Enum):
    """The nine aspects of the meta-system."""
    # Creativity aspects
    CREATION = auto()
    INNOVATION = auto()
    EMERGENCE = auto()
    
    # Stability aspects
    PRESERVATION = auto()
    MAINTENANCE = auto()
    EQUILIBRIUM = auto()
    
    # Drift aspects
    VARIATION = auto()
    ADAPTATION = auto()
    EVOLUTION = auto()


class EnneadMetaSystem:
    """
    The 9 - Creativity-Stability-Drift
    
    The meta-system that governs the balance between
    creativity, stability, and drift.
    """
    
    def __init__(self):
        self.aspects: Dict[EnneadAspect, float] = {
            aspect: 0.0 for aspect in EnneadAspect
        }
        
        # Group scores
        self.creativity = 0.0
        self.stability = 0.0
        self.drift = 0.0
    
    def update(self, inputs: Dict[str, float]) -> Dict[str, float]:
        """Update ennead aspects based on inputs."""
        # Map inputs to aspects
        aspect_mapping = {
            'novelty': EnneadAspect.CREATION,
            'innovation': EnneadAspect.INNOVATION,
            'emergence': EnneadAspect.EMERGENCE,
            'preservation': EnneadAspect.PRESERVATION,
            'maintenance': EnneadAspect.MAINTENANCE,
            'equilibrium': EnneadAspect.EQUILIBRIUM,
            'variation': EnneadAspect.VARIATION,
            'adaptation': EnneadAspect.ADAPTATION,
            'evolution': EnneadAspect.EVOLUTION
        }
        
        for input_name, aspect in aspect_mapping.items():
            if input_name in inputs:
                self.aspects[aspect] = inputs[input_name]
        
        # Update group scores
        self.creativity = (
            self.aspects[EnneadAspect.CREATION] +
            self.aspects[EnneadAspect.INNOVATION] +
            self.aspects[EnneadAspect.EMERGENCE]
        ) / 3
        
        self.stability = (
            self.aspects[EnneadAspect.PRESERVATION] +
            self.aspects[EnneadAspect.MAINTENANCE] +
            self.aspects[EnneadAspect.EQUILIBRIUM]
        ) / 3
        
        self.drift = (
            self.aspects[EnneadAspect.VARIATION] +
            self.aspects[EnneadAspect.ADAPTATION] +
            self.aspects[EnneadAspect.EVOLUTION]
        ) / 3
        
        return {
            'creativity': self.creativity,
            'stability': self.stability,
            'drift': self.drift
        }
    
    def get_dominant_mode(self) -> str:
        """Get the dominant mode (creativity, stability, or drift)."""
        modes = {
            'creativity': self.creativity,
            'stability': self.stability,
            'drift': self.drift
        }
        return max(modes, key=modes.get)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'aspects': {a.name: v for a, v in self.aspects.items()},
            'creativity': self.creativity,
            'stability': self.stability,
            'drift': self.drift,
            'dominant_mode': self.get_dominant_mode()
        }


# =============================================================================
# THE ELEVEN - EVOLUTIONARY HELIX
# =============================================================================

class HelixPhase(Enum):
    """Phases of the evolutionary helix."""
    DESCENT = auto()       # Going inward/downward
    NADIR = auto()         # Lowest point
    ASCENT = auto()        # Going outward/upward
    ZENITH = auto()        # Highest point
    TRANSITION = auto()    # Moving between spirals


class EvolutionaryHelix:
    """
    The 11 - Long-Term Transformation Cycles
    
    The evolutionary helix represents long-term transformation
    through spiraling cycles of descent and ascent.
    """
    
    def __init__(self):
        self.current_phase = HelixPhase.DESCENT
        self.spiral_count = 0
        self.phase_progress = 0.0
        self.elevation = 0.0  # Overall evolutionary level
        self._phase_history: List[Tuple[HelixPhase, float]] = []
    
    def advance(self, transformation_input: float) -> HelixPhase:
        """Advance the evolutionary helix."""
        self.phase_progress += transformation_input * 0.05
        
        if self.phase_progress >= 1.0:
            self._phase_history.append((self.current_phase, self.phase_progress))
            self.phase_progress = 0.0
            
            # Transition to next phase
            phases = list(HelixPhase)
            current_index = phases.index(self.current_phase)
            next_index = (current_index + 1) % len(phases)
            self.current_phase = phases[next_index]
            
            # Complete spiral at transition
            if self.current_phase == HelixPhase.DESCENT:
                self.spiral_count += 1
                self.elevation += 0.1  # Each spiral raises elevation
        
        return self.current_phase
    
    def get_evolutionary_level(self) -> float:
        """Get the current evolutionary level."""
        return self.elevation + self.phase_progress * 0.02
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'current_phase': self.current_phase.name,
            'spiral_count': self.spiral_count,
            'phase_progress': self.phase_progress,
            'elevation': self.elevation,
            'evolutionary_level': self.get_evolutionary_level()
        }


# =============================================================================
# NUMERICAL HIERARCHY ORCHESTRATOR
# =============================================================================

class NumericalHierarchy:
    """
    Orchestrator for the complete numerical hierarchy.
    
    Coordinates all numerical levels (1, 2, 3, 4, 7, 9, 11)
    to provide a unified organizational framework.
    """
    
    def __init__(self):
        self.monad = HieroglyphicMonad()
        self.dual = DualComplementarity()
        self.triad = TriadicSystem()
        self.cycle = SelfStabilizingCycle()
        self.production = TriadProductionProcess()
        self.ennead = EnneadMetaSystem()
        self.helix = EvolutionaryHelix()
    
    def update(self, system_state: Dict[str, Any]) -> Dict[str, Any]:
        """Update all numerical levels based on system state."""
        results = {}
        
        # Level 1: Monad
        level = system_state.get('complexity_level', 1)
        results['monad'] = {
            'manifestation': self.monad.manifest_at_level(level),
            'state': self.monad.to_dict()
        }
        
        # Level 2: Dual
        self.dual.resolve_tension(system_state)
        results['dual'] = self.dual.to_dict()
        
        # Level 3: Triad
        self.triad.compute_equilibrium(system_state)
        results['triad'] = self.triad.to_dict()
        
        # Level 4: Cycle
        self.cycle.advance_phase(system_state)
        results['cycle'] = self.cycle.to_dict()
        
        # Level 7: Production
        production_input = system_state.get('production_energy', 0.5)
        self.production.advance(production_input)
        results['production'] = self.production.to_dict()
        
        # Level 9: Ennead
        ennead_inputs = {
            'novelty': system_state.get('novelty', 0.0),
            'preservation': system_state.get('stability', 0.5),
            'adaptation': system_state.get('adaptability', 0.5)
        }
        self.ennead.update(ennead_inputs)
        results['ennead'] = self.ennead.to_dict()
        
        # Level 11: Helix
        transformation = system_state.get('transformation', 0.0)
        self.helix.advance(transformation)
        results['helix'] = self.helix.to_dict()
        
        return results
    
    def get_overall_coherence(self) -> float:
        """Get overall coherence across all levels."""
        coherence_factors = [
            self.monad.unity_field,
            1.0 - self.dual.state.tension,
            self.triad.state.equilibrium,
            self.cycle.state.stability_index,
            self.production.get_production_progress(),
            (self.ennead.creativity + self.ennead.stability + self.ennead.drift) / 3,
            self.helix.get_evolutionary_level()
        ]
        return sum(coherence_factors) / len(coherence_factors)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'monad': self.monad.to_dict(),
            'dual': self.dual.to_dict(),
            'triad': self.triad.to_dict(),
            'cycle': self.cycle.to_dict(),
            'production': self.production.to_dict(),
            'ennead': self.ennead.to_dict(),
            'helix': self.helix.to_dict(),
            'overall_coherence': self.get_overall_coherence()
        }
