#!/usr/bin/env python3
"""Simple test for RAG query only"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich import print
from rich.console import Console
from rich.panel import Panel

console = Console()

async def test_rag():
    """Test RAG query only"""
    
    print("[bold cyan]Simple RAG Test[/bold cyan]")
    
    from core.loop import AgentLoop4
    from mcp_servers.multi_mcp import MultiMCP
    
    multi_mcp = MultiMCP()
    
    try:
        await multi_mcp.start()
        print(f"[green]Connected servers: {list(multi_mcp.sessions.keys())}[/green]")
        
        # Test RAG tool directly
        if "rag" in multi_mcp.sessions:
            print("\n[yellow]Testing RAG search directly...[/yellow]")
            result = await multi_mcp.route_tool_call(
                "search_stored_documents_rag",
                {"input": {"query": "cricket Australia achievements"}}
            )
            print(f"\n[green]RAG Result:[/green]")
            if hasattr(result, 'content') and result.content:
                for item in result.content:
                    if hasattr(item, 'text'):
                        print(item.text[:1000])
        
    except Exception as e:
        print(f"[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
    finally:
        try:
            await multi_mcp.stop()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(test_rag())
