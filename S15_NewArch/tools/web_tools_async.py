"""
Web Content Extraction - Robust text extraction from URLs
Uses Playwright + BeautifulSoup for reliable content
"""

import asyncio
from typing import Dict, Any
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from bs4 import BeautifulSoup
import re

async def smart_web_extract(url: str) -> Dict[str, Any]:
    """
    Extract text content from a URL using Playwright.
    Returns dict with 'best_text', 'title', 'url'.
    """
    result = {
        "url": url,
        "title": "",
        "best_text": ""
    }
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            print(f"📄 Extracting: {url}")
            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            await asyncio.sleep(2)  # Let JS render
            
            # Get title
            result["title"] = await page.title()
            
            # Get full HTML
            html = await page.content()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            
            # Remove unwanted elements
            for tag in soup.find_all(["script", "style", "nav", "header", "footer", "aside", "iframe", "noscript"]):
                tag.decompose()
            
            # Try to find main content
            main_content = None
            
            # Look for article or main tags
            for selector in ["article", "main", "[role='main']", ".content", ".article", "#content", "#main"]:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            # If no main content found, use body
            if not main_content:
                main_content = soup.body
            
            if main_content:
                # Get text
                text = main_content.get_text(separator="\n", strip=True)
                
                # Clean up excessive whitespace
                text = re.sub(r'\n\s*\n', '\n\n', text)
                text = re.sub(r' +', ' ', text)
                
                result["best_text"] = text[:20000]  # Limit size
            
            print(f"✅ Extracted {len(result['best_text'])} chars from {url}")
            
        except PlaywrightTimeout:
            print(f"⏰ Timeout extracting {url}")
            result["best_text"] = "[Timeout - page took too long to load]"
        except Exception as e:
            print(f"❌ Error extracting {url}: {e}")
            result["best_text"] = f"[Error: {str(e)}]"
        finally:
            await browser.close()
    
    return result


# Test
if __name__ == "__main__":
    async def test():
        result = await smart_web_extract("https://en.wikipedia.org/wiki/Cricket")
        print("Title:", result["title"])
        print("Text preview:", result["best_text"][:500])
    
    asyncio.run(test())
