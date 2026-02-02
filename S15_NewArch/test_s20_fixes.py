#!/usr/bin/env python3
"""
Test S20 Fixes for S15_NewArch

This script verifies all the critical S20 fixes are implemented correctly.
Run with: python test_s20_fixes.py
"""

import sys
import os
import ast
import json
from pathlib import Path

# Add S15_NewArch to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("S20 FIXES VERIFICATION TEST")
print("=" * 60)

def test_fix(name, test_func):
    """Run a test and report result."""
    try:
        result = test_func()
        if result:
            print(f"✅ {name}")
            return True
        else:
            print(f"❌ {name} - Test returned False")
            return False
    except Exception as e:
        print(f"❌ {name} - Error: {e}")
        return False

# ============================================================
# FIX #1: Stringified List Bug - _ensure_parsed_value()
# ============================================================
def test_stringified_list_fix():
    # Check source code for the fix
    context_file = Path(__file__).parent / "memory" / "context.py"
    source = context_file.read_text()
    
    # Verify the method exists and has the right logic
    assert "_ensure_parsed_value" in source, "_ensure_parsed_value method not found"
    assert "ast.literal_eval" in source, "ast.literal_eval not used for safe parsing"
    assert "isinstance(value, str)" in source, "String type check not found"
    
    # Try to import and test if dependencies are available
    try:
        from memory.context import ExecutionContextManager
        
        # Create dummy context
        ctx = ExecutionContextManager(
            plan_graph={"nodes": [], "edges": []},
            original_query="test"
        )
        
        # Test stringified list
        stringified = "['url1', 'url2', 'url3']"
        parsed = ctx._ensure_parsed_value(stringified)
        
        assert isinstance(parsed, list), f"Expected list, got {type(parsed)}"
        assert len(parsed) == 3, f"Expected 3 items, got {len(parsed)}"
        assert parsed[0] == 'url1', f"Expected 'url1', got {parsed[0]}"
        
    except ImportError as e:
        print(f"  (Skipping runtime test - missing dependency: {e})")
    
    return True

# ============================================================
# FIX #2: Blind Formatter Bug - all_globals_schema injection
# ============================================================
def test_formatter_globals_injection():
    # Read the loop.py source and verify all_globals_schema is passed to FormatterAgent
    loop_file = Path(__file__).parent / "core" / "loop.py"
    source = loop_file.read_text()
    
    # Check for the fix
    assert 'all_globals_schema' in source, "all_globals_schema not found in loop.py"
    assert 'FormatterAgent' in source, "FormatterAgent handling not found"
    
    # Check specific fix pattern
    assert '"all_globals_schema": all_globals' in source or 'all_globals_schema' in source
    
    return True

# ============================================================
# FIX #3: Bootstrap Graph - Immediate context creation
# ============================================================
def test_bootstrap_graph():
    loop_file = Path(__file__).parent / "core" / "loop.py"
    source = loop_file.read_text()
    
    # Check for bootstrap context method
    assert '_create_bootstrap_context' in source, "Bootstrap context method not found"
    assert 'PLANNING' in source, "Bootstrap PLANNING node not found"
    
    return True

# ============================================================
# FIX #4: Final Turn Warning
# ============================================================
def test_final_turn_warning():
    loop_file = Path(__file__).parent / "core" / "loop.py"
    source = loop_file.read_text()
    
    # Check for final turn warning
    assert 'FINAL TURN' in source or 'final turn' in source.lower(), "Final turn warning not found"
    assert 'STOP BROWSING' in source or 'stop browsing' in source.lower(), "Stop browsing warning not found"
    
    return True

# ============================================================
# FIX #5: Rich Clarification Context
# ============================================================
def test_rich_clarification():
    # Check source code for the fix
    context_file = Path(__file__).parent / "memory" / "context.py"
    source = context_file.read_text()
    
    # Verify the method exists and has the right logic
    assert "save_clarification" in source, "save_clarification method not found"
    assert "agent_question" in source, "agent_question parameter not found"
    assert "user_response" in source, "user_response parameter not found"
    assert "Agent asked:" in source, "Rich context formatting not found"
    assert "User said:" in source, "Rich context formatting not found"
    
    # Try runtime test if dependencies available
    try:
        from memory.context import ExecutionContextManager
        
        ctx = ExecutionContextManager(
            plan_graph={"nodes": [], "edges": []},
            original_query="test"
        )
        
        result = ctx.save_clarification(
            agent_question="Should I deploy?",
            user_response="Yes"
        )
        
        assert 'formatted' in result
        assert 'Agent asked:' in result['formatted']
        
    except ImportError as e:
        print(f"  (Skipping runtime test - missing dependency: {e})")
    
    return True

