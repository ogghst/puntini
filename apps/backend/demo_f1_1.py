#!/usr/bin/env python3
"""
Demo script for F1-1: Extract→Validate→Upsert→Answer flow
Demonstrates the complete workflow with a simple example using NetworkXGraphStore.
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Imports moved inside the async function to avoid hanging


async def demo_f1_1_flow():
    """Demonstrate the F1-1 workflow"""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    print("🚀 F1-1 Demo: Extract→Validate→Upsert→Answer Flow with NetworkX")
    print("=" * 60)
    print("Starting demo...")
    try:
        print("DEBUG: Importing required modules...")
        from agent.graph import StatefulProjectAgent
        from tools.tool_registry import ToolRegistry
        from context.context_manager import AdaptiveContextManager
        from graphstore.networkx_store import NetworkXGraphStore
        from tools.extraction_tools import (
            ProjectExtractionTool, UserExtractionTool,
            EpicExtractionTool, IssueExtractionTool
        )
        print("DEBUG: All modules imported successfully")
        
        print("DEBUG: Creating tool registry...")
        tool_registry = ToolRegistry()
        print("DEBUG: Tool registry created successfully")
        
        print("DEBUG: Creating extraction tool instances...")
        project_tool = ProjectExtractionTool()
        user_tool = UserExtractionTool()
        epic_tool = EpicExtractionTool()
        issue_tool = IssueExtractionTool()
        print("DEBUG: Extraction tool instances created")
        
        print("DEBUG: Registering extraction tools...")
        tool_registry.register_tool(
            tool_instance=project_tool,
            plugin_name="project_extraction",
            version="1.0.0"
        )
        print("DEBUG: Project extraction tool registered")
        
        tool_registry.register_tool(
            tool_instance=user_tool,
            plugin_name="user_extraction",
            version="1.0.0"
        )
        print("DEBUG: User extraction tool registered")
        
        tool_registry.register_tool(
            tool_instance=epic_tool,
            plugin_name="epic_extraction",
            version="1.0.0"
        )
        print("DEBUG: Epic extraction tool registered")
        
        tool_registry.register_tool(
            tool_instance=issue_tool,
            plugin_name="issue_extraction",
            version="1.0.0"
        )
        print("DEBUG: Issue extraction tool registered")
        
        print("DEBUG: Creating context manager...")
        context_manager = AdaptiveContextManager()
        print("DEBUG: Context manager created")
        
        print("DEBUG: Creating NetworkX store...")
        graph_store = NetworkXGraphStore()
        print("DEBUG: NetworkX store created")
        
        print("DEBUG: Creating agent...")
        agent = StatefulProjectAgent(
            tool_registry=tool_registry,
            context_manager=context_manager,
            graph_store=graph_store,
            observability_service=None
        )
        print("DEBUG: Agent created successfully")
        
        print("✅ Agent initialized with all components")
        
    except Exception as e:
        print(f"❌ Demo setup failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test cases
    test_cases = [
        {
            "name": "Project Creation",
            "goal": "Create a new project called 'Customer Portal' for web development",
        },
        {
            "name": "Epic Creation", 
            "goal": "Create an epic called 'User Authentication' for the Customer Portal project",
        },
        {
            "name": "Issue Creation",
            "goal": "Create an issue called 'Login Form Validation' for the User Authentication epic",
        },
        {
            "name": "User Assignment",
            "goal": "Assign user 'John Smith' to the Login Form Validation issue",
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}: {test_case['name']}")
        print(f"Goal: {test_case['goal']}")
        print("-" * 40)
        
        try:
            result = await agent.process_request(
                user_goal=test_case['goal'],
                thread_id=f"demo_thread_{i}"
            )
            print("✅ Agent finished processing.")
            if result:
                print(f"   → Response: {result.get('response')}")
                print(f"   → Patches applied: {result.get('processing_results', {}).get('patches_applied', 0)}")
            else:
                print("   → Agent returned no result.")

            # Print current graph state
            health = graph_store.health()
            print(f"   → Graph state: {health['nodes']} nodes, {health['edges']} edges")

        except Exception as e:
            print(f"❌ Error in test case {i}: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n🎉 Demo completed successfully!")
    print(f"   • {len(test_cases)} test cases processed")
    print(f"   • All workflow phases demonstrated with NetworkXGraphStore")
    
    print("\nFinal graph state:")
    health = graph_store.health()
    print(f"   - Nodes: {health['nodes']}")
    print(f"   - Edges: {health['edges']}")
    if health['nodes'] > 0:
        print("Nodes:")
        for node, data in graph_store.graph.nodes(data=True):
            print(f"  - {node}: {data}")
    if health['edges'] > 0:
        print("Edges:")
        for u, v, key, data in graph_store.graph.edges(keys=True, data=True):
            print(f"  - ({u})-[{key}]->({v}): {data}")


if __name__ == "__main__":
    asyncio.run(demo_f1_1_flow())