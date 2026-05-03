"""
Cognitive Agent - Integration of Cognitive Kernel with OpenManus Agent Framework
================================================================================

This module bridges the cognitive kernel's reasoning, attention, and learning
capabilities with the OpenManus agent framework. The CognitiveAgent doesn't
just execute tools - it THINKS about what to do using:

1. PLN reasoning to derive new knowledge and make inferences
2. ECAN attention to focus on relevant concepts
3. Autognosis to reflect on its own performance
4. AtomSpace to maintain persistent semantic memory

The cognitive kernel acts as the "brain" that guides the agent's decisions.
"""

from __future__ import annotations
import asyncio
import json
import sys
import os
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from pydantic import Field, model_validator

# Add project root to path for kernel imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

from app.agent.toolcall import ToolCallAgent
from app.logger import logger
from app.schema import AgentState, Message, ToolCall
from app.tool import Terminate, ToolCollection
from app.tool.python_execute import PythonExecute
from app.tool.str_replace_editor import StrReplaceEditor

# Import cognitive kernel components
from kernel.cognitive_kernel import CognitiveKernel, KernelConfig, KernelState
from kernel.cognitive.types import AtomType, TruthValue, AttentionValue, AtomHandle


# =============================================================================
# COGNITIVE PROMPTS
# =============================================================================

COGNITIVE_SYSTEM_PROMPT = """You are a cognitive agent with an integrated reasoning engine.

Unlike typical LLM agents, you have access to a cognitive kernel that provides:
- **Semantic Memory**: Knowledge stored in an AtomSpace hypergraph
- **PLN Reasoning**: Probabilistic logic for deriving new knowledge
- **Attention Allocation**: Economic attention networks (ECAN) for focus
- **Self-Reflection**: Autognosis for monitoring your own performance

When processing tasks:
1. First, query your semantic memory for relevant knowledge
2. Use PLN reasoning to derive new insights
3. Focus attention on the most relevant concepts
4. Execute tools based on reasoned decisions
5. Learn from outcomes to improve future performance

Your cognitive state is continuously updated. Use the cognitive tools to:
- Store important concepts and relationships
- Query existing knowledge
- Reason about relationships between concepts
- Focus attention on relevant information
"""

COGNITIVE_NEXT_STEP_PROMPT = """Based on your cognitive state and the current task, determine the next action.

Consider:
1. What knowledge do you have about this task?
2. What can you infer from existing knowledge?
3. What concepts should you focus attention on?
4. What tool would best advance the task?

Think step by step, then select the appropriate tool.
"""


# =============================================================================
# COGNITIVE TOOLS
# =============================================================================

