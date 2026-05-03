"""
VORTEX Architecture
===================

Vortical Organization for Recursive Transformation and EXpansion.

VORTEX represents self-organizing cognitive dynamics through
vortical patterns that enable recursive self-improvement.

Components:
- Primitives: Core vortex types and structures
- Orchestrator: Coordination with kernel components

The VORTEX architecture provides:
- Self-organizing cognitive structures
- Recursive transformation patterns
- Dynamic attention allocation
- Memory consolidation dynamics

Usage:
    from kernel.vortex import VortexOrchestrator, VortexConfig
    
    # Initialize orchestrator
    config = VortexConfig(
        update_interval=0.5,
        enable_metamodel_coupling=True
    )
    vortex = VortexOrchestrator(config)
    
    # Initialize with kernel
    await vortex.initialize(kernel)
    
    # Start dynamics
    await vortex.start()
    
    # Create attention vortex
    attention = vortex.create_attention_vortex("important_concept")
    
    # Get status
    status = vortex.get_status()
"""

from .primitives import (
    # Core types
    VortexPhase,
    VortexScale,
    FlowDirection,
    VortexState,
    
    # Primitives
    VortexCore,
    VortexArm,
    VortexBoundary,
    
    # Main entity
    Vortex,
    
    # Interactions
    VortexInteraction,
    InteractionResult,
    compute_interaction,
    
    # Field
    VortexField
)

from .orchestrator import (
    VortexConfig,
    VortexOrchestrator
)

__all__ = [
    # Orchestrator
    'VortexOrchestrator',
    'VortexConfig',
    
    # Core types
    'VortexPhase',
    'VortexScale',
    'FlowDirection',
    'VortexState',
    
    # Primitives
    'VortexCore',
    'VortexArm',
    'VortexBoundary',
    'Vortex',
    
    # Interactions
    'VortexInteraction',
    'InteractionResult',
    'compute_interaction',
    
    # Field
    'VortexField'
]

__version__ = '0.1.0'
