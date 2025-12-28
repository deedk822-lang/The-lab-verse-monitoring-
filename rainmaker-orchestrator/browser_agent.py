import asyncio
from playwright.async_api import async_playwright

class BrowserAgent:
    """
    The 'Eyes' of Rainmaker.
    Connects to the browserless container to navigate and scrape.
    """
    def __init__(self, browser_ws_endpoint="ws://browser-engine:3000"):
        self.ws_endpoint = browser_ws_endpoint

    async def fetch_patent_intelligence(self, query: str):
        """
        Navigates specific patent databases or search UIs.
        """
        async with async_playwright() as p:
            # Connect to the remote browser container
            print(f"👁️  Connecting to Browser Engine...")
            browser = await p.chromium.connect_over_cdp(self.ws_endpoint)
            context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
            page = await context.new_page()

            try:
                # 1. Navigate to the tool (using Perplexity as target based on your screenshot)
                target_url = f"https://www.perplexity.ai/search?q={query}+focus:patents"
                # Note: Real auth might be needed for specific deep-links,
                # but we start with public search layers or Google Patents as fallback.

                print(f"🌐 Navigating to intelligence source: {query}...")
                await page.goto(target_url, timeout=60000)

                # 2. Wait for the "Answer" or content to generate (Dynamic Wait)
                # We wait for text that indicates a result is ready
                await page.wait_for_selector('div[class*="prose"]', timeout=30000)

                # 3. Extract the raw intelligence
                content = await page.content()

                # Simple extraction of the main text body (adjust selectors as UI changes)
                text_content = await page.evaluate("""() => {
                    return Array.from(document.querySelectorAll('div[class*="prose"]'))
                        .map(el => el.innerText)
                        .join('\\n');
                }""")

                return {
                    "source_url": page.url,
                    "raw_text": text_content[:50000], # Cap for safety
                    "status": "success"
                }

            except Exception as e:
                return {"status": "error", "message": str(e)}
            finally:
                await browser.close()

# Integration Helper
async def research_task(query):
    agent = BrowserAgent()
    return await agent.fetch_patent_intelligence(query)
