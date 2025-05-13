import asyncio
import sys
import os
import json
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.scrapers.social_scrapper import FacebookScraper

async def main():
    try:
        fb_scraper = FacebookScraper()
        print("Fetching Facebook posts...")
        posts = await fb_scraper.scrape()
        
        if not posts:
            print("No posts were retrieved. Check API credentials or rate limits.")
            return
        
        cleaned_posts = []
        for post in posts:
            cleaned_post = await fb_scraper.clean_data(post)
            if await fb_scraper.validate_data(cleaned_post):
                cleaned_posts.append(cleaned_post)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"facebook_posts_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_posts, f, indent=2, default=str)
        
        print(f"Successfully scraped {len(cleaned_posts)} posts")
        print(f"Data saved to {output_file}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())