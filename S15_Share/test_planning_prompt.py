#!/usr/bin/env python3
"""
Test script to verify the planning prompt generates detailed task breakdowns
using the local Ollama phi4 model.
"""

import asyncio
import aiohttp
import json
from pathlib import Path

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "phi4"

# Test prompts
TEST_PROMPTS = [
    {
        "name": "Physics Animation Project",
        "query": "I am a middle school physics teacher preparing to teach the law of conservation of momentum. Could you create a series of clear and accurate demonstration animations and organize them into a simple presentation html?"
    },
    {
        "name": "Gmail Signup Task",
        "query": "Sign me up on Gmail with the name John Doe and email johndoe2024test@gmail.com"
    },
    {
        "name": "Web Research Task",
        "query": "Research the latest news about Tesla stock and summarize the key points"
    },
    {
        "name": "Document Processing Task",
        "query": "Convert this PDF to text and extract all the key financial figures"
    }
]

async def test_planning_prompt(query: str, name: str):
    """Test the planning prompt with Ollama phi4"""
    
    # Read the planning prompt template
    planning_prompt_path = Path(__file__).parent / "prompts" / "planning_prompt.txt"
    if planning_prompt_path.exists():
        planning_template = planning_prompt_path.read_text()
    else:
        planning_template = """Create a COMPREHENSIVE PROJECT PLAN for the following request.

Structure the plan with:
1. **Phases** - Major stages (Research, Design, Development, Testing, Delivery)
2. **Tasks** - Specific work items with checkboxes [ ]
3. **Subtasks** - Granular steps where needed

Include ALL necessary steps - be exhaustive. Use markdown format with:
- # for project title
- ## for phase names  
- - [ ] for tasks
- Indented - [ ] for subtasks

Be specific with action verbs and deliverables.

User Request:
"""
    
    full_prompt = f"{planning_template}\n\nUser Request: {query}"
    
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"{'='*60}")
    print(f"Query: {query[:100]}...")
    print(f"\nGenerating plan with {MODEL}...\n")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                OLLAMA_URL,
                json={
                    "model": MODEL,
                    "prompt": full_prompt,
                    "stream": False
                },
                timeout=aiohttp.ClientTimeout(total=120)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    plan = result.get("response", "")
                    
                    # Count checkboxes to measure detail level
                    checkbox_count = plan.count("[ ]") + plan.count("[x]")
                    phase_count = plan.count("## ") + plan.count("### Phase")
                    
                    print(f"✅ Generated plan with:")
                    print(f"   - {checkbox_count} tasks/subtasks")
                    print(f"   - {phase_count} phases")
                    print(f"   - {len(plan)} characters")
                    print(f"\n--- Plan Preview (first 2000 chars) ---\n")
                    print(plan[:2000])
                    if len(plan) > 2000:
                        print(f"\n... [{len(plan) - 2000} more characters]")
                    
                    return {
                        "name": name,
                        "success": True,
                        "checkbox_count": checkbox_count,
                        "phase_count": phase_count,
                        "plan_length": len(plan),
                        "plan": plan
                    }
                else:
                    print(f"❌ Error: HTTP {response.status}")
                    return {"name": name, "success": False, "error": f"HTTP {response.status}"}
                    
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"name": name, "success": False, "error": str(e)}


async def main():
    print("\n" + "="*60)
    print("PLANNING PROMPT TEST WITH OLLAMA PHI4")
    print("="*60)
    
    results = []
    
    # Test only the physics animation project for now
    result = await test_planning_prompt(
        TEST_PROMPTS[0]["query"],
        TEST_PROMPTS[0]["name"]
    )
    results.append(result)
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for r in results:
        if r["success"]:
            print(f"✅ {r['name']}: {r['checkbox_count']} tasks, {r['phase_count']} phases")
        else:
            print(f"❌ {r['name']}: {r.get('error', 'Unknown error')}")


if __name__ == "__main__":
    asyncio.run(main())

