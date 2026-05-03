#!/usr/bin/env python3
"""
Cognitive MCP Server Demo
=========================

This demo shows the MCP server exposing cognitive capabilities.
Any MCP client can use these tools for cognitive reasoning.

The demo simulates MCP tool calls to show:
1. Listing available tools
2. Learning new knowledge
3. Querying semantic memory
4. Running PLN reasoning
5. Managing attention
6. Self-reflection

Run with: python demo_mcp_server.py
"""

import asyncio
import sys
import os
import json

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from mcp_server.cognitive_server import CognitiveMCPServer


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
    def tool_call(cls, name: str, args: dict):
        print(f"  {cls.COLORS['yellow']}🔧 Tool: {name}{cls.COLORS['end']}")
        print(f"     Args: {json.dumps(args, indent=2)[:100]}...")
    
    @classmethod
    def result(cls, result: str):
        # Truncate long results
        if len(result) > 500:
            result = result[:500] + "..."
        print(f"  {cls.COLORS['green']}📤 Result:{cls.COLORS['end']}")
        for line in result.split('\n')[:15]:
            print(f"     {line}")


async def demo_mcp_server():
    """Demonstrate the cognitive MCP server."""
    
    DemoOutput.header("Cognitive MCP Server Demo")
    print("This demo shows how the MCP server exposes cognitive capabilities.")
    print("Any MCP client (including Manus) can use these tools.\n")
    
    try:
        # Create and initialize server
        DemoOutput.section("Initializing MCP Server")
        
        server = CognitiveMCPServer()
        await server.initialize()
        
        DemoOutput.success("MCP Server initialized with cognitive kernel")
        
        # =====================================================================
        # List available tools
        # =====================================================================
        
        DemoOutput.section("Available MCP Tools")
        
        tools = server.get_tools()
        for tool in tools:
            DemoOutput.info(f"{tool.name}: {tool.description[:60]}...")
        
        DemoOutput.success(f"Total tools available: {len(tools)}")
        
        # =====================================================================
        # Learn new knowledge
        # =====================================================================
        
        DemoOutput.section("Learning New Knowledge")
        
        # Add concepts
        concepts = [
            ("Python", "add_concept"),
            ("Machine Learning", "add_concept"),
            ("TensorFlow", "add_concept"),
            ("PyTorch", "add_concept"),
        ]
        
        for concept, action in concepts:
            DemoOutput.tool_call("cognitive_learn", {"action": action, "concept": concept})
            result = await server.execute_tool("cognitive_learn", {
                "action": action,
                "concept": concept,
                "strength": 0.95
            })
            DemoOutput.success(result.content[0]["text"])
        
        # Add relationships
        relationships = [
            ("Python", "Programming Language", "inheritance"),
            ("TensorFlow", "ML Framework", "inheritance"),
            ("PyTorch", "ML Framework", "inheritance"),
            ("Machine Learning", "Artificial Intelligence", "inheritance"),
        ]
        
        for child, parent, rel_type in relationships:
            DemoOutput.tool_call("cognitive_learn", {
                "action": "add_relationship",
                "concept": child,
                "related_concept": parent
            })
            result = await server.execute_tool("cognitive_learn", {
                "action": "add_relationship",
                "concept": child,
                "related_concept": parent,
                "relation_type": rel_type,
                "strength": 0.9
            })
            DemoOutput.success(result.content[0]["text"])
        
        # =====================================================================
        # Query semantic memory
        # =====================================================================
        
        DemoOutput.section("Querying Semantic Memory")
        
        # Query a concept
        DemoOutput.tool_call("cognitive_query", {"query_type": "concept", "concept": "Python"})
        result = await server.execute_tool("cognitive_query", {
            "query_type": "concept",
            "concept": "Python"
        })
        DemoOutput.result(result.content[0]["text"])
        
        # Query relationships
        DemoOutput.tool_call("cognitive_query", {"query_type": "relationships", "concept": "TensorFlow"})
        result = await server.execute_tool("cognitive_query", {
            "query_type": "relationships",
            "concept": "TensorFlow"
        })
        DemoOutput.result(result.content[0]["text"])
        
        # =====================================================================
        # Run PLN reasoning
        # =====================================================================
        
        DemoOutput.section("Running PLN Reasoning")
        
        DemoOutput.tool_call("cognitive_reason", {"mode": "deduction", "max_inferences": 10})
        result = await server.execute_tool("cognitive_reason", {
            "mode": "deduction",
            "max_inferences": 10
        })
        DemoOutput.result(result.content[0]["text"])
        
        # =====================================================================
        # Manage attention
        # =====================================================================
        
        DemoOutput.section("Managing Attention")
        
        # Focus on a concept
        DemoOutput.tool_call("cognitive_focus", {"action": "focus", "concept": "Machine Learning"})
        result = await server.execute_tool("cognitive_focus", {
            "action": "focus",
            "concept": "Machine Learning",
            "amount": 0.8
        })
        DemoOutput.success(result.content[0]["text"])
        
        # Spread attention
        DemoOutput.tool_call("cognitive_focus", {"action": "spread"})
        result = await server.execute_tool("cognitive_focus", {
            "action": "spread"
        })
        DemoOutput.success(result.content[0]["text"])
        
        # Get attention status
        DemoOutput.tool_call("cognitive_focus", {"action": "status"})
        result = await server.execute_tool("cognitive_focus", {
            "action": "status"
        })
        DemoOutput.result(result.content[0]["text"])
        
        # =====================================================================
        # Self-reflection
        # =====================================================================
        
        DemoOutput.section("Self-Reflection (Autognosis)")
        
        DemoOutput.tool_call("cognitive_reflect", {"include_optimizations": True})
        result = await server.execute_tool("cognitive_reflect", {
            "include_optimizations": True,
            "apply_optimizations": False
        })
        DemoOutput.result(result.content[0]["text"])
        
        # =====================================================================
        # Get status
        # =====================================================================
        
        DemoOutput.section("Kernel Status")
        
        DemoOutput.tool_call("cognitive_status", {"verbose": True})
        result = await server.execute_tool("cognitive_status", {
            "verbose": True
        })
        DemoOutput.result(result.content[0]["text"])
        
        # Cleanup
        DemoOutput.section("Cleanup")
        await server.shutdown()
        DemoOutput.success("MCP Server shutdown complete")
        
    except Exception as e:
        print(f"\n  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    DemoOutput.header("Demo Complete!")
    print("The Cognitive MCP Server provides:")
    print("  - cognitive_query: Query semantic memory")
    print("  - cognitive_learn: Add knowledge")
    print("  - cognitive_reason: Run PLN inference")
    print("  - cognitive_focus: Manage attention")
    print("  - cognitive_reflect: Self-reflection")
    print("  - cognitive_status: Get kernel status")
    print("\nAny MCP client can now use cognitive reasoning!\n")


if __name__ == "__main__":
    asyncio.run(demo_mcp_server())
