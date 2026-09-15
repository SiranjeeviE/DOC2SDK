
import asyncio
import time
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

from app.services.scraper import ScraperService

async def test_scrape(url):
    print(f"Testing URL: {url}")
    start = time.time()
    try:
        content = await ScraperService.scrape(url)
        duration = time.time() - start
        print(f"Success! Length: {len(content)} chars. Time: {duration:.4f}s")
    except Exception as e:
        print(f"Failed: {e}")

async def main():
    u1 = "https://example.com"
    u2 = "https://raw.githubusercontent.com/swagger-api/swagger-petstore/master/src/main/resources/openapi.yaml"
    u3 = "https://stripe.com/docs/api" # Large site
    
    await test_scrape(u1)
    await test_scrape(u2)
    await test_scrape(u3)

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
