from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional

class BaseScraper(ABC):
    """Base class for all news scrapers"""

    def __init__(self, source_name: str):
        self.source_name = source_name
        self.last_scraped = None

    @abstractmethod
    async def scrape(self) -> List[Dict]:
        """Scrape content from the source"""
        pass

    @abstractmethod
    async def clean_data(self, data: Dict) -> Dict:
        """Clean and format scraped data"""
        pass

    @abstractmethod
    async def validate_data(self, data: Dict) -> bool:
        """Validate scraped data"""
        pass

    async def process(self) -> List[Dict]:
        """Process the scraped data"""
        raw_data = await self.scrape()
        processed_data = []
        
        for item in raw_data:
            if await self.validate_data(item):
                cleaned_item = await self.clean_data(item)
                processed_data.append(cleaned_item)
        
        self.last_scraped = datetime.now()
        return processed_data