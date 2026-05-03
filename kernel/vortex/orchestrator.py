"""
VORTEX Orchestrator Module
==========================

Coordinates VORTEX dynamics with other kernel components.
Manages the vortical organization of cognitive processes.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import logging

from .primitives import (
    VortexPhase, VortexScale, FlowDirection,
    VortexState, Vortex, VortexField,
    VortexInteraction, InteractionResult
)

if TYPE_CHECKING:
    from kernel.cognitive_kernel import CognitiveKernel
    from kernel.metamodel import HolisticMetamodelOrchestrator
    from kernel.autognosis import AutognosisOrchestrator


logger = logging.getLogger("VORTEX.Orchestrator")


@dataclass
class VortexConfig:
    """Configuration for VORTEX orchestrator."""
    update_interval: float = 0.5  # seconds
    max_vortices: int = 100
    auto_create_threshold: float = 0.7
    auto_destroy_threshold: float = 0.1
    enable_metamodel_coupling: bool = True


class VortexOrchestrator:
    """
    Orchestrates VORTEX dynamics for the cognitive kernel.
    
    Manages:
    - Vortex lifecycle
    - Field dynamics
    - Integration with metamodel
    - Cognitive process mapping
    """
    
    def __init__(self, config: VortexConfig = None):
        self.config = config or VortexConfig()
        
        # Main vortex field
        self.field = VortexField("cognitive_field")
        
        # Specialized fields for different cognitive processes
        self.attention_field = VortexField("attention")
        self.memory_field = VortexField("memory")
        self.reasoning_field = VortexField("reasoning")
        
        # State
        self._is_running = False
        self._update_task: Optional[asyncio.Task] = None
        
        # External references
        self._kernel: Optional['CognitiveKernel'] = None
        self._metamodel: Optional['HolisticMetamodelOrchestrator'] = None
        self._autognosis: Optional['AutognosisOrchestrator'] = None
        
        # Metrics
        self._total_cycles = 0
        self._total_transformations = 0
    
    async def initialize(self, kernel: 'CognitiveKernel'):
        """Initialize the VORTEX orchestrator."""
        logger.info("Initializing VORTEX Orchestrator...")
        
        self._kernel = kernel
        
        # Get metamodel reference
        if hasattr(kernel, 'metamodel') and kernel.metamodel:
            self._metamodel = kernel.metamodel
        
        # Get autognosis reference
        if hasattr(kernel, 'autognosis') and kernel.autognosis:
            self._autognosis = kernel.autognosis
        
        # Create initial vortices
        self._create_initial_vortices()
        
        logger.info("VORTEX Orchestrator initialized")
    
    async def start(self):
        """Start the VORTEX orchestrator."""
        if self._is_running:
            logger.warning("VORTEX Orchestrator already running")
            return
        
        self._is_running = True
        self._update_task = asyncio.create_task(self._update_loop())
        logger.info("VORTEX Orchestrator started")
    
    async def stop(self):
        """Stop the VORTEX orchestrator."""
        self._is_running = False
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
        logger.info("VORTEX Orchestrator stopped")
    
    def _create_initial_vortices(self):
        """Create initial vortex structures."""
        # Main cognitive vortex
        main_vortex = self.field.create_vortex(
            scale=VortexScale.MACRO,
            position=(0.0, 0.0, 0.0)
        )
        main_vortex.add_arm(FlowDirection.INWARD)
        main_vortex.add_arm(FlowDirection.OUTWARD)
        main_vortex.add_arm(FlowDirection.HELICAL)
        
        # Attention vortices
        for i in range(3):
            v = self.attention_field.create_vortex(
                scale=VortexScale.MESO,
                position=(float(i), 0.0, 0.0)
            )
            v.add_arm(FlowDirection.CIRCULAR)
        
        # Memory vortex
        memory_v = self.memory_field.create_vortex(
            scale=VortexScale.MACRO,
            position=(0.0, 0.0, 0.0)
        )
        memory_v.boundary.permeability = 0.3  # Less permeable
        
        # Reasoning vortex
        reasoning_v = self.reasoning_field.create_vortex(
            scale=VortexScale.MACRO,
            position=(0.0, 0.0, 0.0)
        )
        reasoning_v.add_arm(FlowDirection.HELICAL)
    
    async def _update_loop(self):
        """Background update loop."""
        while self._is_running:
            try:
                await asyncio.sleep(self.config.update_interval)
                await self._update_all_fields()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"VORTEX update error: {e}")
    
    async def _update_all_fields(self):
        """Update all vortex fields."""
        delta_t = self.config.update_interval
        
        # Update main field
        main_result = self.field.update(delta_t)
        
        # Update specialized fields
        attention_result = self.attention_field.update(delta_t)
        memory_result = self.memory_field.update(delta_t)
        reasoning_result = self.reasoning_field.update(delta_t)
        
        # Couple with metamodel if enabled
        if self.config.enable_metamodel_coupling and self._metamodel:
            await self._couple_with_metamodel()
        
        # Auto-manage vortices
        await self._auto_manage_vortices()
        
        self._total_cycles += 1
    
    async def _couple_with_metamodel(self):
        """Couple VORTEX dynamics with metamodel."""
        if not self._metamodel:
            return
        
        # Get metamodel state
        metamodel_state = self._metamodel.state
        
        # Map entropic stream to main field energy
        entropic_energy = self._metamodel.streams.entropic.state.energy
        self.field.field_energy = entropic_energy
        
        # Map negentropic stream to memory field coherence
        negentropic_stability = self._metamodel.streams.negentropic.state.stability
        for vortex in self.memory_field.get_all_vortices():
            vortex.state.coherence = negentropic_stability
        
        # Map identity stream to reasoning field
        identity_coherence = self._metamodel.streams.identity.identity_coherence
        for vortex in self.reasoning_field.get_all_vortices():
            vortex.state.intensity = identity_coherence
    
    async def _auto_manage_vortices(self):
        """Automatically create/destroy vortices based on dynamics."""
        # Check for high-energy regions that need new vortices
        if self.field.field_energy > self.config.auto_create_threshold:
            if len(self.field.vortices) < self.config.max_vortices:
                self.field.create_vortex(scale=VortexScale.MICRO)
        
        # Check for low-intensity vortices to destroy
        to_destroy = []
        for vortex in self.field.get_all_vortices():
            if vortex.state.intensity < self.config.auto_destroy_threshold:
                if vortex.state.scale == VortexScale.MICRO:
                    to_destroy.append(vortex.vortex_id)
        
        for vortex_id in to_destroy:
            self.field.destroy_vortex(vortex_id)
    
    # =========================================================================
    # PUBLIC API
    # =========================================================================
    
    def create_attention_vortex(self, focus: str) -> Vortex:
        """Create a new attention vortex for a specific focus."""
        vortex = self.attention_field.create_vortex(scale=VortexScale.MESO)
        vortex.attract(focus)
        return vortex
    
    def create_reasoning_vortex(self, problem: str) -> Vortex:
        """Create a reasoning vortex for a problem."""
        vortex = self.reasoning_field.create_vortex(scale=VortexScale.MESO)
        vortex.attract(problem)
        vortex.add_arm(FlowDirection.HELICAL)
        return vortex
    
    def store_in_memory(self, item: Any) -> bool:
        """Store an item in memory vortex."""
        vortices = self.memory_field.get_all_vortices()
        if vortices:
            return vortices[0].attract(item)
        return False
    
    def get_field_status(self) -> Dict[str, Any]:
        """Get status of all vortex fields."""
        return {
            'main_field': self.field.get_metrics(),
            'attention_field': self.attention_field.get_metrics(),
            'memory_field': self.memory_field.get_metrics(),
            'reasoning_field': self.reasoning_field.get_metrics()
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status."""
        return {
            'is_running': self._is_running,
            'total_cycles': self._total_cycles,
            'total_transformations': self._total_transformations,
            'fields': self.get_field_status(),
            'config': {
                'update_interval': self.config.update_interval,
                'max_vortices': self.config.max_vortices,
                'metamodel_coupling': self.config.enable_metamodel_coupling
            }
        }
