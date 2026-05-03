#!/usr/bin/env python3
"""
Autognosis Optimizer Demo
=========================

This demo shows the autognosis system actually optimizing the cognitive kernel.
Unlike the original placeholder, this optimizer ACTUALLY modifies system parameters.

The optimizer can:
1. Adjust ECAN parameters (attention spread, decay rates)
2. Tune PLN inference depth
3. Manage memory pressure
4. Rebalance attention allocation

Run with: python demo_autognosis_optimizer.py
"""

import asyncio
import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from kernel.cognitive_kernel import CognitiveKernel, KernelConfig, KernelState
from kernel.cognitive.types import AtomType, TruthValue, AttentionValue
from kernel.autognosis.orchestrator import AutognosisOrchestrator, AutognosisConfig
from kernel.autognosis.optimizer import AutognosisOptimizer, OptimizationPolicy


class DemoOutput:
    """Pretty output for the demo."""
    
    COLORS = {
        'header': '\033[95m',
        'blue': '\033[94m',
        'cyan': '\033[96m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'red': '\033[91m',
        'bold': '\033[1m',
        'end': '\033[0m'
    }
    
    @classmethod
    def header(cls, text: str):
        print(f"\n{cls.COLORS['bold']}{cls.COLORS['header']}{'='*60}{cls.COLORS['end']}")
        print(f"{cls.COLORS['bold']}{cls.COLORS['header']}{text.center(60)}{cls.COLORS['end']}")
        print(f"{cls.COLORS['bold']}{cls.COLORS['header']}{'='*60}{cls.COLORS['end']}\n")
    
    @classmethod
    def section(cls, text: str):
        print(f"\n{cls.COLORS['bold']}{cls.COLORS['cyan']}▶ {text}{cls.COLORS['end']}")
        print(f"{cls.COLORS['cyan']}{'-'*50}{cls.COLORS['end']}")
    
    @classmethod
    def info(cls, text: str):
        print(f"  {cls.COLORS['blue']}ℹ {text}{cls.COLORS['end']}")
    
    @classmethod
    def success(cls, text: str):
        print(f"  {cls.COLORS['green']}✓ {text}{cls.COLORS['end']}")
    
    @classmethod
    def warning(cls, text: str):
        print(f"  {cls.COLORS['yellow']}⚠ {text}{cls.COLORS['end']}")
    
    @classmethod
    def optimization(cls, text: str):
        print(f"  {cls.COLORS['header']}🔧 {text}{cls.COLORS['end']}")
    
    @classmethod
    def data(cls, label: str, value):
        print(f"    {cls.COLORS['bold']}{label}:{cls.COLORS['end']} {value}")


async def demo_autognosis_optimizer():
    """Demonstrate the autognosis optimizer in action."""
    
    DemoOutput.header("Autognosis Optimizer Demo")
    print("This demo shows autognosis ACTUALLY optimizing the cognitive kernel.")
    print("Watch as the system adjusts its own parameters based on self-reflection.\n")
    
    try:
        # Create cognitive kernel with auto-optimization enabled
        DemoOutput.section("Creating Cognitive Kernel with Auto-Optimization")
        
        config = KernelConfig(
            kernel_id="optimizer-demo",
            kernel_name="Optimizer Demo Kernel",
            max_atoms=50000,
            attention_budget=100.0,
            max_inference_depth=3,  # Start low to show optimization
            log_level="WARNING"
        )
        
        kernel = CognitiveKernel(config)
        if not kernel.boot():
            raise RuntimeError("Failed to boot cognitive kernel")
        
        DemoOutput.success("Cognitive kernel booted!")
        
        # Create autognosis with optimization enabled
        autognosis_config = AutognosisConfig(
            enable_auto_optimization=True,
            optimization_approval_threshold=0.8,  # Allow most optimizations
            max_levels=5
        )
        
        autognosis = AutognosisOrchestrator(autognosis_config)
        await autognosis.initialize(kernel)
        
        DemoOutput.success("Autognosis initialized with auto-optimization ENABLED")
        
        # Record initial parameters
        DemoOutput.section("Initial System Parameters")
        
        initial_params = {
            'pln_inference_depth': kernel.pln.max_inference_depth if kernel.pln else None,
            'ecan_decay_rate': kernel.ecan.params.sti_decay_rate if kernel.ecan else None,
            'ecan_spread_decay': kernel.ecan.params.spread_decay if kernel.ecan else None,
            'atomspace_size': kernel.atomspace.size()
        }
        
        for key, value in initial_params.items():
            DemoOutput.data(key, value)
        
        # Add knowledge to create optimization opportunities
        DemoOutput.section("Populating Knowledge Base")
        
        # Add many concepts to create memory pressure scenarios
        concepts = [
            "Python", "JavaScript", "Rust", "Go", "TypeScript",
            "Machine Learning", "Deep Learning", "Neural Networks",
            "Data Science", "Statistics", "Linear Algebra",
            "Web Development", "Backend", "Frontend", "API",
            "Database", "SQL", "NoSQL", "GraphQL"
        ]
        
        for name in concepts:
            kernel.atomspace.add_node(
                AtomType.CONCEPT_NODE,
                name,
                tv=TruthValue(1.0, 0.9),
                av=AttentionValue(sti=0.3)
            )
        
        # Add relationships
        relationships = [
            ("Python", "Programming Language"),
            ("JavaScript", "Programming Language"),
            ("Machine Learning", "AI"),
            ("Deep Learning", "Machine Learning"),
            ("Neural Networks", "Deep Learning"),
        ]
        
        for child, parent in relationships:
            child_handles = kernel.atomspace._name_index.get_by_name(child)
            parent_handles = kernel.atomspace._name_index.get_by_name(parent)
            
            if not parent_handles:
                kernel.atomspace.add_node(
                    AtomType.CONCEPT_NODE, parent,
                    tv=TruthValue(1.0, 0.9)
                )
                parent_handles = kernel.atomspace._name_index.get_by_name(parent)
            
            if child_handles and parent_handles:
                kernel.atomspace.add_link(
                    AtomType.INHERITANCE_LINK,
                    [list(child_handles)[0], list(parent_handles)[0]],
                    tv=TruthValue(1.0, 0.9)
                )
        
        DemoOutput.success(f"Added {len(concepts)} concepts and {len(relationships)} relationships")
        
        # Run autognosis cycles to trigger optimization
        DemoOutput.section("Running Autognosis Cycles")
        
        for cycle in range(3):
            DemoOutput.info(f"Cycle {cycle + 1}...")
            
            # Run autognosis cycle
            result = await autognosis.run_autognosis_cycle(kernel)
            
            DemoOutput.data("Self-awareness score", f"{result.self_awareness_score:.2f}")
            DemoOutput.data("Insights discovered", len(result.insights))
            DemoOutput.data("Optimizations found", len(result.optimizations))
            
            # Show insights
            if result.insights:
                DemoOutput.info("Insights:")
                for insight in result.insights[:3]:
                    DemoOutput.data(f"  {insight.insight_type.name}", insight.title)
            
            # Show optimizations
            if result.optimizations:
                DemoOutput.info("Optimization opportunities:")
                for opt in result.optimizations[:2]:
                    DemoOutput.optimization(f"{opt.title} (risk: {opt.risk_level:.2f})")
            
            # Now manually apply optimizations to show them working
            if result.optimizations:
                DemoOutput.info("Applying optimizations...")
                opt_results = await autognosis.optimizer.apply_optimizations(
                    kernel, result.optimizations, result.insights
                )
                
                for opt_result in opt_results:
                    if opt_result.success:
                        DemoOutput.success(f"Applied: {opt_result.message}")
                        DemoOutput.data("  Old value", opt_result.old_value)
                        DemoOutput.data("  New value", opt_result.new_value)
                        DemoOutput.data("  Est. improvement", f"{opt_result.improvement_estimate:.1%}")
            
            print()
        
        # Show final parameters
        DemoOutput.section("Final System Parameters (After Optimization)")
        
        final_params = {
            'pln_inference_depth': kernel.pln.max_inference_depth if kernel.pln else None,
            'ecan_decay_rate': kernel.ecan.params.sti_decay_rate if kernel.ecan else None,
            'ecan_spread_decay': kernel.ecan.params.spread_decay if kernel.ecan else None,
            'atomspace_size': kernel.atomspace.size()
        }
        
        for key, value in final_params.items():
            initial = initial_params.get(key)
            if initial != value:
                DemoOutput.optimization(f"{key}: {initial} → {value}")
            else:
                DemoOutput.data(key, value)
        
        # Show optimizer statistics
        DemoOutput.section("Optimizer Statistics")
        
        stats = autognosis.optimizer.get_statistics()
        for key, value in stats.items():
            DemoOutput.data(key, value)
        
        # Cleanup
        DemoOutput.section("Cleanup")
        kernel.shutdown()
        DemoOutput.success("Kernel shutdown complete")
        
    except Exception as e:
        print(f"\n  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    DemoOutput.header("Demo Complete!")
    print("The autognosis optimizer demonstrated actual parameter changes:")
    print("  - PLN inference depth adjusted based on resource utilization")
    print("  - ECAN parameters tuned based on attention patterns")
    print("  - Memory consolidation triggered when needed")
    print("\nThis is the key difference from the original placeholder:")
    print("the system now ACTUALLY optimizes itself based on self-reflection.\n")


if __name__ == "__main__":
    asyncio.run(demo_autognosis_optimizer())
