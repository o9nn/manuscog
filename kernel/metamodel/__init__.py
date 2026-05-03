"""
Holistic Metamodel
==================

Implementation of Eric Schwarz's organizational systems theory
for comprehensive self-organizing dynamics.

Components:
- Dynamic Streams: Entropic, Negentropic, Identity
- Numerical Hierarchy: 1, 2, 3, 4, 7, 9, 11

The metamodel provides:
- Unified organizational dynamics
- Self-organizing behavior patterns
- Evolution readiness assessment
- Coherence monitoring

Usage:
    from kernel.metamodel import HolisticMetamodelOrchestrator, MetamodelConfig
    
    # Initialize metamodel
    config = MetamodelConfig(
        update_interval=1.0,
        enable_stream_interactions=True
    )
    metamodel = HolisticMetamodelOrchestrator(config)
    
    # Initialize with kernel
    await metamodel.initialize(kernel)
    
    # Start background updates
    await metamodel.start()
    
    # Get status
    status = metamodel.get_status()
    coherence = metamodel.get_coherence_report()
    guidance = metamodel.get_evolution_guidance()
"""

from .streams import (
    # Stream types
    StreamPhase,
    StreamState,
    StreamInteraction,
    DynamicStream,
    EntropicStream,
    NegentropicStream,
    IdentityStream,
    StreamTriad
)

from .numerical_hierarchy import (
    # Level 1
    HieroglyphicMonad,
    
    # Level 2
    DualPole,
    DualState,
    DualComplementarity,
    
    # Level 3
    TriadicElement,
    TriadicState,
    TriadicSystem,
    
    # Level 4
    CyclePhase,
    CycleState,
    SelfStabilizingCycle,
    
    # Level 7
    ProductionStep,
    TriadProductionProcess,
    
    # Level 9
    EnneadAspect,
    EnneadMetaSystem,
    
    # Level 11
    HelixPhase,
    EvolutionaryHelix,
    
    # Orchestrator
    NumericalHierarchy
)

from .orchestrator import (
    MetamodelConfig,
    MetamodelState,
    HolisticMetamodelOrchestrator
)

__all__ = [
    # Main orchestrator
    'HolisticMetamodelOrchestrator',
    'MetamodelConfig',
    'MetamodelState',
    
    # Streams
    'StreamPhase',
    'StreamState',
    'StreamInteraction',
    'DynamicStream',
    'EntropicStream',
    'NegentropicStream',
    'IdentityStream',
    'StreamTriad',
    
    # Numerical Hierarchy
    'NumericalHierarchy',
    'HieroglyphicMonad',
    'DualPole',
    'DualState',
    'DualComplementarity',
    'TriadicElement',
    'TriadicState',
    'TriadicSystem',
    'CyclePhase',
    'CycleState',
    'SelfStabilizingCycle',
    'ProductionStep',
    'TriadProductionProcess',
    'EnneadAspect',
    'EnneadMetaSystem',
    'HelixPhase',
    'EvolutionaryHelix'
]

__version__ = '0.1.0'
