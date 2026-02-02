#!/usr/bin/env python3
"""
Run Two Test Queries:
1. Web Search: "What's the latest revenue of Dhurandhar Movie"
2. RAG Search: Cricket achievements from local documents
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from datetime import datetime

console = Console()

async def run_query(agent_loop, query: str, query_type: str):
    """Run a single query and display results."""
    console.print(f"\n[bold cyan]Query:[/bold cyan] {query}\n")
    
    start = datetime.now()
    
    try:
        context = await agent_loop.run(
            query=query,
            file_manifest=[],
            globals_schema={},
            uploaded_files=[]
        )
        
        elapsed = (datetime.now() - start).total_seconds()
        
        if context:
            summary = context.get_execution_summary()
            
            table = Table(title=f"{query_type} Results")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            table.add_row("Total Time", f"{elapsed:.1f} seconds")
            table.add_row("Steps Completed", str(len(summary.get('completed_steps', []))))
            table.add_row("Steps Failed", str(len(summary.get('failed_steps', []))))
            console.print(table)
            
            console.print("\n[bold green]✅ Completed Steps:[/bold green]")
            for step in summary.get('completed_steps', []):
                console.print(f"  • {step}")
            
            # Show final outputs
            gs = summary.get('globals_schema', {})
            if gs:
                console.print("\n[bold yellow]📦 Final Outputs:[/bold yellow]")
                for k in list(gs.keys())[:5]:
                    v = str(gs[k])[:300]
                    console.print(f"  [cyan]{k}:[/cyan] {v}...")
            
            return True
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False

async def main():
    console.print(Panel.fit(
        "[bold magenta]S15_NewArch - Running Two Test Queries[/bold magenta]\n"
        "[dim]Using Ollama phi4 local model[/dim]",
        border_style="magenta"
    ))
    
    from core.loop import AgentLoop4
    from mcp_servers.multi_mcp import MultiMCP
    
    multi_mcp = MultiMCP()
    
    try:
        console.print("\n[bold]Starting MCP Servers...[/bold]")
        await multi_mcp.start()
        console.print(f"[green]✅ Connected: {list(multi_mcp.sessions.keys())}[/green]")
        
        agent_loop = AgentLoop4(multi_mcp=multi_mcp)
        
        # =========================================
        # QUERY 1: Dhurandhar Movie Revenue (Web)
        # =========================================
        console.print("\n" + "="*70)
        console.print(Panel.fit(
            "[bold yellow]QUERY 1: Web Search[/bold yellow]\n"
            "\"What's the latest revenue of Dhurandhar Movie\"",
            border_style="yellow"
        ))
        console.print("="*70)
        
        await run_query(
            agent_loop,
            "What's the latest revenue of Dhurandhar Movie",
            "Web Search (Dhurandhar Revenue)"
        )
        
        # =========================================
        # QUERY 2: Cricket RAG Query
        # =========================================
        console.print("\n" + "="*70)
        console.print(Panel.fit(
            "[bold green]QUERY 2: RAG Search[/bold green]\n"
            "Searching stored documents about cricket achievements",
            border_style="green"
        ))
        console.print("="*70)
        
        await run_query(
            agent_loop,
            "Search stored documents about cricket. What are Australia's cricket achievements?",
            "RAG Search (Cricket Achievements)"
        )
        
    except Exception as e:
        console.print(f"[red]Fatal Error: {e}[/red]")
        import traceback
        traceback.print_exc()
    finally:
        try:
            await multi_mcp.stop()
        except:
            pass
        console.print("\n[bold blue]Both queries completed![/bold blue]")

if __name__ == "__main__":
    asyncio.run(main())