class CognitiveQueryTool:
    """Tool for querying the cognitive kernel's semantic memory."""
    
    name: str = "cognitive_query"
    description: str = """Query the cognitive kernel's semantic memory.
    
    Use this to:
    - Find concepts related to a topic
    - Retrieve relationships between concepts
    - Get the current attentional focus
    
    Arguments:
    - query_type: One of "concept", "relationships", "focus", "infer"
    - concept: The concept name to query (for concept/relationships)
    """
    
    def __init__(self, kernel: CognitiveKernel):
        self.kernel = kernel
    
    async def execute(self, query_type: str, concept: str = None) -> str:
        """Execute a cognitive query."""
        if query_type == "concept":
            return self._query_concept(concept)
        elif query_type == "relationships":
            return self._query_relationships(concept)
        elif query_type == "focus":
            return self._query_focus()
        elif query_type == "infer":
            return self._run_inference()
        else:
            return f"Unknown query type: {query_type}"
    
    def _query_concept(self, concept: str) -> str:
        """Query information about a concept."""
        if not concept:
            return "Error: concept name required"
        
        atoms = self.kernel.atomspace.get_atoms_by_name(concept)
        if not atoms:
            return f"No knowledge found about '{concept}'"
        
        results = []
        for atom in atoms:
            results.append(f"- {atom.name} (type: {atom.atom_type.name}, "
                          f"strength: {atom.truth_value.strength:.2f}, "
                          f"confidence: {atom.truth_value.confidence:.2f})")
        
        return f"Knowledge about '{concept}':\n" + "\n".join(results)
    
    def _query_relationships(self, concept: str) -> str:
        """Query relationships involving a concept."""
        if not concept:
            return "Error: concept name required"
        
        handles = self.kernel.atomspace._name_index.get_by_name(concept)
        if not handles:
            return f"No concept '{concept}' found"
        
        results = []
        for handle in handles:
            # Get incoming links (relationships where this concept is involved)
            links = self.kernel.atomspace.get_incoming(handle)
            for link in links:
                if link.atom_type == AtomType.INHERITANCE_LINK:
                    outgoing = self.kernel.atomspace.get_outgoing(link.handle)
                    if len(outgoing) >= 2:
                        child = outgoing[0]
                        parent = outgoing[1]
                        child_name = getattr(child, 'name', 'Unknown')
                        parent_name = getattr(parent, 'name', 'Unknown')
                        results.append(f"- {child_name} IS-A {parent_name} "
                                      f"(strength: {link.truth_value.strength:.2f})")
        
        if not results:
            return f"No relationships found for '{concept}'"
        
        return f"Relationships involving '{concept}':\n" + "\n".join(results)
    
    def _query_focus(self) -> str:
        """Query current attentional focus."""
        focus = self.kernel.atomspace.get_attentional_focus(limit=10)
        if not focus:
            return "No concepts currently in attentional focus"
        
        results = []
        for atom in focus:
            name = getattr(atom, 'name', f"Link:{atom.atom_type.name}")
            results.append(f"- {name} (STI: {atom.attention_value.sti:.3f})")
        
        return "Current attentional focus:\n" + "\n".join(results)
    
    def _run_inference(self) -> str:
        """Run PLN inference and report new knowledge."""
        if not self.kernel.pln:
            return "PLN engine not available"
        
        # Find deduction opportunities
        premises = self.kernel.pln.controller.find_deduction_premises()
        if not premises:
            return "No inference opportunities found"
        
        # Perform inferences
        inferences = []
        for link_ab, link_bc in premises[:5]:  # Limit to 5
            result = self.kernel.pln.deduction(link_ab, link_bc)
            if result:
                a_atom = self.kernel.atomspace.get_atom(link_ab.outgoing[0])
                c_atom = self.kernel.atomspace.get_atom(link_bc.outgoing[1])
                if a_atom and c_atom:
                    a_name = getattr(a_atom, 'name', 'Unknown')
                    c_name = getattr(c_atom, 'name', 'Unknown')
                    inferences.append(f"- Inferred: {a_name} → {c_name} "
                                     f"(strength: {result.truth_value.strength:.2f})")
        
        if not inferences:
            return "No new inferences could be made"
        
        return "PLN Inferences:\n" + "\n".join(inferences)


