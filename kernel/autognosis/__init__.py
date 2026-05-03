"""
Autognosis - Hierarchical Self-Image Building System
====================================================

The autognosis system enables the cognitive kernel to understand, monitor,
and optimize its own cognitive processes through hierarchical self-image building.

This represents a significant step toward truly self-aware AI systems.

Components:
- SelfMonitor: Continuous observation of system states and behaviors
- HierarchicalSelfModeler: Build multi-level self-images
- MetaCognitiveProcessor: Generate insights from self-images
- AutognosisOrchestrator: Coordinate the entire autognosis system

Usage:
    from kernel.autognosis import AutognosisOrchestrator, AutognosisConfig
    
    # Initialize autognosis
    config = AutognosisConfig(
        cycle_interval=30.0,
        max_levels=5,
        enable_auto_optimization=False
    )
    autognosis = AutognosisOrchestrator(config)
    
    # Initialize with kernel
    await autognosis.initialize(kernel)
    
    # Start background cycles
    await autognosis.start(kernel)
    
    # Or run manual cycle
    result = await autognosis.run_autognosis_cycle(kernel)
    
    # Get status
    status = autognosis.get_status()
    report = autognosis.get_self_awareness_report()
"""

from .types import (
    # Enumerations
    SelfAwarenessLevel,
    InsightType,
    InsightPriority,
    OptimizationType,
    
    # Observation types
    ComponentState,
    PerformanceMetrics,
    BehavioralPattern,
    Anomaly,
    SystemObservation,
    
    # Self-image types
    MetaReflection,
    SelfImage,
    
    # Insight types
    MetaCognitiveInsight,
    OptimizationOpportunity,
    
    # Result types
    AutognosisCycleResult,
    SelfAwarenessAssessment
)

from .self_monitor import SelfMonitor, MonitorConfig
from .self_modeler import HierarchicalSelfModeler, ModelerConfig
from .orchestrator import AutognosisOrchestrator, AutognosisConfig

__all__ = [
    # Main orchestrator
    'AutognosisOrchestrator',
    'AutognosisConfig',
    
    # Components
    'SelfMonitor',
    'MonitorConfig',
    'HierarchicalSelfModeler',
    'ModelerConfig',
    
    # Enumerations
    'SelfAwarenessLevel',
    'InsightType',
    'InsightPriority',
    'OptimizationType',
    
    # Types
    'ComponentState',
    'PerformanceMetrics',
    'BehavioralPattern',
    'Anomaly',
    'SystemObservation',
    'MetaReflection',
    'SelfImage',
    'MetaCognitiveInsight',
    'OptimizationOpportunity',
    'AutognosisCycleResult',
    'SelfAwarenessAssessment'
]

__version__ = '0.1.0'
