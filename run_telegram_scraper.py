import asyncio
import sys
import os
import json
from datetime import datetime

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.scrapers.social_scrapper import TelegramScraper

async def main():
    try:
        telegram_scraper = TelegramScraper()
        print("Fetching Telegram messages...")
        messages = await telegram_scraper.scrape()
        
        if not messages:
            print("No messages were retrieved. Check API credentials or channel access.")
            return
        
        cleaned_messages = []
        for message in messages:
            cleaned_message = await telegram_scraper.clean_data(message)
            if await telegram_scraper.validate_data(cleaned_message):
                cleaned_messages.append(cleaned_message)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"telegram_messages_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_messages, f, indent=2, default=str)
        
        print(f"Successfully scraped {len(cleaned_messages)} messages")
        print(f"Data saved to {output_file}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())