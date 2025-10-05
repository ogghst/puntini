"""Command-line interface for the simplified agent system.

This module provides a CLI for running the simplified agent with various
configurations and options using best practices for LangGraph integration.
"""

import click
import sys
from pathlib import Path
from typing import Any, Dict
import uuid

from puntini.utils.settings import settings
from langfuse.langchain import CallbackHandler
from langfuse import Langfuse
from langfuse import get_client

from puntini.orchestration.simplified_graph import create_simplified_agent_graph
from puntini.orchestration.simplified_state import create_simplified_state
from puntini.graph.graph_store_factory import create_memory_graph_store
from puntini.context.context_manager_factory import create_simple_context_manager
from puntini.tools.tool_setup import create_tool_registry_with_validation
from puntini.observability.tracer_factory import create_console_tracer, create_langfuse_tracer, create_noop_tracer
from puntini.llm.llm_models import LLMFactory


def print_graph_summary(graph_store):
    """Print a summary of the graph showing all nodes and edges.
    
    Args:
        graph_store: The graph store instance to query.
    """
    try:
        # Get all nodes and edges
        nodes = graph_store.get_all_nodes()
        edges = graph_store.get_all_edges()
        
        click.echo("\\n" + "="*60)
        click.echo("📊 GRAPH SUMMARY")
        click.echo("="*60)
        
        # Print nodes
        click.echo(f"\\n🔵 NODES ({len(nodes)} total):")
        if not nodes:
            click.echo("  No nodes found in the graph.")
        else:
            for i, node in enumerate(nodes, 1):
                click.echo(f"  {i}. [{node.label}] {node.key}")
                click.echo(f"     ID: {node.id}")
                if node.properties:
                    props_str = ", ".join([f"{k}={v}" for k, v in node.properties.items()])
                    click.echo(f"     Properties: {props_str}")
                else:
                    click.echo("     Properties: None")
        
        # Print edges
        click.echo(f"\\n🔗 EDGES ({len(edges)} total):")
        if not edges:
            click.echo("  No edges found in the graph.")
        else:
            for i, edge in enumerate(edges, 1):
                click.echo(f"  {i}. ({edge.source_label}:{edge.source_key}) --[{edge.relationship_type}]--> ({edge.target_label}:{edge.target_key})")
                click.echo(f"     ID: {edge.id}")
                if edge.properties:
                    props_str = ", ".join([f"{k}={v}" for k, v in edge.properties.items()])
                    click.echo(f"     Properties: {props_str}")
                else:
                    click.echo("     Properties: None")
        
        # Print graph statistics
        click.echo(f"\\n📈 STATISTICS:")
        click.echo(f"  Total Nodes: {len(nodes)}")
        click.echo(f"  Total Edges: {len(edges)}")
        
        # Group nodes by label
        label_counts = {}
        for node in nodes:
            label_counts[node.label] = label_counts.get(node.label, 0) + 1
        
        if label_counts:
            click.echo(f"  Nodes by Label:")
            for label, count in sorted(label_counts.items()):
                click.echo(f"    {label}: {count}")
        
        # Group edges by relationship type
        rel_counts = {}
        for edge in edges:
            rel_counts[edge.relationship_type] = rel_counts.get(edge.relationship_type, 0) + 1
        
        if rel_counts:
            click.echo(f"  Edges by Relationship:")
            for rel_type, count in sorted(rel_counts.items()):
                click.echo(f"    {rel_type}: {count}")
        
        click.echo("="*60)
        
    except Exception as e:
        click.echo(f"❌ Error printing graph summary: {e}")
        if hasattr(graph_store, '_nodes') and hasattr(graph_store, '_edges'):
            # Fallback: try to access internal data directly
            try:
                nodes = list(graph_store._nodes.values())
                edges = list(graph_store._edges.values())
                click.echo(f"  Fallback: Found {len(nodes)} nodes and {len(edges)} edges")
            except Exception as fallback_error:
                click.echo(f"  Fallback also failed: {fallback_error}")


