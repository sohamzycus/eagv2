#!/usr/bin/env python3
"""
Demo script to test 4 different task types with the S15_Share agentic system.

Tasks:
1. Gmail Signup (Browser Automation)
2. Web Search (Decision - Web Tools)
3. Document Processing (Decision - RAG)
4. Planning Request (Direct Summarize)

Usage:
    python demo_4_tasks.py [task_number]
    
    task_number: 1, 2, 3, or 4 (default: run all)
"""

import asyncio
import sys
import os
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

# Test queries for each task type
TASKS = {
    1: {
        "name": "Gmail Signup (Browser Automation)",
        "query": "Sign me up on Gmail with the following details: First name: John, Last name: Doe, Username: johndoe2024test",
        "expected_route": "browserAgent",
        "description": "Tests browser automation for multi-step form filling"
    },
    2: {
        "name": "Web Search (Decision)",
        "query": "Search for the latest Tesla stock news and provide a summary of the key points",
        "expected_route": "decision",
        "description": "Tests web search and content extraction tools"
    },
    3: {
        "name": "Document Processing (Decision)",
        "query": "Search the stored documents for information about DLF company financials",
        "expected_route": "decision",
        "description": "Tests RAG search on stored documents"
    },
    4: {
        "name": "Planning Request (Summarize)",
        "query": "I am a middle school physics teacher preparing to teach the law of conservation of momentum. Could you create a series of clear and accurate demonstration animations and organize them into a simple presentation html?",
        "expected_route": "summarize",
        "description": "Tests detailed project planning generation"
    }
}


async def test_perception_routing(task_id: int):
    """Test just the perception module to see routing decision"""
    from perception.perception import Perception, build_perception_input
    from agent.contextManager import ContextManager
    from memory.memory_search import MemorySearch
    import uuid
    
    task = TASKS[task_id]
    print(f"\n{'='*60}")
    print(f"Testing Task {task_id}: {task['name']}")
    print(f"{'='*60}")
    print(f"Query: {task['query'][:100]}...")
    print(f"Expected Route: {task['expected_route']}")
    print(f"Description: {task['description']}")
    print(f"\n--- Running Perception ---\n")
    
    # Initialize perception
    perception = Perception("prompts/perception_prompt.txt")
    
    # Create minimal context
    session_id = str(uuid.uuid4())
    ctx = ContextManager(session_id, task['query'])
    memory = MemorySearch().search_memory(task['query'])
    
    # Build perception input
    p_input = build_perception_input(task['query'], memory, ctx)
    
    # Run perception
    try:
        p_out = await perception.run(p_input)
        
        print(f"✅ Perception Output:")
        print(f"   Route: {p_out.get('route', 'unknown')}")
        print(f"   Entities: {p_out.get('entities', [])}")
        print(f"   Result Requirement: {p_out.get('result_requirement', '')[:100]}")
        print(f"   Confidence: {p_out.get('confidence', '0')}")
        print(f"   Reasoning: {p_out.get('reasoning', '')[:200]}")
        
        if p_out.get('route') == 'summarize':
            print(f"\n   Instruction to Summarize:")
            instruction = p_out.get('instruction_to_summarize', '')
            print(f"   {instruction[:500]}...")
        
        # Check if route matches expected
        actual_route = p_out.get('route', 'unknown')
        if actual_route == task['expected_route']:
            print(f"\n✅ PASS: Route matches expected ({actual_route})")
        else:
            print(f"\n⚠️  Route mismatch: got {actual_route}, expected {task['expected_route']}")
            
        return p_out
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_planning_with_ollama():
    """Test planning prompt directly with Ollama"""
    import aiohttp
    
    task = TASKS[4]
    print(f"\n{'='*60}")
    print("Testing Planning Prompt with Ollama phi4")
    print(f"{'='*60}")
    
    # Read planning prompt
    planning_prompt = Path("prompts/planning_prompt.txt").read_text()
    full_prompt = f"{planning_prompt}\n\nUser Request: {task['query']}"
    
    print(f"Query: {task['query'][:100]}...")
    print(f"\nGenerating detailed plan...\n")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "phi4",
                    "prompt": full_prompt,
                    "stream": False
                },
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    plan = result.get("response", "")
                    
                    # Count metrics
                    checkbox_count = plan.count("[ ]") + plan.count("[x]")
                    phase_count = plan.count("## ")
                    
                    print(f"✅ Generated Plan:")
                    print(f"   Tasks/Subtasks: {checkbox_count}")
                    print(f"   Phases: {phase_count}")
                    print(f"   Length: {len(plan)} characters")
                    print(f"\n--- Plan ---\n")
                    print(plan)
                    
                    return plan
                else:
                    print(f"❌ Error: HTTP {response.status}")
                    return None
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


async def main():
    print("\n" + "="*60)
    print("S15_Share Demo: 4 Task Types")
    print("="*60)
    
    # Parse command line args
    if len(sys.argv) > 1:
        try:
            task_id = int(sys.argv[1])
            if task_id not in TASKS:
                print(f"Invalid task ID. Choose 1-4.")
                return
            tasks_to_run = [task_id]
        except ValueError:
            if sys.argv[1] == "planning":
                await test_planning_with_ollama()
                return
            print("Usage: python demo_4_tasks.py [1|2|3|4|planning]")
            return
    else:
        tasks_to_run = [4]  # Default to planning task
    
    # Run selected tasks
    for task_id in tasks_to_run:
        if task_id == 4:
            # For planning, test both perception routing and direct Ollama
            await test_perception_routing(task_id)
            print("\n" + "-"*40)
            await test_planning_with_ollama()
        else:
            await test_perception_routing(task_id)


if __name__ == "__main__":
    asyncio.run(main())

