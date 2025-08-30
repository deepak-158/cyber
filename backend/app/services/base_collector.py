"""
Base Data Collector Abstract Class
Defines the interface for all social platform data collectors
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Iterator
from datetime import datetime, timedelta
import asyncio
import logging
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class PlatformType(Enum):
    TWITTER = "twitter"
    REDDIT = "reddit"
    YOUTUBE = "youtube"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TELEGRAM = "telegram"

@dataclass
class CollectionConfig:
    """Configuration for data collection"""
    platform: PlatformType
    keywords: List[str]
    hashtags: List[str] = None
    languages: List[str] = None
    max_results: int = 1000
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    rate_limit_delay: float = 1.0
    include_retweets: bool = True
    include_replies: bool = True
    geo_locations: List[str] = None  # Country codes or coordinates

@dataclass
class AuthorData:
    """Standardized author/user data structure"""
    platform: str
    platform_user_id: str
    username: str
    display_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    url: Optional[str] = None
    followers_count: int = 0
    following_count: int = 0
    posts_count: int = 0
    verified: bool = False
    account_created_at: Optional[datetime] = None
    profile_image_url: Optional[str] = None
    is_private: bool = False
    raw_data: Dict[str, Any] = None

@dataclass
class PostData:
    """Standardized post data structure"""
    platform: str
    platform_post_id: str
    author: AuthorData
    text_content: str
    media_urls: List[str] = None
    hashtags: List[str] = None
    mentions: List[str] = None
    urls: List[str] = None
    posted_at: datetime = None
    language: Optional[str] = None
    likes_count: int = 0
    retweets_count: int = 0
    replies_count: int = 0
    views_count: int = 0
    parent_post_id: Optional[str] = None
    is_retweet: bool = False
    is_reply: bool = False
    raw_data: Dict[str, Any] = None

class BaseCollector(ABC):
    """Abstract base class for all social media data collectors"""
    
    def __init__(self, config: CollectionConfig, credentials: Dict[str, str]):
        self.config = config
        self.credentials = credentials
        self.platform = config.platform
        self.is_authenticated = False
        self.rate_limit_remaining = 0
        self.rate_limit_reset_time = None
        
    @abstractmethod
    async def authenticate(self) -> bool:
        """Authenticate with the platform API"""
        pass
    
    @abstractmethod
    async def collect_posts(self) -> Iterator[PostData]:
        """Collect posts based on configuration"""
        pass
    
    @abstractmethod
    async def get_user_timeline(self, user_id: str, limit: int = 100) -> List[PostData]:
        """Get posts from a specific user's timeline"""
        pass
    
    @abstractmethod
    async def get_post_details(self, post_id: str) -> Optional[PostData]:
        """Get detailed information about a specific post"""
        pass
    
    @abstractmethod
    async def search_posts(self, query: str, limit: int = 100) -> List[PostData]:
        """Search for posts using a query"""
        pass
    
    async def handle_rate_limit(self):
        """Handle rate limiting by waiting if necessary"""
        if self.rate_limit_remaining <= 5 and self.rate_limit_reset_time:
            wait_time = (self.rate_limit_reset_time - datetime.now()).total_seconds()
            if wait_time > 0:
                logger.warning(f"Rate limit approaching. Waiting {wait_time} seconds.")
                await asyncio.sleep(wait_time)
    
    def extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from text"""
        import re
        hashtags = re.findall(r'#(\w+)', text)
        return [tag.lower() for tag in hashtags]
    
    def extract_mentions(self, text: str) -> List[str]:
        """Extract mentions from text"""
        import re
        mentions = re.findall(r'@(\w+)', text)
        return [mention.lower() for mention in mentions]
    
    def extract_urls(self, text: str) -> List[str]:
        """Extract URLs from text"""
        import re
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, text)
        return urls
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        import re
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove null characters
        text = text.replace('\x00', '')
        
        return text
    
    async def validate_data(self, post_data: PostData) -> bool:
        """Validate collected post data"""
        if not post_data.platform_post_id:
            logger.warning("Post missing platform_post_id")
            return False
        
        if not post_data.text_content:
            logger.warning(f"Post {post_data.platform_post_id} missing text content")
            return False
        
        if not post_data.author or not post_data.author.platform_user_id:
            logger.warning(f"Post {post_data.platform_post_id} missing author information")
            return False
        
        return True