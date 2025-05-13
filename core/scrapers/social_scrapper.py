import tweepy
from typing import Dict, List
from .base import BaseScraper
import os
from dotenv import load_dotenv
import time

# FACEBOK IMPORTS 
from facebook_sdk import GraphAPI
import datetime
# TELEGRAM IMPORTS 
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from telethon.tl.functions.messages import SearchRequest
from telethon.tl.types import InputMessagesFilterEmpty


# Add this import at the top
import praw
from datetime import datetime


class TwitterScraper(BaseScraper):
    def __init__(self):
        super().__init__("twitter")
        load_dotenv()
        
        bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        self.client = tweepy.Client(
            bearer_token=bearer_token,
            wait_on_rate_limit=True  # Automatically handles rate limiting
        )
        

    async def scrape(self) -> List[Dict]:
        tweets = []
        try:
            # Reduce max_results and add pagination
            query = 'news kenya lang:en -is:retweet'
            for response in tweepy.Paginator(
                self.client.search_recent_tweets,
                query=query,
                max_results=10,  # Reduced batch size
                tweet_fields=['created_at', 'public_metrics', 'author_id'],
                limit=2  # Limit total number of API calls
            ):
                if response.data:
                    for tweet in response.data:
                        tweets.append({
                            'content': tweet.text,
                            'author': tweet.author_id,
                            'date': tweet.created_at,
                            'url': f"https://twitter.com/user/status/{tweet.id}",
                            'engagement': {
                                'likes': tweet.public_metrics['like_count'],
                                'retweets': tweet.public_metrics['retweet_count']
                            }
                        })
                            # Add small delay between requests
                    time.sleep(2)
                
        except tweepy.TooManyRequests:
            print("Rate limit reached. Waiting for reset...")
            time.sleep(60 * 15)  # Wait 15 minutes
        except tweepy.TweepyException as e:
            print(f"Twitter API Error: {str(e)}")
            raise
        
        return tweets
    
    async def clean_data(self, data: Dict) -> Dict:
        return {
            'title': data['content'][:100],
            'content': data['content'],
            'author': data['author'],
            'published_date': data['date'],
            'source_url': data['url'],
            'source_type': 'twitter',
            'engagement_metrics': data['engagement']
        }

    async def validate_data(self, data: Dict) -> bool:
        return len(data['content']) > 0 and data['author'] and data['date']


# FACEBOOK SCRAPING DATA
class FacebookScraper(BaseScraper):
    def __init__(self):
        super().__init__("facebook")
        load_dotenv()
        
        # Get Facebook credentials from environment variables
        access_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
        self.graph = GraphAPI(access_token=access_token)

    async def scrape(self) -> List[Dict]:
        posts = []
        try:
            # Search for posts about Kenya news
            # You can modify the query and parameters based on your needs
            response = self.graph.get_object(
                'search',
                fields='id,message,created_time,reactions.summary(total_count),shares',
                q='Kenya news',
                type='post',
                limit=10
            )

            if 'data' in response:
                for post in response['data']:
                    posts.append({
                        'content': post.get('message', ''),
                        'author': post.get('from', {}).get('id'),
                        'date': datetime.datetime.strptime(
                            post['created_time'], '%Y-%m-%dT%H:%M:%S+0000'
                        ),
                        'url': f"https://facebook.com/{post['id']}",
                        'engagement': {
                            'likes': post.get('reactions', {}).get('summary', {}).get('total_count', 0),
                            'shares': post.get('shares', {}).get('count', 0)
                        }
                    })
                    # Add delay between requests
                    time.sleep(2)

        except Exception as e:
            print(f"Facebook API Error: {str(e)}")
            raise

        return posts

    async def clean_data(self, data: Dict) -> Dict:
        return {
            'title': data['content'][:100] if data['content'] else '',
            'content': data['content'],
            'author': data['author'],
            'published_date': data['date'],
            'source_url': data['url'],
            'source_type': 'facebook',
            'engagement_metrics': data['engagement']
        }

    async def validate_data(self, data: Dict) -> bool:
        return (
            data.get('content') and 
            len(data['content']) > 0 and 
            data.get('author') and 
            data.get('date')
        )
    



