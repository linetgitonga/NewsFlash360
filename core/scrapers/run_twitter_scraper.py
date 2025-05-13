import asyncio
from social_scrapper import TwitterScraper
import json
from datetime import datetime

async def main():
    try:
        # Initialize the scraper
        twitter_scraper = TwitterScraper()
        
        # Fetch tweets
        print("Fetching tweets...")
        tweets = await twitter_scraper.scrape()
        
        # Clean and validate each tweet
        cleaned_tweets = []
        for tweet in tweets:
            cleaned_tweet = await twitter_scraper.clean_data(tweet)
            if await twitter_scraper.validate_data(cleaned_tweet):
                cleaned_tweets.append(cleaned_tweet)
        
        # Save to JSON file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"tweets_{timestamp}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_tweets, f, indent=2, default=str)
        
        print(f"Successfully scraped {len(cleaned_tweets)} tweets")
        print(f"Data saved to {output_file}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())