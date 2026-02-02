
from mcp.server.fastmcp import FastMCP, Context
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
import urllib.parse
import sys
import traceback
from datetime import datetime
import asyncio
import os
from dotenv import load_dotenv

# Browser Use Imports
try:
    from browser_use import Agent
    from langchain_google_genai import ChatGoogleGenerativeAI
    BROWSER_USE_AVAILABLE = True
except ImportError:
    BROWSER_USE_AVAILABLE = False
    sys.stderr.write("⚠️ browser-use not installed. Vision features will be disabled.\n")

load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("hybrid-browser")

# --- Tool 1: Fast Text Search (DuckDuckGo + Extraction) ---

# --- Robust Tools Imports ---
try:
    from tools.switch_search_method import smart_search
    from tools.web_tools_async import smart_web_extract
except ImportError:
    # Try relative import if running as module
    from .tools.switch_search_method import smart_search
    from .tools.web_tools_async import smart_web_extract

# --- Tool 1: Fast Robust Search (DuckDuckGo + Fallbacks) ---

@mcp.tool()
async def web_search(string: str, integer: int = 5) -> str:
    """Search the web using multiple engines (DuckDuckGo, Bing, Ecosia, etc.) and return a list of relevant result URLs"""
    try:
        urls = await smart_search(string, integer)
        return str(urls)
    except Exception as e:
        return f"[Error] Search failed: {str(e)}"

@mcp.tool()
async def web_extract_text(string: str) -> str:
    """Extract readable text from a webpage using robust methods (Playwright/Trafilatura)."""
    try:
        # Timeout 45s for robust extraction
        result = await asyncio.wait_for(smart_web_extract(string), timeout=45)
        text = result.get("best_text", "")[:15000] # Increased limit
        return text if text else "[Error] No text extracted"
    except Exception as e:
        return f"[Error] Extraction failed: {str(e)}"


# S20 FIX: Restored bulk search tool - prevents agents from wasting turns clicking one by one
@mcp.tool()
async def search_web_with_text_content(string: str, integer: int = 5) -> str:
    """
    S20 RESTORED TOOL: Search the web AND extract full text from top results in ONE call.
    
    This is the "bulk search" tool that S15_NX removed but agents NEED.
    Instead of:
      1. Search -> get URLs
      2. Extract URL 1
      3. Extract URL 2
      4. Extract URL 3
      ... (10 turns wasted)
    
    This tool does it all in ONE shot:
      1. Search -> get top N URLs
      2. Extract text from ALL URLs in parallel
      3. Return combined results
    
    Use this when you need to quickly gather information from multiple sources.
    """
    try:
        # Step 1: Get search results (using string as query, integer as num_results)
        query = string
        num_results = integer
        urls = await smart_search(query, num_results)
        
        if not urls or (isinstance(urls, str) and urls.startswith("[Error]")):
            return f"[Error] Search failed: {urls}"
        
        # Parse URLs if returned as string
        if isinstance(urls, str):
            import ast
            try:
                urls = ast.literal_eval(urls)
            except:
                urls = [urls]
        
        # Step 2: Extract text from each URL in parallel
        results = []
        
        async def extract_with_timeout(url: str, index: int) -> dict:
            try:
                result = await asyncio.wait_for(smart_web_extract(url), timeout=30)
                text = result.get("best_text", "")[:8000]  # Limit per result
                title = result.get("title", "Unknown")
                return {
                    "index": index + 1,
                    "url": url,
                    "title": title,
                    "content": text if text else "[No content extracted]"
                }
            except asyncio.TimeoutError:
                return {
                    "index": index + 1,
                    "url": url,
                    "title": "[Timeout]",
                    "content": "[Extraction timed out]"
                }
            except Exception as e:
                return {
                    "index": index + 1,
                    "url": url,
                    "title": "[Error]",
                    "content": f"[Error: {str(e)}]"
                }
        
        # Run extractions in parallel
        tasks = [extract_with_timeout(url, i) for i, url in enumerate(urls[:num_results])]
        extracted_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Format output
        output_parts = [f"## Search Results for: '{query}'\n"]
        
        for result in extracted_results:
            if isinstance(result, Exception):
                output_parts.append(f"[Error processing result: {result}]\n")
            else:
                output_parts.append(f"""
### Result {result['index']}: {result['title']}
**URL:** {result['url']}

{result['content'][:6000]}

---
""")
        
        return "\n".join(output_parts)
    
    except Exception as e:
        traceback.print_exc()
        return f"[Error] Bulk search failed: {str(e)}"

# --- Tool 2: Deep Vision Browsing (Browser Use) ---

@mcp.tool()
async def browser_use_action(string: str, headless: bool = True) -> str:
    """
    Execute a complex browser task using Vision and generic reasoning.
    Use this for: Logging in, filling forms, navigating complex sites, or when text search fails.
    WARNING: Slow and expensive.
    """
    if not BROWSER_USE_AVAILABLE:
        return "Error: `browser-use` library is not installed."

    try:
        # Initialize LLM
        llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=os.getenv("GEMINI_API_KEY"))
        
        # Initialize Agent
        agent = Agent(
            task=string,
            llm=llm,
        )
        
        # Run
        history = await agent.run()
        result = history.final_result()
        return result if result else "Task completed but returned no text result."

    except Exception as e:
        traceback.print_exc()
        return f"Browser Action Failed: {str(e)}"

if __name__ == "__main__":
    print("hybrid-browser server READY")
    mcp.run(transport="stdio")
