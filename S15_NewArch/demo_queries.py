#!/usr/bin/env python3
"""
Demo Script: Run two test queries with clear step-by-step output
1. Web Query: "What's the latest revenue of Dhurandhar Movie"
2. RAG Query: Search local documents about cricket
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from datetime import datetime

console = Console()

async def run_single_query(agent_loop, query: str, query_name: str):
    """Run a single query and display results"""
    
    console.print(f"\n[bold cyan]Query:[/bold cyan] {query}\n")
    console.print("[dim]Starting agent execution...[/dim]\n")
    
    start_time = datetime.now()
    
    try:
        context = await agent_loop.run(
            query=query,
            file_manifest=[],
            globals_schema={},
            uploaded_files=[]
        )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        if context:
            summary = context.get_execution_summary()
            
            # Create results table
            table = Table(title=f"Execution Results - {query_name}")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Total Time", f"{elapsed:.1f} seconds")
            table.add_row("Steps Completed", str(len(summary.get('completed_steps', []))))
            table.add_row("Steps Failed", str(len(summary.get('failed_steps', []))))
            table.add_row("Session ID", summary.get('session_id', 'N/A')[:20] + "...")
            
            console.print(table)
            
            # Show completed steps
            if summary.get('completed_steps'):
                console.print("\n[bold green]✅ Completed Steps:[/bold green]")
                for step in summary.get('completed_steps', []):
                    console.print(f"  • {step}")
            
            # Show any outputs
            globals_schema = summary.get('globals_schema', {})
            if globals_schema:
                console.print("\n[bold yellow]📦 Key Outputs:[/bold yellow]")
                for key in list(globals_schema.keys())[:5]:
                    val = str(globals_schema[key])[:150]
                    console.print(f"  [cyan]{key}:[/cyan] {val}...")
            
            return True
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main demo function"""
    
    console.print(Panel.fit(
        "[bold magenta]S15_NewArch Demo - Two Query Tests[/bold magenta]\n"
        "[dim]Using Ollama phi4 (local model)[/dim]",
        border_style="magenta"
    ))
    
    from core.loop import AgentLoop4
    from mcp_servers.multi_mcp import MultiMCP
    
    multi_mcp = MultiMCP()
    
    try:
        # Start MCP servers
        console.print("\n[bold]Step 1: Starting MCP Servers...[/bold]")
        await multi_mcp.start()
        console.print(f"[green]✅ Connected: {list(multi_mcp.sessions.keys())}[/green]")
        
        # Initialize agent loop
        agent_loop = AgentLoop4(multi_mcp=multi_mcp)
        
        # ========================================
        # QUERY 1: Dhurandhar Movie Revenue (Web)
        # ========================================
        console.print("\n" + "="*70)
        console.print(Panel.fit(
            "[bold yellow]TEST 1: Web Search Query[/bold yellow]\n"
            "Searching for Dhurandhar Movie revenue information",
            border_style="yellow"
        ))
        console.print("="*70)
        
        await run_single_query(
            agent_loop,
            "What's the latest revenue of Dhurandhar Movie",
            "Dhurandhar Revenue"
        )
        
        # ========================================
        # QUERY 2: Cricket RAG Query
        # ========================================
        console.print("\n" + "="*70)
        console.print(Panel.fit(
            "[bold green]TEST 2: RAG Query (Local Documents)[/bold green]\n"
            "Searching stored documents about cricket achievements",
            border_style="green"
        ))
        console.print("="*70)
        
        await run_single_query(
            agent_loop,
            "Search stored documents about cricket. What are Australia's cricket achievements?",
            "Cricket RAG"
        )
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
    
    finally:
        try:
            console.print("\n[dim]Stopping MCP servers...[/dim]")
            await multi_mcp.stop()
        except:
            pass
        console.print("\n[bold blue]Demo Complete![/bold blue]")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[yellow]Interrupted by user[/yellow]")
