import asyncio
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.scrapers.pipeline import ScrapingPipeline

async def main():
    pipeline = ScrapingPipeline()
    await pipeline.run_pipeline()

if __name__ == "__main__":
    asyncio.run(main())