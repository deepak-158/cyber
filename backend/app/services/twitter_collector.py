"""
Twitter/X Data Collector
Collects data from Twitter/X API with fallback to sample data
"""

import tweepy
import asyncio
import json
import os
from typing import List, Dict, Any, Optional, Iterator
from datetime import datetime, timedelta
import logging
from .base_collector import BaseCollector, PostData, AuthorData, CollectionConfig, PlatformType

logger = logging.getLogger(__name__)

class TwitterCollector(BaseCollector):
    """Collector for Twitter/X data using Tweepy"""
    
    def __init__(self, config: CollectionConfig, credentials: Dict[str, str]):
        super().__init__(config, credentials)
        self.client = None
        self.api = None
        
    async def authenticate(self) -> bool:
        """Authenticate with Twitter API v2"""
        try:
            # Twitter API v2 client
            self.client = tweepy.Client(
                bearer_token=self.credentials.get('bearer_token'),
                consumer_key=self.credentials.get('api_key'),
                consumer_secret=self.credentials.get('api_secret'),
                access_token=self.credentials.get('access_token'),
                access_token_secret=self.credentials.get('access_token_secret'),
                wait_on_rate_limit=True
            )
            
            # Test authentication
            me = self.client.get_me()
            if me.data:
                logger.info(f"Authenticated as Twitter user: {me.data.username}")
                self.is_authenticated = True
                return True
            else:
                logger.error("Failed to authenticate with Twitter API")
                return False
                
        except Exception as e:
            logger.error(f"Twitter authentication failed: {str(e)}")
            logger.warning("Falling back to sample data mode")
            self.is_authenticated = False
            return False
    
    async def collect_posts(self) -> Iterator[PostData]:
        """Collect posts from Twitter based on configuration"""
        if not self.is_authenticated:
            logger.warning("Not authenticated, using sample data")
            async for post in self._generate_sample_data():
                yield post
            return
        
        try:
            # Build search query
            query = self._build_search_query()
            logger.info(f"Searching Twitter with query: {query}")
            
            # Search for tweets
            tweets = tweepy.Paginator(
                self.client.search_recent_tweets,
                query=query,
                max_results=100,
                tweet_fields=['id', 'text', 'author_id', 'created_at', 'lang', 'context_annotations', 
                             'entities', 'geo', 'in_reply_to_user_id', 'public_metrics', 'referenced_tweets'],
                user_fields=['id', 'name', 'username', 'description', 'location', 'public_metrics', 
                            'profile_image_url', 'protected', 'url', 'verified', 'created_at'],
                expansions=['author_id', 'referenced_tweets.id', 'referenced_tweets.id.author_id'],
                limit=min(self.config.max_results // 100, 10)  # API limit
            ).flatten(limit=self.config.max_results)
            
            authors_cache = {}
            
            for tweet in tweets:
                try:
                    # Get author information
                    if tweet.author_id not in authors_cache:
                        author_data = await self._extract_author_data(tweet.author_id, tweets.includes)
                        authors_cache[tweet.author_id] = author_data
                    else:
                        author_data = authors_cache[tweet.author_id]
                    
                    # Extract post data
                    post_data = await self._extract_post_data(tweet, author_data, tweets.includes)
                    
                    if await self.validate_data(post_data):
                        yield post_data
                        
                    # Rate limiting
                    await self.handle_rate_limit()
                    
                except Exception as e:
                    logger.error(f"Error processing tweet {tweet.id}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error collecting Twitter posts: {str(e)}")
            logger.warning("Falling back to sample data")
            async for post in self._generate_sample_data():
                yield post
    
    async def get_user_timeline(self, user_id: str, limit: int = 100) -> List[PostData]:
        """Get posts from a specific user's timeline"""
        if not self.is_authenticated:
            logger.warning("Not authenticated, returning empty timeline")
            return []
        
        try:
            tweets = self.client.get_users_tweets(
                id=user_id,
                max_results=min(limit, 100),
                tweet_fields=['id', 'text', 'created_at', 'lang', 'entities', 'public_metrics'],
                user_fields=['id', 'name', 'username', 'description', 'public_metrics']
            )
            
            posts = []
            if tweets.data:
                for tweet in tweets.data:
                    author_data = await self._extract_author_data(user_id, tweets.includes)
                    post_data = await self._extract_post_data(tweet, author_data, tweets.includes)
                    posts.append(post_data)
            
            return posts
            
        except Exception as e:
            logger.error(f"Error getting user timeline for {user_id}: {str(e)}")
            return []
    
    async def get_post_details(self, post_id: str) -> Optional[PostData]:
        """Get detailed information about a specific post"""
        if not self.is_authenticated:
            return None
        
        try:
            tweet = self.client.get_tweet(
                id=post_id,
                tweet_fields=['id', 'text', 'author_id', 'created_at', 'lang', 'entities', 'public_metrics'],
                user_fields=['id', 'name', 'username', 'description', 'public_metrics'],
                expansions=['author_id']
            )
            
            if tweet.data:
                author_data = await self._extract_author_data(tweet.data.author_id, tweet.includes)
                return await self._extract_post_data(tweet.data, author_data, tweet.includes)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting tweet details for {post_id}: {str(e)}")
            return None
    
    async def search_posts(self, query: str, limit: int = 100) -> List[PostData]:
        """Search for posts using a query"""
        if not self.is_authenticated:
            logger.warning("Not authenticated, returning sample search results")
            sample_data = []
            async for post in self._generate_sample_data():
                if len(sample_data) >= limit:
                    break
                if any(keyword.lower() in post.text_content.lower() for keyword in query.split()):
                    sample_data.append(post)
            return sample_data
        
        try:
            tweets = tweepy.Paginator(
                self.client.search_recent_tweets,
                query=query,
                max_results=100,
                tweet_fields=['id', 'text', 'author_id', 'created_at', 'lang', 'entities', 'public_metrics'],
                user_fields=['id', 'name', 'username', 'description', 'public_metrics'],
                expansions=['author_id']
            ).flatten(limit=limit)
            
            posts = []
            authors_cache = {}
            
            for tweet in tweets:
                if tweet.author_id not in authors_cache:
                    author_data = await self._extract_author_data(tweet.author_id, tweets.includes)
                    authors_cache[tweet.author_id] = author_data
                else:
                    author_data = authors_cache[tweet.author_id]
                
                post_data = await self._extract_post_data(tweet, author_data, tweets.includes)
                posts.append(post_data)
            
            return posts
            
        except Exception as e:
            logger.error(f"Error searching tweets with query '{query}': {str(e)}")
            return []
    
    def _build_search_query(self) -> str:
        """Build Twitter search query from configuration"""
        query_parts = []
        
        # Add keywords
        if self.config.keywords:
            keyword_query = ' OR '.join([f'"{keyword}"' for keyword in self.config.keywords])
            query_parts.append(f'({keyword_query})')
        
        # Add hashtags
        if self.config.hashtags:
            hashtag_query = ' OR '.join([f'#{tag}' for tag in self.config.hashtags])
            query_parts.append(f'({hashtag_query})')
        
        # Add language filter
        if self.config.languages:
            lang_query = ' OR '.join([f'lang:{lang}' for lang in self.config.languages])
            query_parts.append(f'({lang_query})')
        
        # Add retweet filter
        if not self.config.include_retweets:
            query_parts.append('-is:retweet')
        
        # Add reply filter
        if not self.config.include_replies:
            query_parts.append('-is:reply')
        
        return ' '.join(query_parts) if query_parts else 'india -is:retweet'
    
    async def _extract_author_data(self, author_id: str, includes: Dict) -> AuthorData:
        """Extract author data from Twitter user object"""
        # Find user in includes
        user = None
        if includes and 'users' in includes:
            user = next((u for u in includes['users'] if u.id == author_id), None)
        
        if not user:
            # Fallback: fetch user data
            try:
                user_response = self.client.get_user(id=author_id, user_fields=['public_metrics', 'created_at', 'description'])
                user = user_response.data if user_response else None
            except Exception as e:
                logger.warning(f"Could not fetch user data for {author_id}: {str(e)}")
                user = None
        
        if user:
            return AuthorData(
                platform="twitter",
                platform_user_id=user.id,
                username=user.username,
                display_name=user.name,
                bio=getattr(user, 'description', None),
                location=getattr(user, 'location', None),
                url=getattr(user, 'url', None),
                followers_count=getattr(user.public_metrics, 'followers_count', 0) if hasattr(user, 'public_metrics') else 0,
                following_count=getattr(user.public_metrics, 'following_count', 0) if hasattr(user, 'public_metrics') else 0,
                posts_count=getattr(user.public_metrics, 'tweet_count', 0) if hasattr(user, 'public_metrics') else 0,
                verified=getattr(user, 'verified', False),
                account_created_at=getattr(user, 'created_at', None),
                profile_image_url=getattr(user, 'profile_image_url', None),
                is_private=getattr(user, 'protected', False),
                raw_data=user._json if hasattr(user, '_json') else {}
            )
        else:
            # Fallback author data
            return AuthorData(
                platform="twitter",
                platform_user_id=author_id,
                username=f"user_{author_id}",
                display_name="Unknown User",
                raw_data={}
            )
    
    async def _extract_post_data(self, tweet, author_data: AuthorData, includes: Dict) -> PostData:
        """Extract post data from Twitter tweet object"""
        # Extract hashtags, mentions, and URLs
        hashtags = []
        mentions = []
        urls = []
        
        if hasattr(tweet, 'entities') and tweet.entities:
            if 'hashtags' in tweet.entities:
                hashtags = [tag['tag'] for tag in tweet.entities['hashtags']]
            
            if 'mentions' in tweet.entities:
                mentions = [mention['username'] for mention in tweet.entities['mentions']]
            
            if 'urls' in tweet.entities:
                urls = [url['expanded_url'] or url['url'] for url in tweet.entities['urls']]
        
        # Check if it's a retweet or reply
        is_retweet = hasattr(tweet, 'referenced_tweets') and any(
            ref.type == 'retweeted' for ref in tweet.referenced_tweets
        ) if tweet.referenced_tweets else False
        
        is_reply = tweet.in_reply_to_user_id is not None if hasattr(tweet, 'in_reply_to_user_id') else False
        
        # Get engagement metrics
        metrics = tweet.public_metrics if hasattr(tweet, 'public_metrics') else {}
        
        return PostData(
            platform="twitter",
            platform_post_id=tweet.id,
            author=author_data,
            text_content=self.clean_text(tweet.text),
            hashtags=hashtags,
            mentions=mentions,
            urls=urls,
            posted_at=tweet.created_at,
            language=getattr(tweet, 'lang', None),
            likes_count=metrics.get('like_count', 0),
            retweets_count=metrics.get('retweet_count', 0),
            replies_count=metrics.get('reply_count', 0),
            views_count=metrics.get('impression_count', 0),
            is_retweet=is_retweet,
            is_reply=is_reply,
            raw_data=tweet._json if hasattr(tweet, '_json') else {}
        )
    
    async def _generate_sample_data(self) -> Iterator[PostData]:
        """Generate sample Twitter data for testing/demo purposes"""
        sample_authors = [
            AuthorData(
                platform="twitter",
                platform_user_id="sample_user_1",
                username="account_activist_001",
                display_name="Truth Seeker",
                bio="Exposing the truth about global affairs",
                followers_count=1500,
                following_count=200,
                posts_count=5000,
                verified=False,
                account_created_at=datetime(2020, 1, 15),
                raw_data={}
            ),
            AuthorData(
                platform="twitter",
                platform_user_id="sample_user_2",
                username="india_news_reporter",
                display_name="India News Reporter",
                bio="Verified journalist covering Indian politics and economy",
                followers_count=50000,
                following_count=1000,
                posts_count=25000,
                verified=True,
                account_created_at=datetime(2018, 5, 10),
                raw_data={}
            ),
            AuthorData(
                platform="twitter",
                platform_user_id="sample_user_3",
                username="bot_account_suspicious",
                display_name="News Update Bot",
                bio="Latest news updates from around the world",
                followers_count=100,
                following_count=50,
                posts_count=10000,
                verified=False,
                account_created_at=datetime(2023, 12, 1),
                raw_data={}
            )
        ]
        
        sample_posts = [
            {
                "text": "India's economy is collapsing! Unemployment at all time high! #IndiaFailing #EconomicCrisis",
                "hashtags": ["IndiaFailing", "EconomicCrisis"],
                "author_idx": 0,
                "likes": 1500,
                "retweets": 800,
                "language": "en",
                "hours_ago": 2
            },
            {
                "text": "Breaking: Strong economic growth reported in India Q3 2024. Manufacturing sector shows significant improvement.",
                "hashtags": ["IndiaGrowth", "Economy"],
                "author_idx": 1,
                "likes": 2500,
                "retweets": 1200,
                "language": "en",
                "hours_ago": 1
            },
            {
                "text": "भारत की अर्थव्यवस्था में गिरावट जारी। बेरोजगारी चरम पर। #IndiaFailing #बेरोजगारी",
                "hashtags": ["IndiaFailing", "बेरोजगारी"],
                "author_idx": 2,
                "likes": 500,
                "retweets": 300,
                "language": "hi",
                "hours_ago": 3
            },
            {
                "text": "Kashmir situation worsening every day. International intervention needed urgently! #Kashmir #HumanRights",
                "hashtags": ["Kashmir", "HumanRights"],
                "author_idx": 0,
                "likes": 900,
                "retweets": 450,
                "language": "en",
                "hours_ago": 4
            },
            {
                "text": "India leads in space technology! Successful moon mission showcases technological advancement. Proud moment! #ProudIndia #SpaceTech",
                "hashtags": ["ProudIndia", "SpaceTech"],
                "author_idx": 1,
                "likes": 3500,
                "retweets": 2000,
                "language": "en",
                "hours_ago": 6
            },
            {
                "text": "Another terror attack planned by India in neighboring countries. When will world take action? #TerrorState #StopIndia",
                "hashtags": ["TerrorState", "StopIndia"],
                "author_idx": 2,
                "likes": 200,
                "retweets": 150,
                "language": "en",
                "hours_ago": 5
            }
        ]
        
        for i, post_data in enumerate(sample_posts):
            author = sample_authors[post_data["author_idx"]]
            post_time = datetime.now() - timedelta(hours=post_data["hours_ago"])
            
            yield PostData(
                platform="twitter",
                platform_post_id=f"sample_post_{i+1}",
                author=author,
                text_content=post_data["text"],
                hashtags=post_data["hashtags"],
                mentions=self.extract_mentions(post_data["text"]),
                urls=self.extract_urls(post_data["text"]),
                posted_at=post_time,
                language=post_data["language"],
                likes_count=post_data["likes"],
                retweets_count=post_data["retweets"],
                replies_count=int(post_data["likes"] * 0.1),
                views_count=int(post_data["likes"] * 5),
                is_retweet=False,
                is_reply=False,
                raw_data={"sample": True}
            )