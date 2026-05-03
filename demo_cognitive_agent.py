#!/usr/bin/env python3
"""
Cognitive Agent Demo
====================

This demo shows how a cognitive kernel can be integrated with an agent framework.
It demonstrates the cognitive capabilities that would enhance any agent:

1. Semantic memory in AtomSpace
2. PLN reasoning for deriving new knowledge
3. ECAN attention allocation
4. Autognosis self-reflection

Run with: python demo_cognitive_agent.py
"""

import asyncio
import sys
import os
from typing import Dict, Any, List, Optional

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# Import cognitive kernel directly
from kernel.cognitive_kernel import CognitiveKernel, KernelConfig, KernelState
from kernel.cognitive.types import AtomType, TruthValue, AttentionValue


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
    def thinking(cls, text: str):
        print(f"  {cls.COLORS['yellow']}🧠 {text}{cls.COLORS['end']}")
    
    @classmethod
    def insight(cls, text: str):
        print(f"  {cls.COLORS['header']}💡 {text}{cls.COLORS['end']}")
    
    @classmethod
    def data(cls, label: str, value):
        print(f"    {cls.COLORS['bold']}{label}:{cls.COLORS['end']} {value}")


class SimpleCognitiveAgent:
    """
    A simplified cognitive agent that demonstrates kernel integration.
    
    In a full implementation, this would inherit from the OpenManus
    ToolCallAgent and integrate cognitive capabilities into think/act.
    """
    
    def __init__(self, kernel: CognitiveKernel):
        self.kernel = kernel
        self.memory: List[Dict[str, str]] = []
    
    def add_to_memory(self, role: str, content: str):
        """Add a message to agent memory."""
        self.memory.append({"role": role, "content": content})
    
    async def cognitive_pre_think(self) -> str:
        """
        Perform cognitive processing before LLM thinking.
        
        This is what makes a CognitiveAgent different from a regular agent:
        it uses the cognitive kernel to enhance its reasoning.
        """
        if not self.kernel or self.kernel.state != KernelState.RUNNING:
            return ""
        
        context_parts = []
        
        # 1. Extract concepts from recent messages
        await self._update_semantic_memory()
        
        # 2. Run PLN inference
        if self.kernel.pln:
            inferences = self._run_quick_inference()
            if inferences:
                context_parts.append(f"**Cognitive Insights:** {inferences}")
        
        # 3. Get attentional focus
        focus = self.kernel.atomspace.get_attentional_focus(limit=5)
        if focus:
            focus_names = [getattr(a, 'name', 'Unknown') for a in focus if hasattr(a, 'name')]
            if focus_names:
                context_parts.append(f"**Current Focus:** {', '.join(focus_names)}")
        
        # 4. Run autognosis if available
        if self.kernel.autognosis:
            try:
                result = await self.kernel.autognosis.run_autognosis_cycle(self.kernel)
                if result.insights:
                    insight_texts = [i.title for i in result.insights[:2]]
                    context_parts.append(f"**Self-Reflection:** {'; '.join(insight_texts)}")
            except Exception as e:
                pass  # Autognosis is optional
        
        return "\n".join(context_parts) if context_parts else ""
    
    async def _update_semantic_memory(self):
        """Extract concepts from recent messages and add to semantic memory."""
        if not self.memory:
            return
        
        # Get last few messages
        recent = self.memory[-3:]
        
        for msg in recent:
            content = msg.get("content", "")
            if not content:
                continue
            
            # Simple concept extraction
            words = content.split()
            for word in words:
                if len(word) > 5 and word.isalpha():
                    existing = self.kernel.atomspace._name_index.get_by_name(word.lower())
                    if not existing:
                        self.kernel.atomspace.add_node(
                            AtomType.CONCEPT_NODE,
                            word.lower(),
                            tv=TruthValue(0.5, 0.3),
                            av=AttentionValue(sti=0.2)
                        )
    
    def _run_quick_inference(self) -> str:
        """Run quick PLN inference and return summary."""
        if not self.kernel.pln:
            return ""
        
        premises = self.kernel.pln.controller.find_deduction_premises()
        if not premises:
            return ""
        
        inferences = []
        for link_ab, link_bc in premises[:3]:
            result = self.kernel.pln.deduction(link_ab, link_bc)
            if result:
                a_atom = self.kernel.atomspace.get_atom(link_ab.outgoing[0])
                c_atom = self.kernel.atomspace.get_atom(link_bc.outgoing[1])
                if a_atom and c_atom:
                    a_name = getattr(a_atom, 'name', 'Unknown')
                    c_name = getattr(c_atom, 'name', 'Unknown')
                    inferences.append(f"{a_name} → {c_name}")
        
        return ", ".join(inferences) if inferences else ""
    
    def get_cognitive_status(self) -> Dict[str, Any]:
        """Get current cognitive status."""
        if not self.kernel:
            return {"status": "no kernel"}
        
        return {
            "kernel_state": self.kernel.state.name,
            "atomspace_size": self.kernel.atomspace.size(),
            "pln_stats": self.kernel.pln.stats if self.kernel.pln else None,
            "ecan_stats": self.kernel.ecan.bank.get_stats() if self.kernel.ecan else None,
        }
    
    async def cleanup(self):
        """Clean up resources."""
        if self.kernel:
            try:
                await self.kernel.stop_advanced_modules()
            except:
                pass
            self.kernel.shutdown()