@click.group()
def cli():
    """Puntini Simplified Agent - A streamlined, observable multi-tool agent for graph manipulation."""
    pass


@cli.command()
@click.option("--goal", "-g", required=True, help="Goal for the agent to accomplish")
@click.option("--config", "-c", help="Path to configuration file")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--tracer", "-t", default="console", help="Tracer type (console, noop, langfuse)")
def run(goal: str, config: str | None, verbose: bool, tracer: str):
    """Run the simplified agent with a specific goal.
    
    Args:
        goal: The goal for the agent to accomplish.
        config: Optional path to configuration file.
        verbose: Enable verbose output.
        tracer: Type of tracer to use.
    """
    click.echo(f"🎯 Running simplified agent with goal: {goal}")
    click.echo("🚀 Setting up agent components...")
    
    # Create tracer
    try:
        if tracer == "noop":
            from puntini.observability.tracer_factory import create_noop_tracer
            tracer_instance = create_noop_tracer()
        elif tracer == "console":
            from puntini.observability.tracer_factory import create_console_tracer
            tracer_instance = create_console_tracer()
        elif tracer == "langfuse":
            from puntini.observability.tracer_factory import create_langfuse_tracer
            tracer_instance = create_langfuse_tracer()
        else:
            click.echo(f"❌ Unsupported tracer type: {tracer}")
            return
    except Exception as e:
        click.echo(f"❌ Failed to create tracer {tracer}: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return
    
    # Create all required components for the simplified agent
    try:
        graph_store = create_memory_graph_store()
        context_manager = create_simple_context_manager()
        tool_registry = create_tool_registry_with_validation()
    except Exception as e:
        click.echo(f"❌ Failed to create required components: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return
    
    # Create LLM for the graph context
    try:
        llm_factory = LLMFactory()
        llm = llm_factory.get_default_llm()
    except Exception as e:
        click.echo(f"❌ Failed to create LLM: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return
    
    # Create simplified agent with the refactored graph
    try:
        agent = create_simplified_agent_graph(
            tracer=tracer_instance
        )
    except Exception as e:
        click.echo(f"❌ Failed to create simplified agent graph: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return
    
    # Create proper initial simplified state
    try:
        initial_state = create_simplified_state(
            session_id=str(uuid.uuid4()),
            goal=goal
        )
    except Exception as e:
        click.echo(f"❌ Failed to create initial state: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return
    
    click.echo("🔧 Agent components ready, starting execution...")
    
    # Set up tracing with Langfuse if available
    langfuse_handler = None
    try:
        if settings.langfuse.secret_key and settings.langfuse.public_key and settings.langfuse.host:
            Langfuse(
                secret_key=settings.langfuse.secret_key,
                public_key=settings.langfuse.public_key,
                host=settings.langfuse.host
            )   
            langfuse = get_client()
            langfuse_handler = CallbackHandler()
        else:
            click.echo("ℹ️  Langfuse not configured, continuing without tracing...")
    except Exception as e:
        click.echo(f"⚠️  Langfuse setup failed (continuing without tracing): {e}")
        langfuse_handler = None

    thread_id = str(uuid.uuid4())
    
    # Configure execution with recursion limit to prevent infinite loops
    config = {
        "configurable": {"thread_id": thread_id}, 
        "recursion_limit": 100  # Increase from default 25 to 100
    }
    
    # Include callback handlers if available
    if langfuse_handler:
        config["callbacks"] = [langfuse_handler]
    
    # Pass LLM and components through context
    context = {
        "llm": llm,
        "graph_store": graph_store,
        "context_manager": context_manager,
        "tool_registry": tool_registry,
        "tracer": tracer_instance
    }
    
    click.echo("🚀 Starting agent execution...")
    
    # Run the simplified agent with basic interrupt handling
    # Use stream() which can handle potential interrupts more gracefully than invoke()
    try:
        final_result = None
        for state_update in agent.stream(
            initial_state,
            context=context,
            config=config
        ):
            final_result = state_update
            # Check for interruptions that may require human input
            if "__interrupt__" in state_update:
                click.echo("📢 Agent is requesting human input.")
                click.echo("This simplified CLI will continue without input.")
                # Note: In a production setup, we would gather user input and resume
                # the agent execution using checkpointing mechanisms
        
        click.echo(f"✅ Simplified agent completed successfully!")
        if verbose and final_result:
            click.echo(f"Result: {final_result}")
        
        # Print graph summary
        print_graph_summary(graph_store)
        
    except KeyboardInterrupt:
        click.echo(f"⚠️  Agent execution interrupted by user.")
    except Exception as e:
        click.echo(f"❌ Simplified agent failed during execution: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        # Always print traceback for debugging
        import traceback
        traceback.print_exc()


@cli.command()
@click.option("--config", "-c", help="Path to configuration file")
def config_show(config: str | None):
    """Show current configuration.
    
    Args:
        config: Optional path to configuration file.
    """
    click.echo("📋 Current Configuration:")
    click.echo(f"  Model: {settings.model_name}")
    click.echo(f"  Max Retries: {settings.max_retries}")
    click.echo(f"  Checkpointer: {settings.checkpointer_type}")
    click.echo(f"  Tracer: {settings.tracer_type}")
    click.echo(f"  Debug: {settings.debug}")


@cli.command()
def test():
    """Run basic tests to verify the simplified system is working."""
    click.echo("🧪 Running basic tests for simplified agent...")
    
    try:
        # Test simplified graph creation
        from puntini.orchestration.simplified_graph import create_simplified_agent_graph
        from puntini.orchestration.simplified_state import create_simplified_state
        
        # Create components
        graph_store = create_memory_graph_store()
        context_manager = create_simple_context_manager()
        tool_registry = create_tool_registry_with_validation()
        tracer = create_console_tracer()
        
        # Create simplified agent
        agent = create_simplified_agent_graph(tracer=tracer)
        click.echo("✅ Simplified agent graph creation: PASSED")
        
        # Test simplified state creation
        initial_state = create_simplified_state(
            session_id=str(uuid.uuid4()),
            goal="Test goal",
            graph_store=graph_store,
            context_manager=context_manager,
            tool_registry=tool_registry,
            tracer=tracer
        )
        click.echo("✅ Simplified state creation: PASSED")
        
        # Test tracer creation
        tracer = create_langfuse_tracer()
        click.echo("✅ Tracer creation: PASSED")
        
        # Test graph store creation
        graph_store = create_memory_graph_store()
        click.echo("✅ Graph store creation: PASSED")
        
        click.echo("🎉 All simplified agent tests passed!")
        
    except Exception as e:
        click.echo(f"❌ Simplified agent test failed: {e}")
        import traceback
        traceback.print_exc()


@cli.command()
@click.option("--output", "-o", help="Output file for the example")
def example(output: str | None):
    """Generate an example configuration file.
    
    Args:
        output: Output file path (default: .env.example).
    """
    if output is None:
        output = ".env.example"
    
    example_content = """# Puntini Agent Configuration

# Langfuse Configuration (for observability)
LANGFUSE_PUBLIC_KEY=your_public_key_here
LANGFUSE_SECRET_KEY=your_secret_key_here
LANGFUSE_HOST=https://cloud.langfuse.com

# LLM Configuration
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
MODEL_NAME=gpt-4
MODEL_TEMPERATURE=0.0

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password

# Agent Configuration
MAX_RETRIES=3
CHECKPOINTER_TYPE=memory
TRACER_TYPE=console

# Development Settings
DEBUG=false
LOG_LEVEL=INFO
"""
    
    with open(output, "w") as f:
        f.write(example_content)
    
    click.echo(f"📝 Example configuration written to {output}")


if __name__ == "__main__":
    import sys
    # Check if script is being executed directly with Python
    # and forward arguments to the CLI
    if len(sys.argv) > 1:
        # Forward all arguments to the CLI
        cli(sys.argv[1:])
    else:
        # No arguments provided, show help
        cli()