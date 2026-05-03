"""
VORTEX Architecture Primitives
==============================

Implementation of the VORTEX (Vortical Organization for Recursive
Transformation and EXpansion) architecture primitives.

VORTEX represents self-organizing cognitive dynamics through
vortical patterns that enable recursive self-improvement.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any, Tuple, Set, Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from datetime import datetime
import math
import asyncio
import logging


logger = logging.getLogger("VORTEX.Primitives")


# =============================================================================
# VORTEX CORE TYPES
# =============================================================================

class VortexPhase(Enum):
    """Phases of vortical dynamics."""
    CONVERGENCE = auto()   # Drawing inward
    COMPRESSION = auto()   # Intensification
    TRANSFORMATION = auto() # Core change
    EXPANSION = auto()     # Radiating outward
    INTEGRATION = auto()   # Stabilization


class VortexScale(Enum):
    """Scales of vortical organization."""
    MICRO = auto()    # Individual atom/concept level
    MESO = auto()     # Pattern/schema level
    MACRO = auto()    # System/architecture level
    META = auto()     # Self-referential level


class FlowDirection(Enum):
    """Direction of vortical flow."""
    INWARD = auto()   # Centripetal
    OUTWARD = auto()  # Centrifugal
    CIRCULAR = auto() # Rotational
    HELICAL = auto()  # Spiral (combined)


@dataclass
class VortexState:
    """State of a vortex."""
    phase: VortexPhase = VortexPhase.CONVERGENCE
    scale: VortexScale = VortexScale.MESO
    intensity: float = 0.0      # 0.0 to 1.0
    coherence: float = 0.5      # Internal coherence
    angular_momentum: float = 0.0  # Rotational energy
    radial_velocity: float = 0.0   # Inward/outward flow
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'phase': self.phase.name,
            'scale': self.scale.name,
            'intensity': self.intensity,
            'coherence': self.coherence,
            'angular_momentum': self.angular_momentum,
            'radial_velocity': self.radial_velocity
        }


# =============================================================================
# VORTEX PRIMITIVES
# =============================================================================

@dataclass
class VortexCore:
    """
    The core of a vortex - the point of maximum transformation.
    
    The core is where:
    - Convergent flows meet
    - Maximum compression occurs
    - Transformation happens
    - New patterns emerge
    """
    position: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    radius: float = 1.0
    density: float = 1.0
    temperature: float = 1.0  # Metaphorical - activity level
    
    def attraction_strength(self, distance: float) -> float:
        """Compute attraction strength at a distance."""
        if distance <= 0:
            return float('inf')
        return self.density / (distance ** 2)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'position': self.position,
            'radius': self.radius,
            'density': self.density,
            'temperature': self.temperature
        }


@dataclass
class VortexArm:
    """
    A spiral arm of a vortex.
    
    Arms are the channels through which:
    - Information flows toward/from core
    - Patterns propagate
    - Coherence spreads
    """
    arm_id: str
    origin: Tuple[float, float, float]
    direction: FlowDirection
    length: float = 1.0
    width: float = 0.1
    flow_rate: float = 0.0
    content: List[Any] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'arm_id': self.arm_id,
            'origin': self.origin,
            'direction': self.direction.name,
            'length': self.length,
            'width': self.width,
            'flow_rate': self.flow_rate,
            'content_count': len(self.content)
        }


@dataclass
class VortexBoundary:
    """
    The boundary of a vortex.
    
    The boundary defines:
    - Scope of influence
    - Interface with environment
    - Permeability for exchange
    """
    inner_radius: float = 0.5
    outer_radius: float = 2.0
    permeability: float = 0.5  # 0 = closed, 1 = open
    surface_tension: float = 0.5
    
    def is_inside(self, distance: float) -> bool:
        """Check if a point is inside the vortex."""
        return distance <= self.outer_radius
    
    def is_in_core(self, distance: float) -> bool:
        """Check if a point is in the core region."""
        return distance <= self.inner_radius
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'inner_radius': self.inner_radius,
            'outer_radius': self.outer_radius,
            'permeability': self.permeability,
            'surface_tension': self.surface_tension
        }


# =============================================================================
# VORTEX ENTITY
# =============================================================================

class Vortex:
    """
    A complete vortex entity.
    
    Represents a self-organizing cognitive structure that:
    - Attracts related concepts
    - Transforms through compression
    - Radiates new patterns
    - Maintains coherence
    """
    
    def __init__(self, vortex_id: str, scale: VortexScale = VortexScale.MESO):
        self.vortex_id = vortex_id
        self.state = VortexState(scale=scale)
        self.core = VortexCore()
        self.arms: List[VortexArm] = []
        self.boundary = VortexBoundary()
        
        # Dynamics
        self._creation_time = datetime.now()
        self._last_update = datetime.now()
        self._cycle_count = 0
        
        # Content
        self._attracted_items: List[Any] = []
        self._transformed_items: List[Any] = []
        self._radiated_items: List[Any] = []
    
    def update(self, delta_t: float, inputs: Dict[str, float]) -> VortexState:
        """Update vortex dynamics."""
        self._last_update = datetime.now()
        
        # External inputs
        external_energy = inputs.get('energy', 0.0)
        perturbation = inputs.get('perturbation', 0.0)
        
        # Update intensity based on attracted content
        content_factor = len(self._attracted_items) / 100.0
        self.state.intensity = min(1.0, content_factor + external_energy * 0.1)
        
        # Update angular momentum
        self.state.angular_momentum += external_energy * 0.05
        self.state.angular_momentum *= 0.99  # Decay
        
        # Update radial velocity based on phase
        if self.state.phase in [VortexPhase.CONVERGENCE, VortexPhase.COMPRESSION]:
            self.state.radial_velocity = -self.state.intensity * 0.5  # Inward
        elif self.state.phase in [VortexPhase.EXPANSION, VortexPhase.INTEGRATION]:
            self.state.radial_velocity = self.state.intensity * 0.3  # Outward
        else:
            self.state.radial_velocity = 0.0
        
        # Update coherence
        if self.state.angular_momentum > 0.5:
            self.state.coherence = min(1.0, self.state.coherence + 0.01)
        else:
            self.state.coherence = max(0.0, self.state.coherence - 0.005)
        
        # Phase transitions
        self._check_phase_transition()
        
        return self.state
    
    def _check_phase_transition(self):
        """Check and execute phase transitions."""
        current = self.state.phase
        
        if current == VortexPhase.CONVERGENCE:
            if self.state.intensity > 0.6:
                self.state.phase = VortexPhase.COMPRESSION
        
        elif current == VortexPhase.COMPRESSION:
            if self.state.intensity > 0.8 and self.state.coherence > 0.7:
                self.state.phase = VortexPhase.TRANSFORMATION
                self._cycle_count += 1
        
        elif current == VortexPhase.TRANSFORMATION:
            # Transformation is brief
            self._transform_content()
            self.state.phase = VortexPhase.EXPANSION
        
        elif current == VortexPhase.EXPANSION:
            if self.state.intensity < 0.4:
                self.state.phase = VortexPhase.INTEGRATION
        
        elif current == VortexPhase.INTEGRATION:
            if self.state.coherence > 0.8:
                self.state.phase = VortexPhase.CONVERGENCE
    
    def attract(self, item: Any, strength: float = 1.0) -> bool:
        """Attract an item into the vortex."""
        if self.state.phase in [VortexPhase.CONVERGENCE, VortexPhase.COMPRESSION]:
            self._attracted_items.append(item)
            return True
        return False
    
    def _transform_content(self):
        """Transform attracted content."""
        # Move attracted items to transformed
        for item in self._attracted_items:
            transformed = self._apply_transformation(item)
            self._transformed_items.append(transformed)
        self._attracted_items.clear()
    
    def _apply_transformation(self, item: Any) -> Any:
        """Apply vortex transformation to an item."""
        # Placeholder - actual transformation depends on item type
        return {'original': item, 'transformed': True, 'cycle': self._cycle_count}
    
    def radiate(self) -> List[Any]:
        """Radiate transformed content outward."""
        if self.state.phase in [VortexPhase.EXPANSION, VortexPhase.INTEGRATION]:
            radiated = self._transformed_items.copy()
            self._radiated_items.extend(radiated)
            self._transformed_items.clear()
            return radiated
        return []
    
    def add_arm(self, direction: FlowDirection) -> VortexArm:
        """Add a spiral arm to the vortex."""
        arm_id = f"{self.vortex_id}_arm_{len(self.arms)}"
        arm = VortexArm(
            arm_id=arm_id,
            origin=self.core.position,
            direction=direction
        )
        self.arms.append(arm)
        return arm
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get vortex metrics."""
        return {
            'vortex_id': self.vortex_id,
            'state': self.state.to_dict(),
            'core': self.core.to_dict(),
            'boundary': self.boundary.to_dict(),
            'arms': len(self.arms),
            'attracted': len(self._attracted_items),
            'transformed': len(self._transformed_items),
            'radiated': len(self._radiated_items),
            'cycles': self._cycle_count,
            'age_seconds': (datetime.now() - self._creation_time).total_seconds()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        return self.get_metrics()


# =============================================================================
# VORTEX INTERACTIONS
# =============================================================================

class VortexInteraction(Enum):
    """Types of vortex interactions."""
    MERGER = auto()       # Two vortices merge
    COLLISION = auto()    # Vortices collide and bounce
    RESONANCE = auto()    # Vortices synchronize
    HIERARCHY = auto()    # One vortex contains another
    CHAIN = auto()        # Vortices form a chain


@dataclass
class InteractionResult:
    """Result of a vortex interaction."""
    interaction_type: VortexInteraction
    vortex_a: str
    vortex_b: str
    outcome: str
    energy_transfer: float
    new_vortices: List[str] = field(default_factory=list)
    destroyed_vortices: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'interaction_type': self.interaction_type.name,
            'vortex_a': self.vortex_a,
            'vortex_b': self.vortex_b,
            'outcome': self.outcome,
            'energy_transfer': self.energy_transfer,
            'new_vortices': self.new_vortices,
            'destroyed_vortices': self.destroyed_vortices
        }


