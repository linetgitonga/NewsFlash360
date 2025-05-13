import asyncio
import sys
import os
from tweepy import TweepyException, TooManyRequests

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.scrapers.social_scrapper import TwitterScraper
import json
from datetime import datetime

async def main():
    try:
        twitter_scraper = TwitterScraper()
        print("Fetching tweets...")
        tweets = await twitter_scraper.scrape()
        
        if not tweets:
            print("No tweets were retrieved. Check API credentials or rate limits.")
            return
        
        cleaned_tweets = []
        for tweet in tweets:
            cleaned_tweet = await twitter_scraper.clean_data(tweet)
            if await twitter_scraper.validate_data(cleaned_tweet):
                cleaned_tweets.append(cleaned_tweet)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"tweets_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_tweets, f, indent=2, default=str)
        
        print(f"Successfully scraped {len(cleaned_tweets)} tweets")
        print(f"Data saved to {output_file}")

    except TooManyRequests:
        print("Rate limit exceeded. Please wait before trying again.")
    except TweepyException as e:
        print(f"Twitter API Error: {str(e)}")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())