"""
Ontogenesis Module
==================

Self-evolution and kernel generation for the cognitive system.
Based on B-series theory for systematic kernel derivation.

Components:
- B-Series: Mathematical foundation for kernel generation
- Kernel Generator: Creates optimal cognitive kernels
- Evolution Engine: Manages self-evolution lifecycle

The ontogenesis module enables:
- Systematic kernel generation
- Evolutionary optimization
- Safe deployment with rollback
- Manus-approved evolution

Usage:
    from kernel.ontogenesis import (
        EvolutionEngine, EvolutionConfig,
        KernelGenerator, KernelSpec, KernelType
    )
    
    # Initialize evolution engine
    config = EvolutionConfig(
        enable_auto_evolution=True,
        require_manus_approval=True
    )
    engine = EvolutionEngine(config)
    
    # Initialize with kernel
    await engine.initialize(kernel)
    
    # Start automatic evolution
    await engine.start()
    
    # Manual evolution trigger
    proposal = await engine.evolve(KernelType.INFERENCE)
    
    # Get active kernels
    kernels = engine.get_all_active_kernels()
"""

from .b_series import (
    # Rooted trees
    RootedTree,
    generate_rooted_trees,
    
    # B-series
    BSeriesTerm,
    BSeriesExpansion,
    
    # Butcher tableau
    ButcherTableau,
    
    # Composition
    compose_b_series,
    invert_b_series
)

from .kernel_generator import (
    # Types
    KernelType,
    KernelSpec,
    GeneratedKernel,
    
    # Generation
    GenerationStrategy,
    GenerationConfig,
    KernelGenerator,
    
    # Composition
    KernelComposer
)

from .evolution_engine import (
    # State
    EvolutionState,
    EvolutionTrigger,
    EvolutionEvent,
    EvolutionProposal,
    
    # Engine
    EvolutionConfig,
    EvolutionEngine
)

__all__ = [
    # B-series
    'RootedTree',
    'generate_rooted_trees',
    'BSeriesTerm',
    'BSeriesExpansion',
    'ButcherTableau',
    'compose_b_series',
    'invert_b_series',
    
    # Kernel generation
    'KernelType',
    'KernelSpec',
    'GeneratedKernel',
    'GenerationStrategy',
    'GenerationConfig',
    'KernelGenerator',
    'KernelComposer',
    
    # Evolution
    'EvolutionState',
    'EvolutionTrigger',
    'EvolutionEvent',
    'EvolutionProposal',
    'EvolutionConfig',
    'EvolutionEngine'
]

__version__ = '0.1.0'