def compute_interaction(v1: Vortex, v2: Vortex) -> Optional[InteractionResult]:
    """
    Compute interaction between two vortices.
    
    Returns interaction result if vortices interact, None otherwise.
    """
    # Compute distance between cores
    dx = v1.core.position[0] - v2.core.position[0]
    dy = v1.core.position[1] - v2.core.position[1]
    dz = v1.core.position[2] - v2.core.position[2]
    distance = math.sqrt(dx*dx + dy*dy + dz*dz)
    
    # Check if vortices are close enough to interact
    interaction_range = v1.boundary.outer_radius + v2.boundary.outer_radius
    
    if distance > interaction_range:
        return None
    
    # Determine interaction type based on relative properties
    intensity_ratio = v1.state.intensity / max(0.01, v2.state.intensity)
    coherence_diff = abs(v1.state.coherence - v2.state.coherence)
    
    if distance < (v1.boundary.inner_radius + v2.boundary.inner_radius):
        # Cores overlap - merger or collision
        if coherence_diff < 0.2:
            interaction_type = VortexInteraction.MERGER
            outcome = "merged"
        else:
            interaction_type = VortexInteraction.COLLISION
            outcome = "bounced"
    
    elif coherence_diff < 0.1 and abs(v1.state.angular_momentum - v2.state.angular_momentum) < 0.2:
        # Similar properties - resonance
        interaction_type = VortexInteraction.RESONANCE
        outcome = "synchronized"
    
    elif intensity_ratio > 3.0 or intensity_ratio < 0.33:
        # Large size difference - hierarchy
        interaction_type = VortexInteraction.HIERARCHY
        outcome = "nested"
    
    else:
        # Default - chain
        interaction_type = VortexInteraction.CHAIN
        outcome = "linked"
    
    # Compute energy transfer
    energy_transfer = (v1.state.intensity - v2.state.intensity) * 0.1
    
    return InteractionResult(
        interaction_type=interaction_type,
        vortex_a=v1.vortex_id,
        vortex_b=v2.vortex_id,
        outcome=outcome,
        energy_transfer=energy_transfer
    )