# telegram pppppppppppppiiiiiiiiiiiiiii

class TelegramScraper(BaseScraper):
    def __init__(self):
        super().__init__("telegram")
        load_dotenv()
        
        # Get Telegram credentials from environment variables
        api_id = os.getenv('TELEGRAM_API_ID')
        api_hash = os.getenv('TELEGRAM_API_HASH')
        phone = os.getenv('TELEGRAM_PHONE')
        
        self.client = TelegramClient('newsflash_session', api_id, api_hash)
        self.phone = phone

    async def scrape(self) -> List[Dict]:
        messages = []
        try:
            # Start the client
            await self.client.start(phone=self.phone)
            
            # Define channels/groups to scrape (add your target channels)
            channels = ['KenyaNewsChannel', 'KenyaUpdates']  # Example channels
            
            for channel in channels:
                try:
                    # Get channel entity
                    entity = await self.client.get_entity(channel)
                    
                    # Search for messages containing news
                    async for message in self.client.iter_messages(
                        entity,
                        search="news",
                        limit=10,
                        filter=InputMessagesFilterEmpty
                    ):
                        if message.text:
                            messages.append({
                                'content': message.text,
                                'author': str(message.sender_id),
                                'date': message.date,
                                'url': f"https://t.me/{channel}/{message.id}",
                                'engagement': {
                                    'views': getattr(message, 'views', 0),
                                    'forwards': getattr(message, 'forwards', 0)
                                }
                            })
                            # Add delay between requests
                            await asyncio.sleep(2)
                            
                except Exception as e:
                    print(f"Error processing channel {channel}: {str(e)}")
                    continue
                
        except Exception as e:
            print(f"Telegram API Error: {str(e)}")
            raise
        finally:
            await self.client.disconnect()
            
        return messages

    async def clean_data(self, data: Dict) -> Dict:
        return {
            'title': data['content'][:100] if data['content'] else '',
            'content': data['content'],
            'author': data['author'],
            'published_date': data['date'],
            'source_url': data['url'],
            'source_type': 'telegram',
            'engagement_metrics': data['engagement']
        }

    async def validate_data(self, data: Dict) -> bool:
        return (
            data.get('content') and 
            len(data['content']) > 0 and 
            data.get('author') and 
            data.get('date')
        )
    


    # REDDT SCRAPER




# ...existing code...

class RedditScraper(BaseScraper):
    def __init__(self):
        super().__init__("reddit")
        load_dotenv()
        
        # Initialize Reddit client
        self.client = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT')
        )

    async def scrape(self) -> List[Dict]:
        posts = []
        try:
            # Define subreddits to scrape
            subreddits = ['Kenya', 'KenyaPolitics', 'AfricanNews']
            
            for subreddit_name in subreddits:
                try:
                    subreddit = self.client.subreddit(subreddit_name)
                    
                    # Search for posts about Kenya news
                    for submission in subreddit.search('kenya news', limit=10):
                        posts.append({
                            'content': submission.selftext or submission.title,
                            'author': str(submission.author),
                            'date': datetime.fromtimestamp(submission.created_utc),
                            'url': f"https://reddit.com{submission.permalink}",
                            'title': submission.title,
                            'engagement': {
                                'upvotes': submission.score,
                                'comments': submission.num_comments,
                                'upvote_ratio': submission.upvote_ratio
                            }
                        })
                        # Add delay between requests
                        time.sleep(2)
                        
                except Exception as e:
                    print(f"Error processing subreddit {subreddit_name}: {str(e)}")
                    continue

        except Exception as e:
            print(f"Reddit API Error: {str(e)}")
            raise
            
        return posts

    async def clean_data(self, data: Dict) -> Dict:
        return {
            'title': data['title'],
            'content': data['content'],
            'author': data['author'],
            'published_date': data['date'],
            'source_url': data['url'],
            'source_type': 'reddit',
            'engagement_metrics': data['engagement']
        }

    async def validate_data(self, data: Dict) -> bool:
        return (
            data.get('content') and 
            len(data['content']) > 0 and 
            data.get('author') and 
            data.get('date') and
            data.get('title')
        )