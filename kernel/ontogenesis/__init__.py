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

from .b_series import (  # Rooted trees; B-series; Butcher tableau; Composition
    BSeriesExpansion,
    BSeriesTerm,
    ButcherTableau,
    RootedTree,
    compose_b_series,
    generate_rooted_trees,
    invert_b_series,
)
from .evolution_engine import (  # State; Engine
    EvolutionConfig,
    EvolutionEngine,
    EvolutionEvent,
    EvolutionProposal,
    EvolutionState,
    EvolutionTrigger,
)
from .kernel_generator import (  # Types; Generation; Composition
    GeneratedKernel,
    GenerationConfig,
    GenerationStrategy,
    KernelComposer,
    KernelGenerator,
    KernelSpec,
    KernelType,
)


__all__ = [
    # B-series
    "RootedTree",
    "generate_rooted_trees",
    "BSeriesTerm",
    "BSeriesExpansion",
    "ButcherTableau",
    "compose_b_series",
    "invert_b_series",
    # Kernel generation
    "KernelType",
    "KernelSpec",
    "GeneratedKernel",
    "GenerationStrategy",
    "GenerationConfig",
    "KernelGenerator",
    "KernelComposer",
    # Evolution
    "EvolutionState",
    "EvolutionTrigger",
    "EvolutionEvent",
    "EvolutionProposal",
    "EvolutionConfig",
    "EvolutionEngine",
]

__version__ = "0.1.0"