# =============================================================================
# VORTEX FIELD
# =============================================================================

class VortexField:
    """
    A field containing multiple interacting vortices.
    
    The field manages:
    - Vortex creation and destruction
    - Inter-vortex interactions
    - Global field dynamics
    - Emergent patterns
    """
    
    def __init__(self, field_id: str = "default"):
        self.field_id = field_id
        self.vortices: Dict[str, Vortex] = {}
        self._vortex_counter = 0
        
        # Field properties
        self.field_energy = 0.0
        self.field_coherence = 0.5
        self.background_flow = (0.0, 0.0, 0.0)
        
        # History
        self._interactions: List[InteractionResult] = []
        self._creation_time = datetime.now()
    
    def create_vortex(self, scale: VortexScale = VortexScale.MESO,
                      position: Tuple[float, float, float] = None) -> Vortex:
        """Create a new vortex in the field."""
        self._vortex_counter += 1
        vortex_id = f"{self.field_id}_v{self._vortex_counter:04d}"
        
        vortex = Vortex(vortex_id, scale)
        
        if position:
            vortex.core.position = position
        
        self.vortices[vortex_id] = vortex
        return vortex
    
    def destroy_vortex(self, vortex_id: str) -> bool:
        """Destroy a vortex."""
        if vortex_id in self.vortices:
            del self.vortices[vortex_id]
            return True
        return False
    
    def update(self, delta_t: float) -> Dict[str, Any]:
        """Update all vortices and compute interactions."""
        # Update each vortex
        for vortex in self.vortices.values():
            inputs = {
                'energy': self.field_energy,
                'perturbation': 0.0
            }
            vortex.update(delta_t, inputs)
        
        # Compute interactions
        vortex_list = list(self.vortices.values())
        new_interactions = []
        
        for i, v1 in enumerate(vortex_list):
            for v2 in vortex_list[i+1:]:
                interaction = compute_interaction(v1, v2)
                if interaction:
                    new_interactions.append(interaction)
                    self._apply_interaction(interaction)
        
        self._interactions.extend(new_interactions)
        
        # Update field properties
        self._update_field_properties()
        
        return {
            'vortex_count': len(self.vortices),
            'interactions': len(new_interactions),
            'field_energy': self.field_energy,
            'field_coherence': self.field_coherence
        }
    
    def _apply_interaction(self, interaction: InteractionResult):
        """Apply the effects of an interaction."""
        v1 = self.vortices.get(interaction.vortex_a)
        v2 = self.vortices.get(interaction.vortex_b)
        
        if not v1 or not v2:
            return
        
        if interaction.interaction_type == VortexInteraction.RESONANCE:
            # Synchronize coherence
            avg_coherence = (v1.state.coherence + v2.state.coherence) / 2
            v1.state.coherence = avg_coherence
            v2.state.coherence = avg_coherence
        
        elif interaction.interaction_type == VortexInteraction.MERGER:
            # Merge v2 into v1
            v1.state.intensity += v2.state.intensity * 0.5
            v1._attracted_items.extend(v2._attracted_items)
            self.destroy_vortex(v2.vortex_id)
            interaction.destroyed_vortices.append(v2.vortex_id)
    
    def _update_field_properties(self):
        """Update global field properties."""
        if not self.vortices:
            self.field_energy = 0.0
            self.field_coherence = 0.5
            return
        
        # Field energy is sum of vortex intensities
        self.field_energy = sum(v.state.intensity for v in self.vortices.values())
        
        # Field coherence is average of vortex coherences
        self.field_coherence = sum(v.state.coherence for v in self.vortices.values()) / len(self.vortices)
    
    def get_vortex(self, vortex_id: str) -> Optional[Vortex]:
        """Get a vortex by ID."""
        return self.vortices.get(vortex_id)
    
    def get_all_vortices(self) -> List[Vortex]:
        """Get all vortices."""
        return list(self.vortices.values())
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get field metrics."""
        return {
            'field_id': self.field_id,
            'vortex_count': len(self.vortices),
            'field_energy': self.field_energy,
            'field_coherence': self.field_coherence,
            'total_interactions': len(self._interactions),
            'age_seconds': (datetime.now() - self._creation_time).total_seconds(),
            'vortices': {vid: v.get_metrics() for vid, v in self.vortices.items()}
        }
    
    def to_dict(self) -> Dict[str, Any]:
        return self.get_metrics()
