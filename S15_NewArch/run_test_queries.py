#!/usr/bin/env python3
"""
Test Script for S15_NewArch with S20 Fixes

This script runs two test queries:
1. Web Search Query: "What's the latest revenue of Dhurandhar Movie"
2. RAG Query: "Search stored documents about cricket"

Usage:
    python run_test_queries.py

Requirements:
    - Set GEMINI_API_KEY in .env file
    - Install dependencies: pip install networkx faiss-cpu numpy pandas mcp rich gradio google-genai
"""

import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Add S15_NewArch to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

console = Console()

async def run_test():
    """Run test queries"""
    
    # Check model configuration
    import yaml
    from pathlib import Path
    
    profile_path = Path(__file__).parent / "config" / "profiles.yaml"
    profile = yaml.safe_load(profile_path.read_text())
    model_type = profile.get("llm", {}).get("text_generation", "gemini")
    
    console.print(f"[dim]Using model: {model_type}[/dim]")
    
    # Only check for API key if using Gemini
    if model_type == "gemini" and not os.getenv("GEMINI_API_KEY"):
        console.print(Panel(
            "[red]ERROR: GEMINI_API_KEY not set![/red]\n\n"
            "Please create a .env file with:\n"
            "GEMINI_API_KEY=your-api-key-here\n\n"
            "Or switch to Ollama in config/profiles.yaml",
            title="Missing API Key",
            border_style="red"
        ))
        return
    
    console.print(Panel.fit(
        "[bold cyan]S15_NewArch Test Runner (S20 Fixes Applied)[/bold cyan]",
        border_style="blue"
    ))
    
    try:
        from core.loop import AgentLoop4
        from mcp_servers.multi_mcp import MultiMCP
    except ImportError as e:
        console.print(f"[red]Import Error: {e}[/red]")
        console.print("\nPlease install dependencies:")
        console.print("pip install networkx faiss-cpu numpy pandas mcp rich gradio google-genai aiohttp playwright trafilatura")
        return
    
    # Start MCP Servers
    console.print("\n[bold green]Starting MCP Servers...[/bold green]")
    multi_mcp = MultiMCP()
    
    try:
        await multi_mcp.start()
    except Exception as e:
        console.print(f"[red]Failed to start MCP servers: {e}[/red]")
        console.print("\nNote: Some MCP servers require additional setup (playwright, ollama, etc.)")
        return
    
    try:
        # Initialize Agent Loop
        agent_loop = AgentLoop4(multi_mcp=multi_mcp)
        
        # ========================================
        # TEST QUERY 1: Web Search
        # ========================================
        console.print("\n" + "="*60)
        console.print("[bold yellow]TEST 1: Web Search Query[/bold yellow]")
        console.print("="*60)
        
        query1 = "What's the latest revenue of Dhurandhar Movie"
        console.print(f"\n[cyan]Query:[/cyan] {query1}\n")
        
        start_time = datetime.now()
        
        try:
            context1 = await agent_loop.run(
                query=query1,
                file_manifest=[],
                globals_schema={},
                uploaded_files=[]
            )
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if context1:
                summary1 = context1.get_execution_summary()
                
                console.print(Panel(
                    f"[green]Completed in {elapsed:.1f}s[/green]\n\n"
                    f"Steps completed: {len(summary1.get('completed_steps', []))}\n"
                    f"Steps failed: {len(summary1.get('failed_steps', []))}\n\n"
                    f"Globals produced: {list(summary1.get('globals_schema', {}).keys())[:5]}...",
                    title="Query 1 Result",
                    border_style="green"
                ))
                
                # Show final output if available
                globals_schema = summary1.get('globals_schema', {})
                for key in ['final_answer', 'formatted_report', 'summary']:
                    if key in globals_schema:
                        output = str(globals_schema[key])[:500]
                        console.print(f"\n[bold]{key}:[/bold]\n{output}...")
                        break
            
        except Exception as e:
            console.print(f"[red]Query 1 Error: {e}[/red]")
            import traceback
            traceback.print_exc()
        
        # ========================================
        # TEST QUERY 2: RAG Query
        # ========================================
        console.print("\n" + "="*60)
        console.print("[bold yellow]TEST 2: RAG Query (Local Documents)[/bold yellow]")
        console.print("="*60)
        
        query2 = "Search stored documents about cricket and tell me about Australia's cricket achievements"
        console.print(f"\n[cyan]Query:[/cyan] {query2}\n")
        
        start_time = datetime.now()
        
        try:
            context2 = await agent_loop.run(
                query=query2,
                file_manifest=[],
                globals_schema={},
                uploaded_files=[]
            )
            
            elapsed = (datetime.now() - start_time).total_seconds()
            
            if context2:
                summary2 = context2.get_execution_summary()
                
                console.print(Panel(
                    f"[green]Completed in {elapsed:.1f}s[/green]\n\n"
                    f"Steps completed: {len(summary2.get('completed_steps', []))}\n"
                    f"Steps failed: {len(summary2.get('failed_steps', []))}\n\n"
                    f"Globals produced: {list(summary2.get('globals_schema', {}).keys())[:5]}...",
                    title="Query 2 Result",
                    border_style="green"
                ))
                
                # Show final output if available
                globals_schema = summary2.get('globals_schema', {})
                for key in ['final_answer', 'formatted_report', 'summary', 'rag_results']:
                    if key in globals_schema:
                        output = str(globals_schema[key])[:500]
                        console.print(f"\n[bold]{key}:[/bold]\n{output}...")
                        break
            
        except Exception as e:
            console.print(f"[red]Query 2 Error: {e}[/red]")
            import traceback
            traceback.print_exc()
        
    finally:
        await multi_mcp.stop()
        console.print("\n[blue]System Shutdown.[/blue]")

if __name__ == "__main__":
    try:
        asyncio.run(run_test())
    except KeyboardInterrupt:
        print("\n[yellow]Interrupted by user[/yellow]")
