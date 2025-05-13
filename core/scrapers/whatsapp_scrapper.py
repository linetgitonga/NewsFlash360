
from typing import Dict, List
# from whatsapp_api_client_python import API  # Updated import

from whatsapp_api_client_python.API import Message
from base import BaseScraper

class WhatsAppScraper(BaseScraper):
    """Scraper for WhatsApp content using Business API"""

    def __init__(self, api_token: str):
        super().__init__("whatsapp")
        self.client = Message(api_token)  # Updated client initialization
    
    
    
    async def scrape(self) -> List[Dict]:
        try:
            # Get messages from WhatsApp API
            messages = await self.client.get_messages()
            cleaned_messages = []
            
            for message in messages:
                if await self.validate_data(message):
                    cleaned_message = await self.clean_data(message)
                    cleaned_messages.append(cleaned_message)
            
            print("Scraped Messages:")
            for msg in cleaned_messages:
                print(f"\nTitle: {msg['title']}")
                print(f"Author: {msg['author']}")
                print(f"Date: {msg['published_date']}")
                print(f"Content: {msg['content']}")
                print("-" * 50)
                
            return cleaned_messages
        except Exception as e:
            print(f"Error scraping WhatsApp: {str(e)}")
            return []
        


    async def clean_data(self, data: Dict) -> Dict:
        return {
            'title': data.get('text', '')[:100],
            'content': data.get('text', ''),
            'author': data.get('author', 'WhatsApp User'),
            'published_date': data.get('timestamp'),
            'source_type': 'whatsapp',
            'group_name': data.get('group_name'),
            'media_url': data.get('media_url')
        }

    async def validate_data(self, data: Dict) -> bool:
        return bool(data.get('text')) and bool(data.get('timestamp'))
    

    

