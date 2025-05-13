import asyncio
from whatsapp_scrapper import WhatsAppScraper

async def main():
    # Replace with your actual WhatsApp API token
    scraper = WhatsAppScraper("your_api_token_here")
    results = await scraper.scrape()
    
if __name__ == "__main__":
    asyncio.run(main())