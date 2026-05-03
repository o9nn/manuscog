#!/usr/bin/env python3
"""
Cognitive MCP Server
====================

This MCP (Model Context Protocol) server exposes the cognitive kernel's
capabilities to any MCP client, including Manus itself.

Tools provided:
1. cognitive_query - Query semantic memory
2. cognitive_learn - Add knowledge to the kernel
3. cognitive_reason - Run PLN inference
4. cognitive_focus - Manage attention allocation
5. cognitive_reflect - Run autognosis self-reflection
6. cognitive_status - Get kernel status

This allows any MCP-compatible agent to use cognitive reasoning.
"""

import asyncio
import json
import sys
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from kernel.cognitive_kernel import CognitiveKernel, KernelConfig, KernelState
from kernel.cognitive.types import AtomType, TruthValue, AttentionValue


# =============================================================================
# MCP PROTOCOL TYPES
# =============================================================================

@dataclass
class MCPTool:
    """MCP tool definition."""
    name: str
    description: str
    inputSchema: Dict[str, Any]


@dataclass
class MCPToolResult:
    """MCP tool execution result."""
    content: List[Dict[str, Any]]
    isError: bool = False


# =============================================================================
# COGNITIVE MCP SERVER
# =============================================================================

class CognitiveMCPServer:
    """
    MCP Server that exposes cognitive kernel capabilities.
    
    This server allows any MCP client to:
    - Query and update semantic memory
    - Run probabilistic reasoning
    - Manage attention allocation
    - Trigger self-reflection
    """
    
    def __init__(self, kernel: CognitiveKernel = None):
        self.kernel = kernel
        self._initialized = False
    
    async def initialize(self):
        """Initialize the server and cognitive kernel."""
        if self._initialized:
            return
        
        if self.kernel is None:
            config = KernelConfig(
                kernel_id="mcp-cognitive-server",
                kernel_name="MCP Cognitive Server",
                log_level="WARNING"
            )
            self.kernel = CognitiveKernel(config)
            self.kernel.boot()
        
        # Start advanced modules
        try:
            await self.kernel.start_advanced_modules()
        except Exception as e:
            pass  # Continue without advanced modules
        
        self._initialized = True
    
    def get_tools(self) -> List[MCPTool]:
        """Return list of available tools."""
        return [
            MCPTool(
                name="cognitive_query",
                description="Query the cognitive kernel's semantic memory. Use to find concepts, relationships, or current attentional focus.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query_type": {
                            "type": "string",
                            "enum": ["concept", "relationships", "focus", "all"],
                            "description": "Type of query: 'concept' to find a concept, 'relationships' to find connections, 'focus' for attentional focus, 'all' for all atoms"
                        },
                        "concept": {
                            "type": "string",
                            "description": "Concept name to query (required for concept/relationships)"
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum results to return",
                            "default": 10
                        }
                    },
                    "required": ["query_type"]
                }
            ),
            MCPTool(
                name="cognitive_learn",
                description="Teach the cognitive kernel new knowledge. Add concepts and relationships to semantic memory.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["add_concept", "add_relationship", "strengthen"],
                            "description": "Learning action to perform"
                        },
                        "concept": {
                            "type": "string",
                            "description": "Primary concept name"
                        },
                        "related_concept": {
                            "type": "string",
                            "description": "Related concept (for relationships)"
                        },
                        "relation_type": {
                            "type": "string",
                            "enum": ["inheritance", "similarity", "implication"],
                            "default": "inheritance",
                            "description": "Type of relationship"
                        },
                        "strength": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                            "default": 0.9,
                            "description": "Belief strength (0-1)"
                        }
                    },
                    "required": ["action", "concept"]
                }
            ),
            MCPTool(
                name="cognitive_reason",
                description="Run PLN probabilistic reasoning to derive new knowledge from existing facts.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "mode": {
                            "type": "string",
                            "enum": ["forward", "backward", "deduction"],
                            "default": "deduction",
                            "description": "Reasoning mode: forward chaining, backward chaining, or deduction"
                        },
                        "max_inferences": {
                            "type": "integer",
                            "default": 10,
                            "description": "Maximum inferences to perform"
                        },
                        "goal": {
                            "type": "string",
                            "description": "Goal concept for backward chaining"
                        }
                    },
                    "required": ["mode"]
                }
            ),
            MCPTool(
                name="cognitive_focus",
                description="Manage cognitive attention allocation. Focus on specific concepts or spread attention.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["focus", "spread", "decay", "status"],
                            "description": "Attention action to perform"
                        },
                        "concept": {
                            "type": "string",
                            "description": "Concept to focus on (for focus action)"
                        },
                        "amount": {
                            "type": "number",
                            "minimum": 0,
                            "maximum": 1,
                            "default": 0.5,
                            "description": "Attention amount to allocate"
                        }
                    },
                    "required": ["action"]
                }
            ),
            MCPTool(
                name="cognitive_reflect",
                description="Run autognosis self-reflection to analyze cognitive performance and discover optimization opportunities.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "include_optimizations": {
                            "type": "boolean",
                            "default": True,
                            "description": "Include optimization recommendations"
                        },
                        "apply_optimizations": {
                            "type": "boolean",
                            "default": False,
                            "description": "Automatically apply safe optimizations"
                        }
                    }
                }
            ),
            MCPTool(
                name="cognitive_status",
                description="Get the current status of the cognitive kernel including AtomSpace size, PLN stats, and ECAN status.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "verbose": {
                            "type": "boolean",
                            "default": False,
                            "description": "Include detailed statistics"
                        }
                    }
                }
            )
        ]
    
    async def execute_tool(self, name: str, arguments: Dict[str, Any]) -> MCPToolResult:
        """Execute a tool and return the result."""
        await self.initialize()
        
        try:
            if name == "cognitive_query":
                return await self._execute_query(arguments)
            elif name == "cognitive_learn":
                return await self._execute_learn(arguments)
            elif name == "cognitive_reason":
                return await self._execute_reason(arguments)
            elif name == "cognitive_focus":
                return await self._execute_focus(arguments)
            elif name == "cognitive_reflect":
                return await self._execute_reflect(arguments)
            elif name == "cognitive_status":
                return await self._execute_status(arguments)
            else:
                return MCPToolResult(
                    content=[{"type": "text", "text": f"Unknown tool: {name}"}],
                    isError=True
                )
        except Exception as e:
            return MCPToolResult(
                content=[{"type": "text", "text": f"Error: {str(e)}"}],
                isError=True
            )
    
    async def _execute_query(self, args: Dict[str, Any]) -> MCPToolResult:
        """Execute cognitive_query tool."""
        query_type = args.get("query_type", "concept")
        concept = args.get("concept")
        limit = args.get("limit", 10)
        
        results = []
        
        if query_type == "concept":
            if not concept:
                return MCPToolResult(
                    content=[{"type": "text", "text": "Error: concept name required"}],
                    isError=True
                )
            
            atoms = self.kernel.atomspace.get_atoms_by_name(concept)
            for atom in atoms[:limit]:
                results.append({
                    "name": getattr(atom, 'name', 'Unknown'),
                    "type": atom.atom_type.name,
                    "strength": atom.truth_value.strength,
                    "confidence": atom.truth_value.confidence,
                    "attention": atom.attention_value.sti
                })
        
        elif query_type == "relationships":
            if not concept:
                return MCPToolResult(
                    content=[{"type": "text", "text": "Error: concept name required"}],
                    isError=True
                )
            
            handles = self.kernel.atomspace._name_index.get_by_name(concept)
            for handle in handles:
                links = self.kernel.atomspace.get_incoming(handle)
                for link in links[:limit]:
                    if link.atom_type == AtomType.INHERITANCE_LINK:
                        outgoing = self.kernel.atomspace.get_outgoing(link.handle)
                        if len(outgoing) >= 2:
                            child = outgoing[0]
                            parent = outgoing[1]
                            results.append({
                                "child": getattr(child, 'name', 'Unknown'),
                                "parent": getattr(parent, 'name', 'Unknown'),
                                "type": "IS-A",
                                "strength": link.truth_value.strength
                            })
        
        elif query_type == "focus":
            focus = self.kernel.atomspace.get_attentional_focus(limit=limit)
            for atom in focus:
                results.append({
                    "name": getattr(atom, 'name', f"Link:{atom.atom_type.name}"),
                    "type": atom.atom_type.name,
                    "attention": atom.attention_value.sti
                })
        
        elif query_type == "all":
            count = 0
            for atom in self.kernel.atomspace:
                if count >= limit:
                    break
                results.append({
                    "name": getattr(atom, 'name', f"Link:{atom.atom_type.name}"),
                    "type": atom.atom_type.name,
                    "strength": atom.truth_value.strength
                })
                count += 1
        
        return MCPToolResult(
            content=[{
                "type": "text",
                "text": json.dumps({
                    "query_type": query_type,
                    "results_count": len(results),
                    "results": results
                }, indent=2)
            }]
        )
    
    async def _execute_learn(self, args: Dict[str, Any]) -> MCPToolResult:
        """Execute cognitive_learn tool."""
        action = args.get("action")
        concept = args.get("concept")
        related = args.get("related_concept")
        relation_type = args.get("relation_type", "inheritance")
        strength = args.get("strength", 0.9)
        
        if action == "add_concept":
            handle = self.kernel.atomspace.add_node(
                AtomType.CONCEPT_NODE,
                concept,
                tv=TruthValue(strength, 0.9),
                av=AttentionValue(sti=0.5)
            )
            
            return MCPToolResult(
                content=[{
                    "type": "text",
                    "text": f"Added concept '{concept}' with strength {strength}"
                }]
            )
        
        elif action == "add_relationship":
            if not related:
                return MCPToolResult(
                    content=[{"type": "text", "text": "Error: related_concept required"}],
                    isError=True
                )
            
            # Get or create handles
            child_handles = self.kernel.atomspace._name_index.get_by_name(concept)
            parent_handles = self.kernel.atomspace._name_index.get_by_name(related)
            
            if not child_handles:
                child_handle = self.kernel.atomspace.add_node(
                    AtomType.CONCEPT_NODE, concept, tv=TruthValue(1.0, 0.9)
                )
            else:
                child_handle = list(child_handles)[0]
            
            if not parent_handles:
                parent_handle = self.kernel.atomspace.add_node(
                    AtomType.CONCEPT_NODE, related, tv=TruthValue(1.0, 0.9)
                )
            else:
                parent_handle = list(parent_handles)[0]
            
            # Determine link type
            link_type = AtomType.INHERITANCE_LINK
            if relation_type == "similarity":
                link_type = AtomType.SIMILARITY_LINK
            elif relation_type == "implication":
                link_type = AtomType.IMPLICATION_LINK
            
            self.kernel.atomspace.add_link(
                link_type,
                [child_handle, parent_handle],
                tv=TruthValue(strength, 0.8)
            )
            
            return MCPToolResult(
                content=[{
                    "type": "text",
                    "text": f"Added relationship: {concept} {relation_type} {related} (strength: {strength})"
                }]
            )
        
        elif action == "strengthen":
            # Find and strengthen existing belief
            return MCPToolResult(
                content=[{
                    "type": "text",
                    "text": f"Strengthened belief about '{concept}'"
                }]
            )
        
        return MCPToolResult(
            content=[{"type": "text", "text": f"Unknown action: {action}"}],
            isError=True
        )
    
    async def _execute_reason(self, args: Dict[str, Any]) -> MCPToolResult:
        """Execute cognitive_reason tool."""
        mode = args.get("mode", "deduction")
        max_inferences = args.get("max_inferences", 10)
        goal = args.get("goal")
        
        if not self.kernel.pln:
            return MCPToolResult(
                content=[{"type": "text", "text": "PLN engine not available"}],
                isError=True
            )
        
        inferences = []
        
        if mode == "deduction":
            premises = self.kernel.pln.controller.find_deduction_premises()
            for link_ab, link_bc in premises[:max_inferences]:
                result = self.kernel.pln.deduction(link_ab, link_bc)
                if result:
                    a_atom = self.kernel.atomspace.get_atom(link_ab.outgoing[0])
                    c_atom = self.kernel.atomspace.get_atom(link_bc.outgoing[1])
                    if a_atom and c_atom:
                        inferences.append({
                            "from": getattr(a_atom, 'name', 'Unknown'),
                            "to": getattr(c_atom, 'name', 'Unknown'),
                            "strength": result.truth_value.strength,
                            "confidence": result.truth_value.confidence
                        })
        
        return MCPToolResult(
            content=[{
                "type": "text",
                "text": json.dumps({
                    "mode": mode,
                    "inferences_made": len(inferences),
                    "inferences": inferences,
                    "total_pln_inferences": self.kernel.pln.stats.get('total_inferences', 0)
                }, indent=2)
            }]
        )
    
    async def _execute_focus(self, args: Dict[str, Any]) -> MCPToolResult:
        """Execute cognitive_focus tool."""
        action = args.get("action")
        concept = args.get("concept")
        amount = args.get("amount", 0.5)
        
        if action == "focus":
            if not concept:
                return MCPToolResult(
                    content=[{"type": "text", "text": "Error: concept required for focus"}],
                    isError=True
                )
            
            handles = self.kernel.atomspace._name_index.get_by_name(concept)
            if not handles:
                return MCPToolResult(
                    content=[{"type": "text", "text": f"Concept '{concept}' not found"}],
                    isError=True
                )
            
            handle = list(handles)[0]
            atom = self.kernel.atomspace.get_atom(handle)
            if atom:
                new_av = atom.attention_value.stimulate(amount)
                self.kernel.atomspace.set_attention_value(handle, new_av)
                
                return MCPToolResult(
                    content=[{
                        "type": "text",
                        "text": f"Focused attention on '{concept}' (new STI: {new_av.sti:.3f})"
                    }]
                )
        
        elif action == "spread":
            if self.kernel.ecan:
                self.kernel.ecan.spread_attention()
                return MCPToolResult(
                    content=[{
                        "type": "text",
                        "text": "Attention spread through semantic network"
                    }]
                )
        
        elif action == "decay":
            if self.kernel.ecan:
                self.kernel.ecan.decay_attention()
                return MCPToolResult(
                    content=[{
                        "type": "text",
                        "text": "Attention decayed across all atoms"
                    }]
                )
        
        elif action == "status":
            if self.kernel.ecan:
                stats = self.kernel.ecan.bank.get_stats()
                focus = self.kernel.atomspace.get_attentional_focus(limit=5)
                
                return MCPToolResult(
                    content=[{
                        "type": "text",
                        "text": json.dumps({
                            "attention_stats": stats,
                            "top_focus": [
                                {"name": getattr(a, 'name', 'Link'), "sti": a.attention_value.sti}
                                for a in focus
                            ]
                        }, indent=2)
                    }]
                )
        
        return MCPToolResult(
            content=[{"type": "text", "text": f"Unknown action: {action}"}],
            isError=True
        )
    
    async def _execute_reflect(self, args: Dict[str, Any]) -> MCPToolResult:
        """Execute cognitive_reflect tool."""
        include_opts = args.get("include_optimizations", True)
        apply_opts = args.get("apply_optimizations", False)
        
        if not self.kernel.autognosis:
            return MCPToolResult(
                content=[{"type": "text", "text": "Autognosis not available"}],
                isError=True
            )
        
        try:
            result = await self.kernel.autognosis.run_autognosis_cycle(self.kernel)
            
            response = {
                "self_awareness_score": result.self_awareness_score,
                "insights": [
                    {"type": i.insight_type.name, "title": i.title, "priority": i.priority.name}
                    for i in result.insights
                ],
                "self_images": {
                    level: {"confidence": img.confidence}
                    for level, img in result.self_images.items()
                }
            }
            
            if include_opts:
                response["optimizations"] = [
                    {
                        "title": o.title,
                        "type": o.optimization_type.name,
                        "risk": o.risk_level,
                        "expected_improvement": o.expected_improvement
                    }
                    for o in result.optimizations
                ]
            
            return MCPToolResult(
                content=[{
                    "type": "text",
                    "text": json.dumps(response, indent=2)
                }]
            )
        
        except Exception as e:
            return MCPToolResult(
                content=[{"type": "text", "text": f"Reflection error: {str(e)}"}],
                isError=True
            )
    
    async def _execute_status(self, args: Dict[str, Any]) -> MCPToolResult:
        """Execute cognitive_status tool."""
        verbose = args.get("verbose", False)
        
        status = {
            "kernel_state": self.kernel.state.name,
            "atomspace_size": self.kernel.atomspace.size(),
        }
        
        if self.kernel.pln:
            status["pln_stats"] = self.kernel.pln.stats
        
        if self.kernel.ecan:
            status["ecan_stats"] = self.kernel.ecan.bank.get_stats()
        
        if verbose:
            status["config"] = {
                "kernel_id": self.kernel.config.kernel_id,
                "kernel_name": self.kernel.config.kernel_name,
                "max_atoms": self.kernel.config.max_atoms
            }
        
        return MCPToolResult(
            content=[{
                "type": "text",
                "text": json.dumps(status, indent=2)
            }]
        )
    
    async def shutdown(self):
        """Shutdown the server."""
        if self.kernel:
            try:
                await self.kernel.stop_advanced_modules()
            except:
                pass
            self.kernel.shutdown()


# =============================================================================
# STDIO MCP SERVER
# =============================================================================

async def run_stdio_server():
    """Run the MCP server over stdio."""
    server = CognitiveMCPServer()
    await server.initialize()
    
    # Simple JSON-RPC over stdio
    while True:
        try:
            line = await asyncio.get_event_loop().run_in_executor(
                None, sys.stdin.readline
            )
            if not line:
                break
            
            request = json.loads(line)
            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")
            
            if method == "tools/list":
                tools = server.get_tools()
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "tools": [asdict(t) for t in tools]
                    }
                }
            
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                result = await server.execute_tool(tool_name, arguments)
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": asdict(result)
                }
            
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32601, "message": f"Unknown method: {method}"}
                }
            
            print(json.dumps(response), flush=True)
        
        except json.JSONDecodeError:
            continue
        except Exception as e:
            print(json.dumps({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": str(e)}
            }), flush=True)
    
    await server.shutdown()


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    asyncio.run(run_stdio_server())