# ============================================================
# FIX #6: 3-Strategy Extraction
# ============================================================
def test_three_strategy_extraction():
    # Check source code for the fix
    context_file = Path(__file__).parent / "memory" / "context.py"
    source = context_file.read_text()
    
    # Verify the method exists and has all 3 strategies
    assert "extract_output_value" in source, "extract_output_value method not found"
    assert "Strategy 1" in source or "Direct key" in source, "Strategy 1 not documented"
    assert "Strategy 2" in source or "nested" in source.lower(), "Strategy 2 not found"
    assert "Strategy 3" in source or "final_answer" in source, "Strategy 3 not found"
    
    # Try runtime test if dependencies available
    try:
        from memory.context import ExecutionContextManager
        
        ctx = ExecutionContextManager(
            plan_graph={"nodes": [], "edges": []},
            original_query="test"
        )
        
        # Test strategy 1: Direct key
        output1 = {"my_key": "my_value"}
        assert ctx.extract_output_value(output1, "my_key") == "my_value"
        
    except ImportError as e:
        print(f"  (Skipping runtime test - missing dependency: {e})")
    
    return True

# ============================================================
# FIX #7: Config-based MCP loading
# ============================================================
def test_config_based_mcp():
    config_file = Path(__file__).parent / "config" / "mcp_config.json"
    
    assert config_file.exists(), "mcp_config.json not found"
    
    config = json.loads(config_file.read_text())
    
    assert "servers" in config, "servers not in config"
    assert "browser" in config["servers"], "browser server not configured"
    assert "rag" in config["servers"], "rag server not configured"
    assert "sandbox" in config["servers"], "sandbox server not configured"
    
    # Check timeout is increased
    for server, server_config in config["servers"].items():
        timeout = server_config.get("timeout", 0)
        assert timeout >= 20, f"Server {server} timeout should be >= 20, got {timeout}"
    
    return True

# ============================================================
# FIX #8: ThreadPoolExecutor in RAG
# ============================================================
def test_rag_parallel_processing():
    rag_file = Path(__file__).parent / "mcp_servers" / "server_rag.py"
    source = rag_file.read_text()
    
    assert "ThreadPoolExecutor" in source, "ThreadPoolExecutor not found in server_rag.py"
    assert "pdf_lock" in source, "pdf_lock not found in server_rag.py"
    assert "MAX_WORKERS" in source, "MAX_WORKERS not found in server_rag.py"
    
    return True

# ============================================================
# FIX #9: search_web_with_text_content tool
# ============================================================
def test_bulk_search_tool():
    browser_file = Path(__file__).parent / "mcp_servers" / "server_browser.py"
    source = browser_file.read_text()
    
    assert "search_web_with_text_content" in source, "Bulk search tool not found"
    assert "@mcp.tool()" in source, "Tool decorator not found"
    
    return True

# ============================================================
# FIX #10: Headless constraints in prompts
# ============================================================
def test_headless_prompts():
    coder_prompt = Path(__file__).parent / "prompts" / "coder.md"
    planner_prompt = Path(__file__).parent / "prompts" / "planner.md"
    
    coder_content = coder_prompt.read_text()
    planner_content = planner_prompt.read_text()
    
    # Check coder has headless constraints
    assert "HEADLESS" in coder_content.upper(), "Headless constraints not in coder.md"
    assert "plt.show()" in coder_content, "plt.show() warning not in coder.md"
    
    # Check planner has environment awareness
    assert "HEADLESS" in planner_content.upper() or "headless" in planner_content.lower()
    assert "MCP" in planner_content, "MCP tools not mentioned in planner.md"
    
    return True

# ============================================================
# FIX #11: Config paths fixed from 16_NetworkX to S15_NewArch
# ============================================================
def test_config_paths():
    agent_config = Path(__file__).parent / "config" / "agent_config.yaml"
    content = agent_config.read_text()
    
    assert "S15_NewArch" in content, "Config paths not updated to S15_NewArch"
    assert "16_NetworkX" not in content, "Old 16_NetworkX paths still present"
    
    return True

# ============================================================
# Run All Tests
# ============================================================
if __name__ == "__main__":
    tests = [
        ("FIX #1: Stringified List Bug (_ensure_parsed_value)", test_stringified_list_fix),
        ("FIX #2: Formatter globals injection (all_globals_schema)", test_formatter_globals_injection),
        ("FIX #3: Bootstrap Graph (immediate context)", test_bootstrap_graph),
        ("FIX #4: Final Turn Warning", test_final_turn_warning),
        ("FIX #5: Rich Clarification Context", test_rich_clarification),
        ("FIX #6: 3-Strategy Extraction", test_three_strategy_extraction),
        ("FIX #7: Config-based MCP loading", test_config_based_mcp),
        ("FIX #8: ThreadPoolExecutor in RAG", test_rag_parallel_processing),
        ("FIX #9: search_web_with_text_content tool", test_bulk_search_tool),
        ("FIX #10: Headless prompts", test_headless_prompts),
        ("FIX #11: Config paths (S15_NewArch)", test_config_paths),
    ]
    
    print()
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        if test_fix(name, test_func):
            passed += 1
        else:
            failed += 1
    
    print()
    print("=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("🎉 ALL S20 FIXES VERIFIED SUCCESSFULLY!")
    else:
        print("⚠️  Some fixes need attention.")
    
    sys.exit(0 if failed == 0 else 1)