async def demo_cognitive_agent():
    """Demonstrate the cognitive agent's capabilities."""
    
    DemoOutput.header("Cognitive Agent Demo")
    print("This demo shows how a cognitive kernel enhances agent capabilities.")
    print("The agent uses reasoning, memory, and self-reflection.\n")
    
    try:
        # Create the cognitive kernel
        DemoOutput.section("Creating Cognitive Kernel")
        
        config = KernelConfig(
            kernel_id="cognitive-agent-demo",
            kernel_name="Cognitive Agent Kernel",
            max_atoms=50000,
            attention_budget=100.0,
            max_inference_depth=5,
            log_level="WARNING"
        )
        
        kernel = CognitiveKernel(config)
        if not kernel.boot():
            raise RuntimeError("Failed to boot cognitive kernel")
        
        DemoOutput.success("Cognitive kernel booted!")
        
        # Start advanced modules
        try:
            await kernel.start_advanced_modules()
            DemoOutput.success("Advanced modules initialized")
        except Exception as e:
            DemoOutput.info(f"Running without some advanced modules: {e}")
        
        # Create the agent
        agent = SimpleCognitiveAgent(kernel)
        DemoOutput.success("Cognitive agent created!")
        
        # Show initial status
        status = agent.get_cognitive_status()
        DemoOutput.data("Kernel state", status.get('kernel_state', 'Unknown'))
        DemoOutput.data("AtomSpace size", status.get('atomspace_size', 0))
        
        # Pre-populate knowledge base
        DemoOutput.section("Pre-populating Knowledge Base")
        
        # Add domain concepts
        concepts = [
            "Python", "JavaScript", "Programming Language", "Tool",
            "Data Analysis", "Machine Learning", "Pandas", "NumPy",
            "Python Library", "Software", "Task"
        ]
        
        for name in concepts:
            kernel.atomspace.add_node(
                AtomType.CONCEPT_NODE,
                name,
                tv=TruthValue(1.0, 0.9),
                av=AttentionValue(sti=0.3)
            )
        DemoOutput.success(f"Added {len(concepts)} concepts")
        
        # Add relationships
        relationships = [
            ("Python", "Programming Language"),
            ("JavaScript", "Programming Language"),
            ("Programming Language", "Tool"),
            ("Pandas", "Python Library"),
            ("NumPy", "Python Library"),
            ("Python Library", "Software"),
            ("Software", "Tool"),
            ("Machine Learning", "Task"),
            ("Data Analysis", "Task"),
        ]
        
        for child, parent in relationships:
            child_handles = kernel.atomspace._name_index.get_by_name(child)
            parent_handles = kernel.atomspace._name_index.get_by_name(parent)
            
            if child_handles and parent_handles:
                kernel.atomspace.add_link(
                    AtomType.INHERITANCE_LINK,
                    [list(child_handles)[0], list(parent_handles)[0]],
                    tv=TruthValue(1.0, 0.9)
                )
                DemoOutput.thinking(f"Learned: {child} IS-A {parent}")
        
        # Simulate agent receiving a task
        DemoOutput.section("Simulating Agent Task")
        
        agent.add_to_memory("user", "I need to analyze some data using Python and machine learning")
        DemoOutput.info("User request: 'I need to analyze some data using Python and machine learning'")
        
        # Run cognitive pre-think
        DemoOutput.section("Cognitive Pre-Think Phase")
        DemoOutput.info("Before the LLM thinks, the cognitive kernel processes...")
        
        context = await agent.cognitive_pre_think()
        
        if context:
            DemoOutput.success("Cognitive context generated for LLM:")
            for line in context.split('\n'):
                if line.strip():
                    DemoOutput.insight(line)
        else:
            DemoOutput.info("Minimal cognitive context (expected with limited knowledge)")
        
        # Run explicit PLN inference
        DemoOutput.section("PLN Reasoning")
        
        if kernel.pln:
            premises = kernel.pln.controller.find_deduction_premises()
            DemoOutput.data("Deduction opportunities found", len(premises))
            
            inferences_made = 0
            for link_ab, link_bc in premises[:10]:
                result = kernel.pln.deduction(link_ab, link_bc)
                if result:
                    inferences_made += 1
                    a_atom = kernel.atomspace.get_atom(link_ab.outgoing[0])
                    c_atom = kernel.atomspace.get_atom(link_bc.outgoing[1])
                    if a_atom and c_atom:
                        a_name = getattr(a_atom, 'name', 'Unknown')
                        c_name = getattr(c_atom, 'name', 'Unknown')
                        DemoOutput.thinking(f"Inferred: {a_name} → {c_name}")
            
            DemoOutput.success(f"Made {inferences_made} new inferences")
        
        # Focus attention
        DemoOutput.section("Attention Allocation")
        
        # Stimulate attention on relevant concepts
        for concept in ["Python", "Machine Learning", "Data Analysis"]:
            handles = kernel.atomspace._name_index.get_by_name(concept)
            if handles:
                handle = list(handles)[0]
                atom = kernel.atomspace.get_atom(handle)
                if atom:
                    new_av = atom.attention_value.stimulate(0.4)
                    kernel.atomspace.set_attention_value(handle, new_av)
                    DemoOutput.thinking(f"Focused attention on '{concept}'")
        
        # Spread attention
        if kernel.ecan:
            kernel.ecan.spread_attention()
            DemoOutput.success("Attention spread through semantic network")
        
        # Show attentional focus
        focus = kernel.atomspace.get_attentional_focus(limit=5)
        DemoOutput.info("Current attentional focus:")
        for atom in focus:
            name = getattr(atom, 'name', f"Link:{atom.atom_type.name}")
            DemoOutput.data(f"  {name}", f"STI: {atom.attention_value.sti:.3f}")
        
        # Run autognosis
        DemoOutput.section("Self-Reflection (Autognosis)")
        
        if kernel.autognosis:
            try:
                result = await kernel.autognosis.run_autognosis_cycle(kernel)
                DemoOutput.success(f"Self-awareness score: {result.self_awareness_score:.2f}")
                
                if result.insights:
                    DemoOutput.info("Meta-cognitive insights:")
                    for insight in result.insights[:3]:
                        DemoOutput.insight(f"{insight.title}")
                
                if result.optimizations:
                    DemoOutput.info("Optimization opportunities:")
                    for opt in result.optimizations[:2]:
                        DemoOutput.thinking(f"{opt.title} (improvement: {opt.expected_improvement:.0%})")
            except Exception as e:
                DemoOutput.info(f"Autognosis limited: {e}")
        
        # Final status
        DemoOutput.section("Final Cognitive Status")
        status = agent.get_cognitive_status()
        DemoOutput.data("Kernel state", status.get('kernel_state', 'Unknown'))
        DemoOutput.data("AtomSpace size", status.get('atomspace_size', 0))
        
        if status.get('pln_stats'):
            DemoOutput.data("Total PLN inferences", status['pln_stats'].get('total_inferences', 0))
            DemoOutput.data("New atoms created", status['pln_stats'].get('new_atoms_created', 0))
        
        # Cleanup
        DemoOutput.section("Cleanup")
        await agent.cleanup()
        DemoOutput.success("Agent cleaned up")
        
    except Exception as e:
        print(f"\n  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    DemoOutput.header("Demo Complete!")
    print("This demonstrates how cognitive capabilities enhance agents:")
    print("  - Semantic memory stores and retrieves knowledge")
    print("  - PLN reasoning derives new insights")
    print("  - ECAN attention focuses on relevant concepts")
    print("  - Autognosis reflects on performance")
    print("\nIn a full integration, these would enhance the agent's")
    print("think() and act() methods for more intelligent behavior.\n")


if __name__ == "__main__":
    asyncio.run(demo_cognitive_agent())
