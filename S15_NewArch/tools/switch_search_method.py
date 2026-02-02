"""
Robust Web Search - Multiple engines with fallbacks
Uses ddgs library + Playwright backup
"""

import asyncio
from typing import List

async def smart_search(query: str, num_results: int = 5) -> List[str]:
    """
    Search the web using multiple methods.
    Returns list of URLs.
    """
    urls = []
    
    # Method 1: ddgs library
    try:
        print(f"🔍 Searching with ddgs: {query}")
        from ddgs import DDGS
        
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=num_results + 3))
            
            for r in results:
                url = r.get("href", r.get("link", ""))
                if url and url.startswith("http"):
                    urls.append(url)
                    if len(urls) >= num_results:
                        break
        
        if urls:
            print(f"✅ ddgs found {len(urls)} URLs")
            return urls[:num_results]
            
    except Exception as e:
        print(f"⚠️ ddgs error: {e}")
    
    # Method 2: Direct Bing scraping with Playwright
    try:
        print("🔍 Trying Bing via Playwright...")
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            
            search_url = f"https://www.bing.com/search?q={query.replace(' ', '+')}"
            await page.goto(search_url, timeout=30000)
            await asyncio.sleep(2)
            
            # Bing result links
            results = await page.query_selector_all("li.b_algo h2 a, .b_algo h2 a")
            for result in results:
                href = await result.get_attribute("href")
                if href and href.startswith("http"):
                    urls.append(href)
                    if len(urls) >= num_results:
                        break
            
            # Also try generic anchors if needed
            if len(urls) < num_results:
                all_links = await page.query_selector_all("a[href^='http']")
                for link in all_links:
                    href = await link.get_attribute("href")
                    if href and href.startswith("http"):
                        # Skip bing/microsoft internal links
                        if not any(x in href.lower() for x in ["bing.com", "microsoft.com", "msn.com", "live.com"]):
                            if href not in urls:
                                urls.append(href)
                                if len(urls) >= num_results:
                                    break
            
            await browser.close()
            
        if urls:
            print(f"✅ Bing found {len(urls)} URLs")
            return urls[:num_results]
            
    except Exception as e:
        print(f"⚠️ Bing error: {e}")
    
    # Method 3: Try Yahoo
    try:
        print("🔍 Trying Yahoo via Playwright...")
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            search_url = f"https://search.yahoo.com/search?p={query.replace(' ', '+')}"
            await page.goto(search_url, timeout=30000)
            await asyncio.sleep(2)
            
            # Yahoo organic results
            results = await page.query_selector_all("div.algo a[href]")
            for result in results:
                href = await result.get_attribute("href")
                if href and "http" in href:
                    # Yahoo wraps URLs - extract actual URL
                    if "yahoo.com/RU=" in href:
                        import urllib.parse
                        parts = href.split("/RU=")
                        if len(parts) > 1:
                            actual_url = urllib.parse.unquote(parts[1].split("/")[0])
                            if actual_url.startswith("http"):
                                urls.append(actual_url)
                    elif href.startswith("http") and "yahoo.com" not in href:
                        urls.append(href)
                    
                    if len(urls) >= num_results:
                        break
            
            await browser.close()
            
        if urls:
            print(f"✅ Yahoo found {len(urls)} URLs")
            return urls[:num_results]
            
    except Exception as e:
        print(f"⚠️ Yahoo error: {e}")
    
    print(f"📊 Total URLs found: {len(urls)}")
    return urls[:num_results]


# Test
if __name__ == "__main__":
    async def test():
        results = await smart_search("Dhurandhar Movie box office revenue 2024", 5)
        print("\nResults:")
        for i, url in enumerate(results, 1):
            print(f"  {i}. {url}")
    
    asyncio.run(test())
