"""
Dynamic Streams Module
======================

Implementation of Eric Schwarz's three dynamic streams:
1. Entropic Stream: en-tropis → auto-vortis → auto-morphosis
2. Negentropic Stream: negen-tropis → auto-stasis → auto-poiesis
3. Identity Stream: iden-tropis → auto-gnosis → auto-genesis

These streams represent the fundamental organizational dynamics
of self-organizing systems.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime
import math


class StreamPhase(Enum):
    """Phases within each dynamic stream."""
    # Entropic stream phases
    EN_TROPIS = auto()      # Tendency toward organization
    AUTO_VORTIS = auto()    # Self-organizing vortex patterns
    AUTO_MORPHOSIS = auto() # Self-transformation
    
    # Negentropic stream phases
    NEGEN_TROPIS = auto()   # Resistance to entropy
    AUTO_STASIS = auto()    # Self-maintaining equilibrium
    AUTO_POIESIS = auto()   # Self-creating
    
    # Identity stream phases
    IDEN_TROPIS = auto()    # Identity formation
    AUTO_GNOSIS = auto()    # Self-knowledge
    AUTO_GENESIS = auto()   # Self-generation


@dataclass
class StreamState:
    """State of a dynamic stream."""
    energy: float = 0.0      # Current energy level (0.0 to 1.0)
    stability: float = 0.5   # Stability measure (0.0 to 1.0)
    coherence: float = 0.5   # Internal coherence (0.0 to 1.0)
    flow_rate: float = 0.0   # Rate of flow through stream
    phase: StreamPhase = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'energy': self.energy,
            'stability': self.stability,
            'coherence': self.coherence,
            'flow_rate': self.flow_rate,
            'phase': self.phase.name if self.phase else None
        }


@dataclass
class StreamInteraction:
    """Interaction between two streams."""
    source_stream: str
    target_stream: str
    interaction_type: str  # 'reinforcing', 'balancing', 'transforming'
    strength: float
    timestamp: datetime = field(default_factory=datetime.now)


class DynamicStream:
    """Base class for organizational dynamic streams."""
    
    def __init__(self, name: str):
        self.name = name
        self.state = StreamState()
        self._history: List[StreamState] = []
        self._interactions: List[StreamInteraction] = []
    
    def update(self, delta_t: float, inputs: Dict[str, float]) -> StreamState:
        """Update stream state based on inputs."""
        # Store history
        self._history.append(StreamState(
            energy=self.state.energy,
            stability=self.state.stability,
            coherence=self.state.coherence,
            flow_rate=self.state.flow_rate,
            phase=self.state.phase
        ))
        
        # Trim history
        if len(self._history) > 100:
            self._history = self._history[-100:]
        
        # Update state (to be overridden by subclasses)
        self._update_internal(delta_t, inputs)
        
        return self.state
    
    def _update_internal(self, delta_t: float, inputs: Dict[str, float]):
        """Internal update logic (override in subclasses)."""
        pass
    
    def interact_with(self, other: 'DynamicStream', interaction_type: str, strength: float):
        """Record interaction with another stream."""
        interaction = StreamInteraction(
            source_stream=self.name,
            target_stream=other.name,
            interaction_type=interaction_type,
            strength=strength
        )
        self._interactions.append(interaction)
    
    def get_trend(self, metric: str, window: int = 10) -> float:
        """Get trend of a metric over recent history."""
        if len(self._history) < 2:
            return 0.0
        
        recent = self._history[-window:]
        values = [getattr(s, metric, 0.0) for s in recent]
        
        if len(values) < 2:
            return 0.0
        
        # Simple linear regression slope
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        
        numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        return numerator / denominator if denominator > 0 else 0.0


class EntropicStream(DynamicStream):
    """
    Entropic Stream: en-tropis → auto-vortis → auto-morphosis
    
    Represents the tendency toward organization through transformation.
    This stream drives change, adaptation, and evolution.
    """
    
    def __init__(self):
        super().__init__("entropic")
        self.state.phase = StreamPhase.EN_TROPIS
        
        # Stream-specific attributes
        self.en_tropis = 0.0      # Tendency toward organization
        self.auto_vortis = 0.0    # Self-organizing vortex patterns
        self.auto_morphosis = 0.0 # Self-transformation
        
        # Transformation potential
        self.transformation_potential = 0.5
        self.vortex_intensity = 0.0
    
    def _update_internal(self, delta_t: float, inputs: Dict[str, float]):
        """Update entropic stream dynamics."""
        # External inputs
        external_energy = inputs.get('external_energy', 0.0)
        perturbation = inputs.get('perturbation', 0.0)
        
        # Phase 1: en-tropis (tendency toward organization)
        # Increases with external energy and perturbation
        self.en_tropis = min(1.0, self.en_tropis + (external_energy + perturbation) * delta_t * 0.1)
        
        # Phase 2: auto-vortis (self-organizing vortex)
        # Emerges when en-tropis exceeds threshold
        if self.en_tropis > 0.3:
            self.auto_vortis = min(1.0, self.auto_vortis + self.en_tropis * delta_t * 0.05)
            self.vortex_intensity = self.auto_vortis * self.en_tropis
        else:
            self.auto_vortis = max(0.0, self.auto_vortis - delta_t * 0.02)
        
        # Phase 3: auto-morphosis (self-transformation)
        # Occurs when vortex is strong enough
        if self.auto_vortis > 0.5:
            self.auto_morphosis = min(1.0, self.auto_morphosis + self.auto_vortis * delta_t * 0.03)
            self.transformation_potential = 0.5 + self.auto_morphosis * 0.5
        else:
            self.auto_morphosis = max(0.0, self.auto_morphosis - delta_t * 0.01)
        
        # Update stream state
        self.state.energy = (self.en_tropis + self.auto_vortis + self.auto_morphosis) / 3
        self.state.stability = 1.0 - self.vortex_intensity  # Less stable when vortex is strong
        self.state.coherence = self.auto_vortis  # Coherence comes from vortex organization
        self.state.flow_rate = self.en_tropis * self.transformation_potential
        
        # Determine current phase
        if self.auto_morphosis > 0.5:
            self.state.phase = StreamPhase.AUTO_MORPHOSIS
        elif self.auto_vortis > 0.3:
            self.state.phase = StreamPhase.AUTO_VORTIS
        else:
            self.state.phase = StreamPhase.EN_TROPIS
    
    def get_transformation_readiness(self) -> float:
        """Get readiness for transformation."""
        return self.auto_morphosis * self.transformation_potential


class NegentropicStream(DynamicStream):
    """
    Negentropic Stream: negen-tropis → auto-stasis → auto-poiesis
    
    Represents resistance to entropy and self-maintenance.
    This stream drives stability, preservation, and self-creation.
    """
    
    def __init__(self):
        super().__init__("negentropic")
        self.state.phase = StreamPhase.NEGEN_TROPIS
        
        # Stream-specific attributes
        self.negen_tropis = 0.5   # Resistance to entropy
        self.auto_stasis = 0.5   # Self-maintaining equilibrium
        self.auto_poiesis = 0.0  # Self-creating
        
        # Maintenance capacity
        self.maintenance_capacity = 0.5
        self.creation_potential = 0.0
    
    def _update_internal(self, delta_t: float, inputs: Dict[str, float]):
        """Update negentropic stream dynamics."""
        # External inputs
        entropy_pressure = inputs.get('entropy_pressure', 0.0)
        resources = inputs.get('resources', 0.5)
        
        # Phase 1: negen-tropis (resistance to entropy)
        # Maintains against entropy pressure using resources
        resistance = resources - entropy_pressure
        self.negen_tropis = max(0.0, min(1.0, self.negen_tropis + resistance * delta_t * 0.1))
        
        # Phase 2: auto-stasis (self-maintaining equilibrium)
        # Emerges when resistance is successful
        if self.negen_tropis > 0.4:
            equilibrium_target = 0.5 + self.negen_tropis * 0.3
            self.auto_stasis += (equilibrium_target - self.auto_stasis) * delta_t * 0.1
            self.maintenance_capacity = self.auto_stasis
        else:
            self.auto_stasis = max(0.0, self.auto_stasis - delta_t * 0.05)
        
        # Phase 3: auto-poiesis (self-creating)
        # Occurs when equilibrium is stable and resources are abundant
        if self.auto_stasis > 0.6 and resources > 0.5:
            self.auto_poiesis = min(1.0, self.auto_poiesis + self.auto_stasis * delta_t * 0.02)
            self.creation_potential = self.auto_poiesis * resources
        else:
            self.auto_poiesis = max(0.0, self.auto_poiesis - delta_t * 0.01)
        
        # Update stream state
        self.state.energy = resources * self.negen_tropis
        self.state.stability = self.auto_stasis
        self.state.coherence = (self.negen_tropis + self.auto_stasis) / 2
        self.state.flow_rate = self.creation_potential
        
        # Determine current phase
        if self.auto_poiesis > 0.5:
            self.state.phase = StreamPhase.AUTO_POIESIS
        elif self.auto_stasis > 0.5:
            self.state.phase = StreamPhase.AUTO_STASIS
        else:
            self.state.phase = StreamPhase.NEGEN_TROPIS
    
    def get_creation_readiness(self) -> float:
        """Get readiness for self-creation."""
        return self.auto_poiesis * self.creation_potential


class IdentityStream(DynamicStream):
    """
    Identity Stream: iden-tropis → auto-gnosis → auto-genesis
    
    Represents identity formation and self-generation.
    This stream drives self-awareness, self-knowledge, and self-generation.
    """
    
    def __init__(self):
        super().__init__("identity")
        self.state.phase = StreamPhase.IDEN_TROPIS
        
        # Stream-specific attributes
        self.iden_tropis = 0.0    # Identity formation
        self.auto_gnosis = 0.0   # Self-knowledge
        self.auto_genesis = 0.0  # Self-generation
        
        # Identity coherence
        self.identity_coherence = 0.0
        self.self_model_depth = 0
        self.generation_capacity = 0.0
    
    def _update_internal(self, delta_t: float, inputs: Dict[str, float]):
        """Update identity stream dynamics."""
        # External inputs
        self_awareness = inputs.get('self_awareness', 0.0)
        reflection_depth = inputs.get('reflection_depth', 0)
        experience = inputs.get('experience', 0.0)
        
        # Phase 1: iden-tropis (identity formation)
        # Forms through self-awareness and experience
        identity_input = (self_awareness + experience) / 2
        self.iden_tropis = min(1.0, self.iden_tropis + identity_input * delta_t * 0.05)
        
        # Phase 2: auto-gnosis (self-knowledge)
        # Emerges when identity is forming and reflection occurs
        if self.iden_tropis > 0.3 and reflection_depth > 0:
            gnosis_growth = self.iden_tropis * (reflection_depth / 5) * delta_t * 0.03
            self.auto_gnosis = min(1.0, self.auto_gnosis + gnosis_growth)
            self.self_model_depth = max(self.self_model_depth, reflection_depth)
        else:
            self.auto_gnosis = max(0.0, self.auto_gnosis - delta_t * 0.01)
        
        # Phase 3: auto-genesis (self-generation)
        # Occurs when self-knowledge is deep enough
        if self.auto_gnosis > 0.6:
            genesis_potential = self.auto_gnosis * self.iden_tropis
            self.auto_genesis = min(1.0, self.auto_genesis + genesis_potential * delta_t * 0.02)
            self.generation_capacity = self.auto_genesis * self.auto_gnosis
        else:
            self.auto_genesis = max(0.0, self.auto_genesis - delta_t * 0.01)
        
        # Update identity coherence
        self.identity_coherence = (self.iden_tropis + self.auto_gnosis + self.auto_genesis) / 3
        
        # Update stream state
        self.state.energy = self.identity_coherence
        self.state.stability = self.auto_gnosis  # Stability through self-knowledge
        self.state.coherence = self.identity_coherence
        self.state.flow_rate = self.generation_capacity
        
        # Determine current phase
        if self.auto_genesis > 0.5:
            self.state.phase = StreamPhase.AUTO_GENESIS
        elif self.auto_gnosis > 0.3:
            self.state.phase = StreamPhase.AUTO_GNOSIS
        else:
            self.state.phase = StreamPhase.IDEN_TROPIS
    
    def get_generation_readiness(self) -> float:
        """Get readiness for self-generation."""
        return self.auto_genesis * self.generation_capacity


class StreamTriad:
    """
    The three dynamic streams working together.
    
    Represents the complete organizational dynamics of a self-organizing system.
    """
    
    def __init__(self):
        self.entropic = EntropicStream()
        self.negentropic = NegentropicStream()
        self.identity = IdentityStream()
        
        self._last_update = datetime.now()
    
    def update(self, inputs: Dict[str, Dict[str, float]]) -> Dict[str, StreamState]:
        """
        Update all streams.
        
        Args:
            inputs: Dictionary of inputs for each stream
                {
                    'entropic': {'external_energy': 0.5, 'perturbation': 0.1},
                    'negentropic': {'entropy_pressure': 0.3, 'resources': 0.7},
                    'identity': {'self_awareness': 0.6, 'reflection_depth': 3, 'experience': 0.5}
                }
        
        Returns:
            Dictionary of stream states
        """
        now = datetime.now()
        delta_t = (now - self._last_update).total_seconds()
        self._last_update = now
        
        # Update each stream
        entropic_state = self.entropic.update(delta_t, inputs.get('entropic', {}))
        negentropic_state = self.negentropic.update(delta_t, inputs.get('negentropic', {}))
        identity_state = self.identity.update(delta_t, inputs.get('identity', {}))
        
        # Process stream interactions
        self._process_interactions()
        
        return {
            'entropic': entropic_state,
            'negentropic': negentropic_state,
            'identity': identity_state
        }
    
    def _process_interactions(self):
        """Process interactions between streams."""
        # Entropic ↔ Negentropic: Balancing interaction
        # High entropy reduces stability, high negentropy resists change
        if self.entropic.state.energy > 0.6:
            self.negentropic.negen_tropis = max(0.0, 
                self.negentropic.negen_tropis - self.entropic.vortex_intensity * 0.1)
            self.entropic.interact_with(self.negentropic, 'balancing', 
                self.entropic.vortex_intensity)
        
        # Negentropic → Identity: Reinforcing interaction
        # Stability enables identity formation
        if self.negentropic.auto_stasis > 0.5:
            self.identity.iden_tropis = min(1.0,
                self.identity.iden_tropis + self.negentropic.auto_stasis * 0.05)
            self.negentropic.interact_with(self.identity, 'reinforcing',
                self.negentropic.auto_stasis)
        
        # Identity → Entropic: Transforming interaction
        # Self-knowledge enables directed transformation
        if self.identity.auto_gnosis > 0.5:
            self.entropic.transformation_potential = min(1.0,
                self.entropic.transformation_potential + self.identity.auto_gnosis * 0.1)
            self.identity.interact_with(self.entropic, 'transforming',
                self.identity.auto_gnosis)
    
    def get_overall_coherence(self) -> float:
        """Get overall system coherence from all streams."""
        return (
            self.entropic.state.coherence +
            self.negentropic.state.coherence +
            self.identity.state.coherence
        ) / 3
    
    def get_overall_stability(self) -> float:
        """Get overall system stability."""
        return (
            self.entropic.state.stability +
            self.negentropic.state.stability +
            self.identity.state.stability
        ) / 3
    
    def get_evolution_readiness(self) -> float:
        """Get readiness for system evolution."""
        return (
            self.entropic.get_transformation_readiness() +
            self.negentropic.get_creation_readiness() +
            self.identity.get_generation_readiness()
        ) / 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert triad state to dictionary."""
        return {
            'entropic': {
                'state': self.entropic.state.to_dict(),
                'en_tropis': self.entropic.en_tropis,
                'auto_vortis': self.entropic.auto_vortis,
                'auto_morphosis': self.entropic.auto_morphosis,
                'transformation_potential': self.entropic.transformation_potential
            },
            'negentropic': {
                'state': self.negentropic.state.to_dict(),
                'negen_tropis': self.negentropic.negen_tropis,
                'auto_stasis': self.negentropic.auto_stasis,
                'auto_poiesis': self.negentropic.auto_poiesis,
                'creation_potential': self.negentropic.creation_potential
            },
            'identity': {
                'state': self.identity.state.to_dict(),
                'iden_tropis': self.identity.iden_tropis,
                'auto_gnosis': self.identity.auto_gnosis,
                'auto_genesis': self.identity.auto_genesis,
                'generation_capacity': self.identity.generation_capacity
            },
            'overall': {
                'coherence': self.get_overall_coherence(),
                'stability': self.get_overall_stability(),
                'evolution_readiness': self.get_evolution_readiness()
            }
        }
