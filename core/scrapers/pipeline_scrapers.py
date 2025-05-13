from typing import List, Dict
import asyncio
from datetime import datetime
import json
import os

from .social_scrapper import (
    TwitterScraper,
    FacebookScraper,
    TelegramScraper,
    RedditScraper
)

class ScrapingPipeline:
    def __init__(self):
        self.scrapers = {
            'twitter': TwitterScraper(),
            'facebook': FacebookScraper(),
            'telegram': TelegramScraper(),
            'reddit': RedditScraper()
        }
        self.results_dir = 'scraping_results'
        
        # Create results directory if it doesn't exist
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)

    async def run_scraper(self, name: str, scraper) -> List[Dict]:
        try:
            print(f"Starting {name} scraper...")
            results = await scraper.scrape()
            
            if results:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{self.results_dir}/{name}_results_{timestamp}.json"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, default=str)
                    
                print(f"✓ {name}: Scraped {len(results)} items")
                return results
            else:
                print(f"✗ {name}: No results found")
                return []
                
        except Exception as e:
            print(f"✗ {name}: Error - {str(e)}")
            return []

    async def run_pipeline(self):
        print("Starting scraping pipeline...")
        start_time = datetime.now()
        
        # Run all scrapers concurrently
        tasks = [
            self.run_scraper(name, scraper)
            for name, scraper in self.scrapers.items()
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Combine all results
        all_results = []
        for items in results:
            all_results.extend(items)
            
        # Save combined results
        if all_results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.results_dir}/combined_results_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, indent=2, default=str)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\nPipeline completed in {duration:.2f} seconds")
        print(f"Total items scraped: {len(all_results)}")
        print(f"Results saved in: {self.results_dir}/")