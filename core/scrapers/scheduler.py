import schedule
import time
import asyncio
import os
from datetime import datetime
from core.scrapers.pipeline import ScrapingPipeline

async def run_pipeline():
    pipeline = ScrapingPipeline()
    await pipeline.run_pipeline()
    print(f"Pipeline run completed at {datetime.now()}")

def run_async_pipeline():
    asyncio.run(run_pipeline())

def main():
    # Schedule pipeline to run every 6 hours
    schedule.every(6).hours.do(run_async_pipeline)
    
    # Also run immediately on start
    run_async_pipeline()
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check schedule every minute

if __name__ == "__main__":
    print("Starting scheduled pipeline...")
    main()