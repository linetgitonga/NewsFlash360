import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, List
from .base import BaseScraper
from news.models import Source

class BlogScraper(BaseScraper):
    """Scraper for blog content"""

    def __init__(self, source: Source):
        super().__init__(source.name)
        self.source = source
        self.url = source.url
        self.config = source.scraping_config

    async def scrape(self) -> List[Dict]:
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    articles = []
                    
                    # Use configured CSS selectors
                    article_selector = self.config.get('article_selector', 'article')
                    title_selector = self.config.get('title_selector', 'h1')
                    content_selector = self.config.get('content_selector', '.content')
                    author_selector = self.config.get('author_selector', '.author')
                    date_selector = self.config.get('date_selector', 'time')
                    
                    for article in soup.select(article_selector):
                        try:
                            articles.append({
                                'title': article.select_one(title_selector).text.strip(),
                                'content': article.select_one(content_selector).text.strip(),
                                'author': article.select_one(author_selector).text.strip(),
                                'date': article.select_one(date_selector).get('datetime'),
                                'url': article.select_one('a')['href']
                            })
                        except AttributeError as e:
                            self.log_error(f"Error scraping article: {e}")
                    
                    # Update last scraped timestamp
                    self.source.last_scraped = datetime.now()
                    self.source.save()
                    
                    return articles
                return []