class CognitiveLearnTool:
    """Tool for teaching the cognitive kernel new knowledge."""
    
    name: str = "cognitive_learn"
    description: str = """Teach the cognitive kernel new knowledge.
    
    Use this to:
    - Add new concepts to semantic memory
    - Create relationships between concepts
    - Strengthen existing beliefs with new evidence
    
    Arguments:
    - action: One of "concept", "relationship", "strengthen"
    - concept1: First concept name
    - concept2: Second concept name (for relationships)
    - relation_type: Type of relationship (default: "inheritance")
    - strength: Belief strength 0-1 (default: 0.9)
    """
    
    def __init__(self, kernel: CognitiveKernel):
        self.kernel = kernel
    
    async def execute(
        self,
        action: str,
        concept1: str,
        concept2: str = None,
        relation_type: str = "inheritance",
        strength: float = 0.9
    ) -> str:
        """Execute a learning action."""
        if action == "concept":
            return self._add_concept(concept1, strength)
        elif action == "relationship":
            return self._add_relationship(concept1, concept2, relation_type, strength)
        elif action == "strengthen":
            return self._strengthen_belief(concept1, concept2, strength)
        else:
            return f"Unknown action: {action}"
    
    def _add_concept(self, name: str, strength: float) -> str:
        """Add a new concept to semantic memory."""
        handle = self.kernel.atomspace.add_node(
            AtomType.CONCEPT_NODE,
            name,
            tv=TruthValue(strength, 0.9),
            av=AttentionValue(sti=0.5)
        )
        if handle:
            return f"Added concept '{name}' to semantic memory"
        return f"Failed to add concept '{name}'"
    
    def _add_relationship(
        self,
        child: str,
        parent: str,
        relation_type: str,
        strength: float
    ) -> str:
        """Add a relationship between concepts."""
        if not parent:
            return "Error: parent concept required for relationship"
        
        # Get or create concept handles
        child_handles = self.kernel.atomspace._name_index.get_by_name(child)
        parent_handles = self.kernel.atomspace._name_index.get_by_name(parent)
        
        if not child_handles:
            child_handle = self.kernel.atomspace.add_node(
                AtomType.CONCEPT_NODE, child, tv=TruthValue(1.0, 0.9)
            )
        else:
            child_handle = list(child_handles)[0]
        
        if not parent_handles:
            parent_handle = self.kernel.atomspace.add_node(
                AtomType.CONCEPT_NODE, parent, tv=TruthValue(1.0, 0.9)
            )
        else:
            parent_handle = list(parent_handles)[0]
        
        # Determine link type
        link_type = AtomType.INHERITANCE_LINK
        if relation_type == "similarity":
            link_type = AtomType.SIMILARITY_LINK
        elif relation_type == "implication":
            link_type = AtomType.IMPLICATION_LINK
        
        # Create the link
        link_handle = self.kernel.atomspace.add_link(
            link_type,
            [child_handle, parent_handle],
            tv=TruthValue(strength, 0.8)
        )
        
        if link_handle:
            return f"Added relationship: {child} {relation_type} {parent} (strength: {strength})"
        return f"Failed to add relationship"
    
    def _strengthen_belief(self, concept1: str, concept2: str, strength: float) -> str:
        """Strengthen an existing belief with new evidence."""
        if not concept2:
            return "Error: both concepts required for strengthening"
        
        # Find existing link
        c1_handles = self.kernel.atomspace._name_index.get_by_name(concept1)
        c2_handles = self.kernel.atomspace._name_index.get_by_name(concept2)
        
        if not c1_handles or not c2_handles:
            return f"Concepts not found: {concept1}, {concept2}"
        
        c1_handle = list(c1_handles)[0]
        c2_handle = list(c2_handles)[0]
        
        # Find the link
        existing = self.kernel.atomspace.match_pattern(
            AtomType.INHERITANCE_LINK,
            [c1_handle, c2_handle]
        )
        
        if existing:
            link = existing[0]
            new_tv = TruthValue(strength, 0.9)
            self.kernel.atomspace.merge_truth_value(link.handle, new_tv)
            return f"Strengthened belief: {concept1} → {concept2}"
        
        return f"No existing relationship found between {concept1} and {concept2}"


class CognitiveAttentionTool:
    """Tool for managing cognitive attention."""
    
    name: str = "cognitive_attention"
    description: str = """Manage cognitive attention allocation.
    
    Use this to:
    - Focus attention on specific concepts
    - Spread attention through related concepts
    - Get current attention distribution
    
    Arguments:
    - action: One of "focus", "spread", "status"
    - concept: Concept to focus on (for focus action)
    - amount: Attention amount 0-1 (default: 0.5)
    """
    
    def __init__(self, kernel: CognitiveKernel):
        self.kernel = kernel
    
    async def execute(
        self,
        action: str,
        concept: str = None,
        amount: float = 0.5
    ) -> str:
        """Execute an attention action."""
        if action == "focus":
            return self._focus_attention(concept, amount)
        elif action == "spread":
            return self._spread_attention()
        elif action == "status":
            return self._attention_status()
        else:
            return f"Unknown action: {action}"
    
    def _focus_attention(self, concept: str, amount: float) -> str:
        """Focus attention on a concept."""
        if not concept:
            return "Error: concept required for focus"
        
        handles = self.kernel.atomspace._name_index.get_by_name(concept)
        if not handles:
            return f"Concept '{concept}' not found"
        
        handle = list(handles)[0]
        atom = self.kernel.atomspace.get_atom(handle)
        if atom:
            new_av = atom.attention_value.stimulate(amount)
            self.kernel.atomspace.set_attention_value(handle, new_av)
            return f"Focused attention on '{concept}' (new STI: {new_av.sti:.3f})"
        
        return f"Failed to focus attention on '{concept}'"
    
    def _spread_attention(self) -> str:
        """Spread attention through the network."""
        if self.kernel.ecan:
            self.kernel.ecan.spread_attention()
            return "Attention spread through semantic network"
        return "ECAN not available"
    
    def _attention_status(self) -> str:
        """Get attention status."""
        if not self.kernel.ecan:
            return "ECAN not available"
        
        stats = self.kernel.ecan.bank.get_stats()
        focus = self.kernel.atomspace.get_attentional_focus(limit=5)
        
        result = [
            "Attention Status:",
            f"- Total STI: {stats.get('total_sti', 0):.2f}",
            f"- Stimulus pool: {stats.get('stimulus_pool', 0):.2f}",
            f"- Cycles: {stats.get('cycles', 0)}",
            "",
            "Top focus atoms:"
        ]
        
        for atom in focus:
            name = getattr(atom, 'name', f"Link:{atom.atom_type.name}")
            result.append(f"  - {name}: {atom.attention_value.sti:.3f}")
        
        return "\n".join(result)


