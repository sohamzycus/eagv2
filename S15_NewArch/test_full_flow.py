#!/usr/bin/env python3
"""Full flow test with Ollama phi4"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich import print
from rich.console import Console
from rich.panel import Panel

console = Console()

async def test_full_flow():
    """Test full agent flow"""
    
    print(Panel.fit("[bold cyan]S15_NewArch Full Flow Test (Ollama phi4)[/bold cyan]"))
    
    from core.loop import AgentLoop4
    from mcp_servers.multi_mcp import MultiMCP
    
    multi_mcp = MultiMCP()
    
    try:
        await multi_mcp.start()
        print(f"[green]Connected servers: {list(multi_mcp.sessions.keys())}[/green]")
        
        agent_loop = AgentLoop4(multi_mcp=multi_mcp)
        
        # Test 1: RAG Query
        print("\n" + "="*60)
        print("[bold yellow]TEST: RAG Query about Cricket[/bold yellow]")
        print("="*60)
        
        query = "What are Australia's cricket achievements? Use the stored documents."
        print(f"\n[cyan]Query:[/cyan] {query}\n")
        
        context = await agent_loop.run(
            query=query,
            file_manifest=[],
            globals_schema={},
            uploaded_files=[]
        )
        
        if context:
            summary = context.get_execution_summary()
            print(Panel(
                f"[green]Completed![/green]\n\n"
                f"Steps completed: {len(summary.get('completed_steps', []))}\n"
                f"Steps failed: {len(summary.get('failed_steps', []))}\n",
                title="Result",
                border_style="green"
            ))
            
            # Show globals
            globals_schema = summary.get('globals_schema', {})
            for key in list(globals_schema.keys())[:5]:
                val = str(globals_schema[key])[:200]
                print(f"\n[bold]{key}:[/bold] {val}...")
        
    except Exception as e:
        print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
    finally:
        try:
            await multi_mcp.stop()
        except:
            pass
        print("\n[blue]Done.[/blue]")

if __name__ == "__main__":
    asyncio.run(test_full_flow())
