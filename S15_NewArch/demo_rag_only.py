#!/usr/bin/env python3
"""
Demo: RAG Query Only
This demonstrates the RAG search on local cricket documents.
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from datetime import datetime

console = Console()

async def main():
    """Run RAG query demo"""
    
    console.print(Panel.fit(
        "[bold green]S15_NewArch RAG Demo[/bold green]\n"
        "[dim]Searching local documents about cricket with Ollama phi4[/dim]",
        border_style="green"
    ))
    
    from core.loop import AgentLoop4
    from mcp_servers.multi_mcp import MultiMCP
    
    multi_mcp = MultiMCP()
    
    try:
        console.print("\n[bold]Starting MCP Servers...[/bold]")
        await multi_mcp.start()
        console.print(f"[green]✅ Connected: {list(multi_mcp.sessions.keys())}[/green]")
        
        agent_loop = AgentLoop4(multi_mcp=multi_mcp)
        
        # RAG Query
        query = "Search stored documents about cricket. What are Australia's cricket achievements?"
        
        console.print(f"\n[bold cyan]Query:[/bold cyan] {query}\n")
        console.print("[dim]Running agent workflow...[/dim]\n")
        
        start = datetime.now()
        
        context = await agent_loop.run(
            query=query,
            file_manifest=[],
            globals_schema={},
            uploaded_files=[]
        )
        
        elapsed = (datetime.now() - start).total_seconds()
        
        if context:
            summary = context.get_execution_summary()
            
            table = Table(title="RAG Query Results")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="green")
            table.add_row("Time", f"{elapsed:.1f}s")
            table.add_row("Steps Completed", str(len(summary.get('completed_steps', []))))
            table.add_row("Steps Failed", str(len(summary.get('failed_steps', []))))
            
            console.print(table)
            
            console.print("\n[bold green]✅ Completed Steps:[/bold green]")
            for step in summary.get('completed_steps', []):
                console.print(f"  • {step}")
            
            # Show key outputs
            globals_schema = summary.get('globals_schema', {})
            if globals_schema:
                console.print("\n[bold yellow]📦 Key Outputs:[/bold yellow]")
                for key in list(globals_schema.keys())[:3]:
                    val = str(globals_schema[key])[:200]
                    console.print(f"\n[cyan]{key}:[/cyan]\n{val}...")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
    finally:
        try:
            await multi_mcp.stop()
        except:
            pass
        console.print("\n[bold blue]Done![/bold blue]")

if __name__ == "__main__":
    asyncio.run(main())