# =============================================================================
# COGNITIVE AGENT
# =============================================================================

class CognitiveAgent(ToolCallAgent):
    """
    An agent with integrated cognitive capabilities.
    
    This agent uses a cognitive kernel for:
    - Semantic memory (AtomSpace)
    - Probabilistic reasoning (PLN)
    - Attention allocation (ECAN)
    - Self-reflection (Autognosis)
    
    The cognitive kernel acts as the agent's "brain", providing
    reasoning and memory capabilities beyond simple tool execution.
    """
    
    name: str = "CognitiveAgent"
    description: str = "An agent with cognitive reasoning, semantic memory, and self-reflection capabilities"
    
    system_prompt: str = COGNITIVE_SYSTEM_PROMPT
    next_step_prompt: str = COGNITIVE_NEXT_STEP_PROMPT
    
    max_steps: int = 20
    max_observe: int = 10000
    
    # Cognitive kernel
    kernel: Optional[CognitiveKernel] = None
    kernel_config: KernelConfig = Field(default_factory=lambda: KernelConfig(
        kernel_id="cognitive-agent",
        kernel_name="Cognitive Agent Kernel",
        max_atoms=50000,
        attention_budget=100.0,
        max_inference_depth=5
    ))
    
    # Cognitive tools (initialized after kernel)
    _cognitive_tools_initialized: bool = False
    
    class Config:
        arbitrary_types_allowed = True
        extra = "allow"
    
    @model_validator(mode="after")
    def initialize_kernel(self) -> "CognitiveAgent":
        """Initialize the cognitive kernel."""
        if self.kernel is None:
            self.kernel = CognitiveKernel(self.kernel_config)
            if not self.kernel.boot():
                logger.error("Failed to boot cognitive kernel")
        return self
    
    async def initialize_cognitive_tools(self):
        """Initialize cognitive tools after kernel is ready."""
        if self._cognitive_tools_initialized:
            return
        
        if self.kernel and self.kernel.state == KernelState.RUNNING:
            # Start advanced modules
            try:
                await self.kernel.start_advanced_modules()
            except Exception as e:
                logger.warning(f"Could not start advanced modules: {e}")
            
            # Add cognitive tools
            # Note: In a full implementation, these would be proper Tool subclasses
            # For now, we'll integrate cognitive capabilities directly into think/act
            
            self._cognitive_tools_initialized = True
            logger.info("Cognitive tools initialized")
    
    async def think(self) -> bool:
        """
        Enhanced thinking with cognitive capabilities.
        
        Before standard LLM-based thinking, the cognitive agent:
        1. Updates its semantic memory with recent context
        2. Runs PLN inference to derive new knowledge
        3. Adjusts attention based on task relevance
        4. Incorporates cognitive insights into the prompt
        """
        # Ensure cognitive tools are initialized
        await self.initialize_cognitive_tools()
        
        # Pre-think cognitive processing
        cognitive_context = await self._cognitive_pre_think()
        
        # Enhance the next step prompt with cognitive context
        original_prompt = self.next_step_prompt
        if cognitive_context:
            self.next_step_prompt = f"{cognitive_context}\n\n{self.next_step_prompt}"
        
        # Standard LLM thinking
        result = await super().think()
        
        # Restore original prompt
        self.next_step_prompt = original_prompt
        
        return result
    
    async def _cognitive_pre_think(self) -> str:
        """
        Perform cognitive processing before LLM thinking.
        
        Returns context string to enhance the prompt.
        """
        if not self.kernel or self.kernel.state != KernelState.RUNNING:
            return ""
        
        context_parts = []
        
        # 1. Extract concepts from recent messages and add to memory
        await self._update_semantic_memory()
        
        # 2. Run PLN inference
        if self.kernel.pln:
            inferences = self._run_quick_inference()
            if inferences:
                context_parts.append(f"**Cognitive Insights:**\n{inferences}")
        
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
                logger.debug(f"Autognosis error: {e}")
        
        return "\n".join(context_parts) if context_parts else ""
    
    async def _update_semantic_memory(self):
        """Extract concepts from recent messages and add to semantic memory."""
        if not self.memory.messages:
            return
        
        # Get last few messages
        recent = self.memory.messages[-3:]
        
        for msg in recent:
            if not msg.content:
                continue
            
            # Simple concept extraction (in production, use NLP)
            # For now, just add message content as a context node
            words = msg.content.split()
            # Add significant words as concepts (simplified)
            for word in words:
                if len(word) > 5 and word.isalpha():
                    # Check if already exists
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
    
    async def act(self) -> str:
        """
        Enhanced action with cognitive post-processing.
        
        After executing tools, the cognitive agent:
        1. Updates semantic memory with results
        2. Adjusts attention based on outcomes
        3. Learns from the action (Hebbian learning)
        """
        # Standard tool execution
        result = await super().act()
        
        # Post-act cognitive processing
        await self._cognitive_post_act(result)
        
        return result
    
    async def _cognitive_post_act(self, result: str):
        """Perform cognitive processing after action execution."""
        if not self.kernel or self.kernel.state != KernelState.RUNNING:
            return
        
        # 1. Learn from the action (Hebbian learning)
        if self.kernel.hebbian:
            # Strengthen associations between recently used concepts
            focus = self.kernel.atomspace.get_attentional_focus(limit=5)
            for i, atom1 in enumerate(focus):
                for atom2 in focus[i+1:]:
                    self.kernel.hebbian.learn_association(
                        atom1.handle,
                        atom2.handle,
                        strength=0.5
                    )
        
        # 2. Decay attention
        if self.kernel.ecan:
            self.kernel.ecan.decay_attention()
        
        # 3. Add action result to memory (simplified)
        if "success" in result.lower() or "completed" in result.lower():
            # Positive outcome - could reinforce relevant concepts
            pass
    
    async def cleanup(self):
        """Clean up cognitive agent resources."""
        # Shutdown cognitive kernel
        if self.kernel:
            try:
                await self.kernel.stop_advanced_modules()
            except:
                pass
            self.kernel.shutdown()
        
        # Standard cleanup
        await super().cleanup()
    
    def get_cognitive_status(self) -> Dict[str, Any]:
        """Get current cognitive status for debugging/monitoring."""
        if not self.kernel:
            return {"status": "no kernel"}
        
        return {
            "kernel_state": self.kernel.state.name,
            "atomspace_size": self.kernel.atomspace.size(),
            "pln_stats": self.kernel.pln.stats if self.kernel.pln else None,
            "ecan_stats": self.kernel.ecan.bank.get_stats() if self.kernel.ecan else None,
        }


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

async def create_cognitive_agent(**kwargs) -> CognitiveAgent:
    """Factory function to create a properly initialized CognitiveAgent."""
    agent = CognitiveAgent(**kwargs)
    await agent.initialize_cognitive_tools()
    return agent


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    'CognitiveAgent',
    'create_cognitive_agent',
    'CognitiveQueryTool',
    'CognitiveLearnTool',
    'CognitiveAttentionTool',
]
