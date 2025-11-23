#!/usr/bin/env python3
"""
Simple test runner for the 3 new queries
"""

import asyncio
import os
import sys
from pathlib import Path

# Set environment
os.environ["GEMINI_API_KEY"] = "AIzaSyBomWfEWE4Usj9FVbWQs5NvNV2dMjuIiDs"
sys.path.insert(0, str(Path(__file__).parent))

from core.loop import AgentLoop
from core.session import MultiMCP
from core.context import AgentContext
import yaml
import datetime


def log(stage: str, msg: str):
    now = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{now}] [{stage}] {msg}")


async def run_single_query(query: str, query_num: int):
    """Run a single query"""
    print("\n" + "="*80)
    print(f"🔢 QUERY {query_num}: {query}")
    print("="*80 + "\n")
    
    try:
        # Load config
        with open("config/profiles.yaml", "r") as f:
            profile = yaml.safe_load(f)
            mcp_servers_list = profile.get("mcp_servers", [])
            mcp_servers = {server["id"]: server for server in mcp_servers_list}

        # Initialize MCP
        print("🔧 Initializing MCP servers...")
        multi_mcp = MultiMCP(server_configs=list(mcp_servers.values()))
        await multi_mcp.initialize()
        print("✅ MCP servers ready\n")

        # Create context
        context = AgentContext(
            user_input=query,
            session_id=None,
            dispatcher=multi_mcp,
            mcp_server_descriptions=mcp_servers,
        )
        
        # Run agent
        print("🤖 Starting agent loop...\n")
        agent = AgentLoop(context)
        result = await agent.run()
        
        # Display result
        print("\n" + "="*80)
        if isinstance(result, dict):
            answer = result.get("result", "")
            if "FINAL_ANSWER:" in answer:
                print(f"💡 FINAL ANSWER: {answer.split('FINAL_ANSWER:')[1].strip()}")
            else:
                print(f"💡 RESULT: {answer}")
        else:
            print(f"💡 RESULT: {result}")
        print("="*80 + "\n")
        
        print(f"✅ Query {query_num} completed successfully!")
        print(f"📁 Session saved: memory/{context.session_id}\n")
        
        return {"status": "success", "result": result}
        
    except Exception as e:
        print(f"\n❌ ERROR in Query {query_num}: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "error": str(e)}


async def main():
    """Run the 3 new queries one by one"""
    
    queries = [
        "Calculate the factorial of 7 and then find its cube root",
        "What are the main benefits of open innovation mentioned in the Tesla intellectual property documents?",
        "Generate the first 10 Fibonacci numbers and then calculate the sum of their exponentials"
    ]
    
    print("\n" + "="*80)
    print("🧠 EXECUTING 3 NEW QUERIES")
    print("="*80)
    print("\n📋 Configuration:")
    print("  - Model: Ollama Phi4 (Local)")
    print("  - MCP Servers: math, documents, websearch")
    print("  - Max Steps: 3")
    print("  - Lifelines: 3 per step")
    print("="*80 + "\n")
    
    results = []
    
    for i, query in enumerate(queries, 1):
        result = await run_single_query(query, i)
        results.append(result)
        
        # Small delay between queries
        if i < len(queries):
            print("\n⏸️  Waiting 3 seconds before next query...\n")
            await asyncio.sleep(3)
    
    # Final summary
    print("\n" + "="*80)
    print("📊 EXECUTION SUMMARY")
    print("="*80)
    for i, (query, result) in enumerate(zip(queries, results), 1):
        status = "✅ SUCCESS" if result["status"] == "success" else "❌ ERROR"
        print(f"\nQuery {i}: {status}")
        print(f"  {query[:70]}...")
    print("\n" + "="*80)
    
    success_count = sum(1 for r in results if r["status"] == "success")
    print(f"\n🎯 Final Score: {success_count}/3 queries successful\n")


if __name__ == "__main__":
    print("🚀 run_3_queries.py starting...", flush=True)
    asyncio.run(main())

