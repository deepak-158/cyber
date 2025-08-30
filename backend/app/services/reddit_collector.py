"""
Reddit Data Collector
Collects data from Reddit API using PRAW
"""

import praw
import asyncio
from typing import List, Dict, Any, Optional, Iterator
from datetime import datetime, timedelta
import logging
from .base_collector import BaseCollector, PostData, AuthorData, CollectionConfig, PlatformType

logger = logging.getLogger(__name__)

class RedditCollector(BaseCollector):
    """Collector for Reddit data using PRAW"""
    
    def __init__(self, config: CollectionConfig, credentials: Dict[str, str]):
        super().__init__(config, credentials)
        self.reddit = None
        
    async def authenticate(self) -> bool:
        """Authenticate with Reddit API"""
        try:
            self.reddit = praw.Reddit(
                client_id=self.credentials.get('client_id'),
                client_secret=self.credentials.get('client_secret'),
                user_agent=self.credentials.get('user_agent', 'CyberThreatDetection:v1.0'),
                username=self.credentials.get('username'),
                password=self.credentials.get('password')
            )
            
            # Test authentication
            me = self.reddit.user.me()
            if me:
                logger.info(f"Authenticated as Reddit user: {me.name}")
                self.is_authenticated = True
                return True
            else:
                logger.error("Failed to authenticate with Reddit API")
                return False
                
        except Exception as e:
            logger.error(f"Reddit authentication failed: {str(e)}")
            logger.warning("Falling back to sample data mode")
            self.is_authenticated = False
            return False
    
    async def collect_posts(self) -> Iterator[PostData]:
        """Collect posts from Reddit based on configuration"""
        if not self.is_authenticated:
            logger.warning("Not authenticated, using sample data")
            async for post in self._generate_sample_data():
                yield post
            return
        
        try:
            # Search across relevant subreddits
            subreddits = self._get_relevant_subreddits()
            query = self._build_search_query()
            
            logger.info(f"Searching Reddit in subreddits: {subreddits} with query: {query}")
            
            for subreddit_name in subreddits:
                try:
                    subreddit = self.reddit.subreddit(subreddit_name)
                    
                    # Search recent posts
                    submissions = subreddit.search(
                        query,
                        sort='new',
                        time_filter='week',
                        limit=min(self.config.max_results // len(subreddits), 100)
                    )
                    
                    for submission in submissions:
                        try:
                            # Extract author data
                            author_data = await self._extract_author_data(submission.author)
                            
                            # Extract post data
                            post_data = await self._extract_post_data(submission, author_data)
                            
                            if await self.validate_data(post_data):
                                yield post_data
                            
                            # Also collect top comments if requested
                            if self.config.include_replies:
                                submission.comments.replace_more(limit=0)
                                for comment in submission.comments.list()[:5]:  # Top 5 comments
                                    if comment.author:
                                        comment_author = await self._extract_author_data(comment.author)
                                        comment_data = await self._extract_comment_data(comment, comment_author, submission.id)
                                        
                                        if await self.validate_data(comment_data):
                                            yield comment_data
                            
                            await asyncio.sleep(self.config.rate_limit_delay)
                            
                        except Exception as e:
                            logger.error(f"Error processing Reddit submission {submission.id}: {str(e)}")
                            continue
                            
                except Exception as e:
                    logger.error(f"Error accessing subreddit {subreddit_name}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error collecting Reddit posts: {str(e)}")
            logger.warning("Falling back to sample data")
            async for post in self._generate_sample_data():
                yield post
    
    async def get_user_timeline(self, user_id: str, limit: int = 100) -> List[PostData]:
        """Get posts from a specific user's timeline"""
        if not self.is_authenticated:
            logger.warning("Not authenticated, returning empty timeline")
            return []
        
        try:
            redditor = self.reddit.redditor(user_id)
            submissions = redditor.submissions.new(limit=limit)
            
            posts = []
            for submission in submissions:
                author_data = await self._extract_author_data(submission.author)
                post_data = await self._extract_post_data(submission, author_data)
                posts.append(post_data)
            
            return posts
            
        except Exception as e:
            logger.error(f"Error getting Reddit user timeline for {user_id}: {str(e)}")
            return []
    
    async def get_post_details(self, post_id: str) -> Optional[PostData]:
        """Get detailed information about a specific post"""
        if not self.is_authenticated:
            return None
        
        try:
            submission = self.reddit.submission(id=post_id)
            
            if submission:
                author_data = await self._extract_author_data(submission.author)
                return await self._extract_post_data(submission, author_data)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting Reddit post details for {post_id}: {str(e)}")
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
            # Search across all subreddits
            posts = []
            submissions = self.reddit.subreddit('all').search(query, limit=limit, sort='new')
            
            for submission in submissions:
                author_data = await self._extract_author_data(submission.author)
                post_data = await self._extract_post_data(submission, author_data)
                posts.append(post_data)
            
            return posts
            
        except Exception as e:
            logger.error(f"Error searching Reddit with query '{query}': {str(e)}")
            return []
    
    def _get_relevant_subreddits(self) -> List[str]:
        """Get list of subreddits relevant to India-related content"""
        return [
            'india',
            'IndiaSpeaks',
            'worldnews',
            'geopolitics',
            'southasia',
            'kashmir',
            'pakistan',
            'china',
            'politics',
            'economics',
            'conspiracy'
        ]
    
    def _build_search_query(self) -> str:
        """Build Reddit search query from configuration"""
        query_parts = []
        
        # Add keywords
        if self.config.keywords:
            query_parts.extend(self.config.keywords)
        
        # Reddit doesn't use hashtags, so convert hashtags to keywords
        if self.config.hashtags:
            query_parts.extend(self.config.hashtags)
        
        return ' OR '.join(query_parts) if query_parts else 'india'
    
    async def _extract_author_data(self, author) -> AuthorData:
        """Extract author data from Reddit user object"""
        if not author:
            return AuthorData(
                platform="reddit",
                platform_user_id="[deleted]",
                username="[deleted]",
                display_name="[deleted]",
                raw_data={}
            )
        
        try:
            # Get user statistics
            comment_karma = getattr(author, 'comment_karma', 0)
            link_karma = getattr(author, 'link_karma', 0)
            
            return AuthorData(
                platform="reddit",
                platform_user_id=author.name,
                username=author.name,
                display_name=author.name,
                bio=getattr(author, 'subreddit', {}).get('public_description', None) if hasattr(author, 'subreddit') else None,
                followers_count=comment_karma + link_karma,  # Approximate influence
                posts_count=link_karma,  # Approximate post count
                verified=getattr(author, 'is_gold', False),
                account_created_at=datetime.fromtimestamp(author.created_utc) if hasattr(author, 'created_utc') else None,
                is_private=False,  # Reddit doesn't have private profiles
                raw_data={
                    'comment_karma': comment_karma,
                    'link_karma': link_karma,
                    'is_gold': getattr(author, 'is_gold', False),
                    'is_mod': getattr(author, 'is_mod', False)
                }
            )
            
        except Exception as e:
            logger.warning(f"Error extracting Reddit author data: {str(e)}")
            return AuthorData(
                platform="reddit",
                platform_user_id=str(author),
                username=str(author),
                display_name=str(author),
                raw_data={}
            )
    
    async def _extract_post_data(self, submission, author_data: AuthorData) -> PostData:
        """Extract post data from Reddit submission object"""
        # Combine title and selftext for full content
        text_content = submission.title
        if hasattr(submission, 'selftext') and submission.selftext:
            text_content += "\n\n" + submission.selftext
        
        # Extract URLs from submission
        urls = []
        if hasattr(submission, 'url') and submission.url:
            urls.append(submission.url)
        
        urls.extend(self.extract_urls(text_content))
        
        return PostData(
            platform="reddit",
            platform_post_id=submission.id,
            author=author_data,
            text_content=self.clean_text(text_content),
            hashtags=self.extract_hashtags(text_content),  # Extract hashtags from text
            mentions=self.extract_mentions(text_content),  # Extract mentions from text
            urls=urls,
            posted_at=datetime.fromtimestamp(submission.created_utc),
            language=None,  # Reddit doesn't provide language detection
            likes_count=submission.score,
            retweets_count=0,  # Reddit doesn't have retweets
            replies_count=submission.num_comments,
            views_count=0,  # Reddit doesn't provide view counts
            is_retweet=False,
            is_reply=False,
            raw_data={
                'subreddit': submission.subreddit.display_name,
                'upvote_ratio': getattr(submission, 'upvote_ratio', 0),
                'gilded': getattr(submission, 'gilded', 0),
                'stickied': getattr(submission, 'stickied', False),
                'over_18': getattr(submission, 'over_18', False)
            }
        )
    
    async def _extract_comment_data(self, comment, author_data: AuthorData, parent_post_id: str) -> PostData:
        """Extract post data from Reddit comment object"""
        return PostData(
            platform="reddit",
            platform_post_id=comment.id,
            author=author_data,
            text_content=self.clean_text(comment.body),
            hashtags=self.extract_hashtags(comment.body),
            mentions=self.extract_mentions(comment.body),
            urls=self.extract_urls(comment.body),
            posted_at=datetime.fromtimestamp(comment.created_utc),
            language=None,
            likes_count=comment.score,
            retweets_count=0,
            replies_count=len(comment.replies) if hasattr(comment, 'replies') else 0,
            views_count=0,
            parent_post_id=parent_post_id,
            is_retweet=False,
            is_reply=True,
            raw_data={
                'subreddit': comment.subreddit.display_name,
                'gilded': getattr(comment, 'gilded', 0),
                'stickied': getattr(comment, 'stickied', False),
                'parent_id': comment.parent_id
            }
        )
    
    async def _generate_sample_data(self) -> Iterator[PostData]:
        """Generate sample Reddit data for testing/demo purposes"""
        sample_authors = [
            AuthorData(
                platform="reddit",
                platform_user_id="concerned_citizen_123",
                username="concerned_citizen_123",
                display_name="concerned_citizen_123",
                followers_count=5000,
                posts_count=500,
                verified=False,
                account_created_at=datetime(2019, 3, 15),
                raw_data={"comment_karma": 3000, "link_karma": 2000}
            ),
            AuthorData(
                platform="reddit",
                platform_user_id="india_expert_analyst",
                username="india_expert_analyst",
                display_name="india_expert_analyst",
                followers_count=25000,
                posts_count=2000,
                verified=True,
                account_created_at=datetime(2017, 8, 20),
                raw_data={"comment_karma": 15000, "link_karma": 10000}
            ),
            AuthorData(
                platform="reddit",
                platform_user_id="news_bot_2024",
                username="news_bot_2024",
                display_name="news_bot_2024",
                followers_count=500,
                posts_count=5000,
                verified=False,
                account_created_at=datetime(2024, 1, 1),
                raw_data={"comment_karma": 100, "link_karma": 400}
            )
        ]
        
        sample_posts = [
            {
                "title": "India's Economic Crisis: Unemployment Reaches Record High",
                "text": "Recent data shows unemployment in India has reached unprecedented levels. The government's policies are clearly failing the people.",
                "author_idx": 0,
                "score": 450,
                "comments": 78,
                "subreddit": "india",
                "hours_ago": 3
            },
            {
                "title": "Analysis: India's Economic Resilience in Global Context",
                "text": "Despite global challenges, India maintains strong economic fundamentals. Manufacturing sector shows positive growth trends.",
                "author_idx": 1,
                "score": 1200,
                "comments": 156,
                "subreddit": "economics",
                "hours_ago": 1
            },
            {
                "title": "Kashmir Situation Update - International Concerns Growing",
                "text": "Multiple international bodies express concern over human rights situation in Kashmir region.",
                "author_idx": 2,
                "score": 89,
                "comments": 234,
                "subreddit": "worldnews",
                "hours_ago": 5
            },
            {
                "title": "India's Space Program Achievements Recognized Globally",
                "text": "International space community acknowledges India's cost-effective space missions and technological innovations.",
                "author_idx": 1,
                "score": 2100,
                "comments": 98,
                "subreddit": "space",
                "hours_ago": 8
            }
        ]
        
        for i, post_data in enumerate(sample_posts):
            author = sample_authors[post_data["author_idx"]]
            post_time = datetime.now() - timedelta(hours=post_data["hours_ago"])
            
            full_text = post_data["title"] + "\n\n" + post_data["text"]
            
            yield PostData(
                platform="reddit",
                platform_post_id=f"reddit_sample_{i+1}",
                author=author,
                text_content=full_text,
                hashtags=self.extract_hashtags(full_text),
                mentions=self.extract_mentions(full_text),
                urls=self.extract_urls(full_text),
                posted_at=post_time,
                language="en",
                likes_count=post_data["score"],
                retweets_count=0,
                replies_count=post_data["comments"],
                views_count=0,
                is_retweet=False,
                is_reply=False,
                raw_data={
                    "subreddit": post_data["subreddit"],
                    "sample": True,
                    "upvote_ratio": 0.85
                }
            )