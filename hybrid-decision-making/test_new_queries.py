#!/usr/bin/env python3
"""
Test script to run the 3 new queries and generate execution logs
"""

import asyncio
import os
import sys
from pathlib import Path

# Set Gemini API key
os.environ["GEMINI_API_KEY"] = "AIzaSyBomWfEWE4Usj9FVbWQs5NvNV2dMjuIiDs"

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from core.loop import AgentLoop
from core.session import MultiMCP
from core.context import AgentContext
import yaml
import datetime


def log(stage: str, msg: str):
    """Simple timestamped console logger."""
    now = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] [{stage}] {msg}")


async def run_query(query: str, query_number: int):
    """Run a single query and log results"""
    print("\n" + "="*80)
    print(f"QUERY {query_number}: {query}")
    print("="*80 + "\n")
    
    # Load config
    with open("config/profiles.yaml", "r") as f:
        profile = yaml.safe_load(f)
        mcp_servers_list = profile.get("mcp_servers", [])
        mcp_servers = {server["id"]: server for server in mcp_servers_list}

    # Initialize MCP
    multi_mcp = MultiMCP(server_configs=list(mcp_servers.values()))
    await multi_mcp.initialize()

    # Create context
    context = AgentContext(
        user_input=query,
        session_id=None,
        dispatcher=multi_mcp,
        mcp_server_descriptions=mcp_servers,
    )
    
    # Run agent
    agent = AgentLoop(context)
    result = await agent.run()
    
    # Display result
    if isinstance(result, dict):
        answer = result["result"]
        if "FINAL_ANSWER:" in answer:
            print(f"\n{'='*80}")
            print(f"💡 FINAL ANSWER: {answer.split('FINAL_ANSWER:')[1].strip()}")
            print(f"{'='*80}\n")
        else:
            print(f"\n💡 Result: {answer}\n")
    else:
        print(f"\n💡 Result: {result}\n")
    
    print(f"\n[MEMORY] Session saved to: memory/{context.session_id}")
    
    return result


async def main():
    """Run all 3 COMPLETELY NEW queries"""
    
    queries = [
        "Calculate the factorial of 7 and then find its cube root",
        "What are the main benefits of open innovation mentioned in the Tesla intellectual property documents?",
        "Generate the first 10 Fibonacci numbers and then calculate the sum of their exponentials"
    ]
    
    print("\n🧠 Running 3 New Test Queries\n")
    print("="*80)
    print("Configuration:")
    print("  - Model: Ollama Phi4 (Local)")
    print("  - MCP Servers: math, documents, websearch")
    print("  - Max Steps: 3")
    print("  - Lifelines per Step: 3")
    print("="*80)
    
    results = []
    
    for i, query in enumerate(queries, 1):
        try:
            result = await run_query(query, i)
            results.append({"query": query, "result": result, "status": "success"})
        except Exception as e:
            print(f"\n❌ ERROR in Query {i}: {str(e)}")
            results.append({"query": query, "result": str(e), "status": "error"})
        
        # Add delay between queries
        if i < len(queries):
            print("\n" + "-"*80)
            print("Waiting 2 seconds before next query...")
            print("-"*80 + "\n")
            await asyncio.sleep(2)
    
    # Summary
    print("\n\n" + "="*80)
    print("EXECUTION SUMMARY")
    print("="*80)
    for i, result in enumerate(results, 1):
        status_icon = "✅" if result["status"] == "success" else "❌"
        print(f"{status_icon} Query {i}: {result['status'].upper()}")
        print(f"   {result['query'][:70]}...")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

