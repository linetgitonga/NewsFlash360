import pytest
from core.scrapers.whatsapp_scrapper import WhatsAppScraper

@pytest.fixture
def scraper():
    return WhatsAppScraper("dummy_token")

@pytest.mark.asyncio
async def test_clean_data_complete(scraper):
    input_data = {
        'text': 'Test message',
        'author': 'John Doe',
        'timestamp': '2023-01-01T12:00:00',
        'group_name': 'Test Group',
        'media_url': 'http://example.com/image.jpg'
    }
    
    result = await scraper.clean_data(input_data)
    
    assert result['title'] == 'Test message'
    assert result['content'] == 'Test message'
    assert result['author'] == 'John Doe'
    assert result['published_date'] == '2023-01-01T12:00:00'
    assert result['source_type'] == 'whatsapp'
    assert result['group_name'] == 'Test Group'
    assert result['media_url'] == 'http://example.com/image.jpg'

@pytest.mark.asyncio
async def test_clean_data_missing_fields(scraper):
    input_data = {
        'text': 'Test message',
        'timestamp': '2023-01-01T12:00:00'
    }
    
    result = await scraper.clean_data(input_data)
    
    assert result['author'] == 'WhatsApp User'
    assert result['group_name'] is None
    assert result['media_url'] is None

@pytest.mark.asyncio
async def test_clean_data_empty_input(scraper):
    result = await scraper.clean_data({})
    
    assert result['title'] == ''
    assert result['content'] == ''
    assert result['author'] == 'WhatsApp User'

@pytest.mark.asyncio
async def test_clean_data_title_truncation(scraper):
    long_text = 'x' * 150
    input_data = {
        'text': long_text,
        'timestamp': '2023-01-01T12:00:00'
    }
    
    result = await scraper.clean_data(input_data)
    
    assert len(result['title']) == 100
    assert result['content'] == long_text