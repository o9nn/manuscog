"""
Holistic Metamodel Orchestrator
===============================

Coordinates all metamodel components for comprehensive
self-organizing dynamics based on Eric Schwarz's theory.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging

from .streams import StreamTriad, StreamState
from .numerical_hierarchy import NumericalHierarchy

if TYPE_CHECKING:
    from kernel.cognitive_kernel import CognitiveKernel
    from kernel.autognosis import AutognosisOrchestrator


logger = logging.getLogger("Metamodel.Orchestrator")


@dataclass
class MetamodelConfig:
    """Configuration for the holistic metamodel."""
    update_interval: float = 1.0  # seconds
    enable_stream_interactions: bool = True
    enable_numerical_hierarchy: bool = True
    coherence_threshold: float = 0.5


@dataclass
class MetamodelState:
    """Current state of the metamodel."""
    timestamp: datetime = field(default_factory=datetime.now)
    stream_states: Dict[str, StreamState] = field(default_factory=dict)
    hierarchy_state: Dict[str, Any] = field(default_factory=dict)
    overall_coherence: float = 0.0
    evolution_readiness: float = 0.0
    dominant_mode: str = "balanced"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'stream_states': {k: v.to_dict() for k, v in self.stream_states.items()},
            'hierarchy_state': self.hierarchy_state,
            'overall_coherence': self.overall_coherence,
            'evolution_readiness': self.evolution_readiness,
            'dominant_mode': self.dominant_mode
        }


class HolisticMetamodelOrchestrator:
    """
    Coordinate all metamodel components.
    
    Integrates:
    - Three Dynamic Streams (Entropic, Negentropic, Identity)
    - Numerical Hierarchy (1, 2, 3, 4, 7, 9, 11)
    
    Provides:
    - Unified organizational dynamics
    - Self-organizing behavior
    - Evolution readiness assessment
    """
    
    def __init__(self, config: MetamodelConfig = None):
        self.config = config or MetamodelConfig()
        
        # Core components
        self.streams = StreamTriad()
        self.hierarchy = NumericalHierarchy()
        
        # State
        self.state = MetamodelState()
        self._history: List[MetamodelState] = []
        
        # Background task
        self._is_running = False
        self._update_task: Optional[asyncio.Task] = None
        
        # Kernel reference
        self._kernel: Optional['CognitiveKernel'] = None
        self._autognosis: Optional['AutognosisOrchestrator'] = None
    
    async def initialize(self, kernel: 'CognitiveKernel'):
        """Initialize the metamodel with kernel reference."""
        logger.info("Initializing Holistic Metamodel...")
        
        self._kernel = kernel
        
        # Get autognosis reference if available
        if hasattr(kernel, 'autognosis') and kernel.autognosis:
            self._autognosis = kernel.autognosis
        
        # Initial update
        await self._update_metamodel()
        
        logger.info("Holistic Metamodel initialized")
    
    async def start(self):
        """Start the metamodel background updates."""
        if self._is_running:
            logger.warning("Metamodel already running")
            return
        
        self._is_running = True
        self._update_task = asyncio.create_task(self._update_loop())
        logger.info("Metamodel background updates started")
    
    async def stop(self):
        """Stop the metamodel background updates."""
        self._is_running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
        logger.info("Metamodel background updates stopped")
    
    async def _update_loop(self):
        """Background loop for metamodel updates."""
        while self._is_running:
            try:
                await asyncio.sleep(self.config.update_interval)
                await self._update_metamodel()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metamodel update error: {e}")
    
    async def _update_metamodel(self):
        """Update all metamodel components."""
        timestamp = datetime.now()
        
        # Gather system state from kernel
        system_state = self._gather_system_state()
        
        # Update streams
        stream_inputs = self._compute_stream_inputs(system_state)
        stream_states = self.streams.update(stream_inputs)
        
        # Update numerical hierarchy
        hierarchy_state = self.hierarchy.update(system_state)
        
        # Compute overall metrics
        overall_coherence = self._compute_overall_coherence()
        evolution_readiness = self.streams.get_evolution_readiness()
        dominant_mode = self._determine_dominant_mode()
        
        # Update state
        self.state = MetamodelState(
            timestamp=timestamp,
            stream_states=stream_states,
            hierarchy_state=hierarchy_state,
            overall_coherence=overall_coherence,
            evolution_readiness=evolution_readiness,
            dominant_mode=dominant_mode
        )
        
        # Store history
        self._history.append(self.state)
        if len(self._history) > 100:
            self._history = self._history[-100:]
    
    def _gather_system_state(self) -> Dict[str, Any]:
        """Gather current system state from kernel."""
        state = {
            'stability': 0.5,
            'change_pressure': 0.5,
            'structure': 0.33,
            'process': 0.33,
            'connection': 0.34,
            'novelty': 0.0,
            'complexity': 0.5,
            'coherence': 0.5,
            'complexity_level': 1,
            'production_energy': 0.5,
            'adaptability': 0.5,
            'transformation': 0.0
        }
        
        if not self._kernel:
            return state
        
        # Get stats from kernel
        kernel_stats = self._kernel.stats if hasattr(self._kernel, 'stats') else {}
        
        # Compute stability from uptime and error rate
        uptime = kernel_stats.get('uptime', 0)
        errors = kernel_stats.get('errors', 0)
        if uptime > 0:
            error_rate = errors / uptime
            state['stability'] = max(0.0, 1.0 - error_rate * 10)
        
        # Get autognosis metrics if available
        if self._autognosis:
            autognosis_status = self._autognosis.get_status()
            
            # Self-awareness contributes to identity stream
            state['self_awareness'] = autognosis_status.get('self_awareness_score', 0.0)
            
            # Insights contribute to novelty
            state['novelty'] = min(1.0, autognosis_status.get('total_insights', 0) / 10)
            
            # Pending optimizations contribute to change pressure
            state['change_pressure'] = min(1.0, autognosis_status.get('pending_optimizations', 0) / 5)
        
        # AtomSpace metrics
        if self._kernel.atomspace:
            atom_count = self._kernel.atomspace.size()
            state['complexity'] = min(1.0, atom_count / 10000)
            state['complexity_level'] = max(1, int(atom_count / 1000))
        
        return state
    
    def _compute_stream_inputs(self, system_state: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
        """Compute inputs for each stream from system state."""
        return {
            'entropic': {
                'external_energy': system_state.get('change_pressure', 0.5),
                'perturbation': system_state.get('novelty', 0.0)
            },
            'negentropic': {
                'entropy_pressure': 1.0 - system_state.get('stability', 0.5),
                'resources': system_state.get('coherence', 0.5)
            },
            'identity': {
                'self_awareness': system_state.get('self_awareness', 0.0),
                'reflection_depth': system_state.get('complexity_level', 1),
                'experience': system_state.get('complexity', 0.5)
            }
        }
    
    def _compute_overall_coherence(self) -> float:
        """Compute overall metamodel coherence."""
        stream_coherence = self.streams.get_overall_coherence()
        hierarchy_coherence = self.hierarchy.get_overall_coherence()
        
        return (stream_coherence + hierarchy_coherence) / 2
    
    def _determine_dominant_mode(self) -> str:
        """Determine the dominant organizational mode."""
        # Check stream dominance
        entropic_energy = self.streams.entropic.state.energy
        negentropic_energy = self.streams.negentropic.state.energy
        identity_energy = self.streams.identity.state.energy
        
        # Check ennead dominance
        ennead_mode = self.hierarchy.ennead.get_dominant_mode()
        
        # Combine assessments
        if entropic_energy > 0.6:
            return "transformative"
        elif negentropic_energy > 0.6:
            return "stabilizing"
        elif identity_energy > 0.6:
            return "self-aware"
        else:
            return ennead_mode
    
    async def process_metamodel_cycle(self) -> MetamodelState:
        """Process a complete metamodel cycle and return state."""
        await self._update_metamodel()
        return self.state
    
    def get_evolution_guidance(self) -> Dict[str, Any]:
        """Get guidance for kernel evolution based on metamodel state."""
        guidance = {
            'ready_for_evolution': self.state.evolution_readiness > 0.5,
            'recommended_direction': None,
            'cautions': [],
            'opportunities': []
        }
        
        # Check stream states for guidance
        if self.streams.entropic.get_transformation_readiness() > 0.7:
            guidance['opportunities'].append("High transformation potential - consider structural changes")
            guidance['recommended_direction'] = "transformation"
        
        if self.streams.negentropic.get_creation_readiness() > 0.7:
            guidance['opportunities'].append("High creation potential - consider new capabilities")
            if not guidance['recommended_direction']:
                guidance['recommended_direction'] = "creation"
        
        if self.streams.identity.get_generation_readiness() > 0.7:
            guidance['opportunities'].append("High self-generation potential - consider self-modification")
            if not guidance['recommended_direction']:
                guidance['recommended_direction'] = "self-generation"
        
        # Check for cautions
        if self.state.overall_coherence < 0.3:
            guidance['cautions'].append("Low coherence - stabilize before evolving")
            guidance['ready_for_evolution'] = False
        
        if self.streams.get_overall_stability() < 0.3:
            guidance['cautions'].append("Low stability - risk of destabilization")
        
        # Check cycle phase
        cycle_phase = self.hierarchy.cycle.state.current_phase.name
        if cycle_phase == "EMERGENCE":
            guidance['opportunities'].append(f"In {cycle_phase} phase - good time for new patterns")
        elif cycle_phase == "STABILIZATION":
            guidance['cautions'].append(f"In {cycle_phase} phase - avoid major changes")
        
        return guidance
    
    def get_status(self) -> Dict[str, Any]:
        """Get metamodel status."""
        return {
            'is_running': self._is_running,
            'state': self.state.to_dict(),
            'streams': self.streams.to_dict(),
            'hierarchy': self.hierarchy.to_dict(),
            'evolution_guidance': self.get_evolution_guidance()
        }
    
    def get_coherence_report(self) -> Dict[str, Any]:
        """Get detailed coherence report."""
        return {
            'overall_coherence': self.state.overall_coherence,
            'stream_coherence': {
                'entropic': self.streams.entropic.state.coherence,
                'negentropic': self.streams.negentropic.state.coherence,
                'identity': self.streams.identity.state.coherence,
                'combined': self.streams.get_overall_coherence()
            },
            'hierarchy_coherence': self.hierarchy.get_overall_coherence(),
            'stability': {
                'stream_stability': self.streams.get_overall_stability(),
                'cycle_stability': self.hierarchy.cycle.state.stability_index
            },
            'dominant_mode': self.state.dominant_mode,
            'evolution_readiness': self.state.evolution_readiness
        }
