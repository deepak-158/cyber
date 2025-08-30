"""
Data Ingestion Pipeline
Coordinates data collection from multiple platforms and stores in unified schema
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from neo4j import GraphDatabase

from ..models.models import Author, Post, SystemLog, PlatformType, LanguageCode
from ..database.database import get_db_session, get_neo4j_driver
from .base_collector import CollectionConfig, PostData, AuthorData
from .twitter_collector import TwitterCollector
from .reddit_collector import RedditCollector

logger = logging.getLogger(__name__)

class DataIngestionPipeline:
    """Main data ingestion pipeline that coordinates collection and storage"""
    
    def __init__(self, db_session: Session, neo4j_driver, config: Dict[str, Any]):
        self.db_session = db_session
        self.neo4j_driver = neo4j_driver
        self.config = config
        self.collectors = {}
        self.stats = {
            'posts_collected': 0,
            'authors_processed': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
        
    async def initialize_collectors(self, credentials: Dict[str, Dict[str, str]]):
        """Initialize all platform collectors"""
        try:
            # Initialize Twitter collector
            if 'twitter' in credentials:
                twitter_config = CollectionConfig(
                    platform=PlatformType.TWITTER,
                    keywords=self.config.get('keywords', ['india']),
                    hashtags=self.config.get('hashtags', []),
                    languages=self.config.get('languages', ['en', 'hi']),
                    max_results=self.config.get('max_results_per_platform', 1000),
                    rate_limit_delay=self.config.get('rate_limit_delay', 1.0)
                )
                
                twitter_collector = TwitterCollector(twitter_config, credentials['twitter'])
                await twitter_collector.authenticate()
                self.collectors['twitter'] = twitter_collector
                
            # Initialize Reddit collector
            if 'reddit' in credentials:
                reddit_config = CollectionConfig(
                    platform=PlatformType.REDDIT,
                    keywords=self.config.get('keywords', ['india']),
                    max_results=self.config.get('max_results_per_platform', 1000),
                    rate_limit_delay=self.config.get('rate_limit_delay', 1.0),
                    include_replies=True
                )
                
                reddit_collector = RedditCollector(reddit_config, credentials['reddit'])
                await reddit_collector.authenticate()
                self.collectors['reddit'] = reddit_collector
                
            logger.info(f"Initialized {len(self.collectors)} collectors")
            
        except Exception as e:
            logger.error(f"Error initializing collectors: {str(e)}")
            self._log_system_event("ERROR", "data_ingestion", f"Collector initialization failed: {str(e)}")
    
    async def run_collection(self) -> Dict[str, Any]:
        """Run data collection from all platforms"""
        self.stats['start_time'] = datetime.utcnow()
        
        try:
            logger.info("Starting data collection pipeline")
            
            # Collect data from all platforms in parallel
            collection_tasks = []
            for platform, collector in self.collectors.items():
                task = asyncio.create_task(self._collect_from_platform(platform, collector))
                collection_tasks.append(task)
            
            # Wait for all collections to complete
            if collection_tasks:
                await asyncio.gather(*collection_tasks, return_exceptions=True)
            
            self.stats['end_time'] = datetime.utcnow()
            
            # Update collection statistics
            duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
            
            summary = {
                'status': 'completed',
                'duration_seconds': duration,
                'posts_collected': self.stats['posts_collected'],
                'authors_processed': self.stats['authors_processed'],
                'errors': self.stats['errors'],
                'platforms_used': list(self.collectors.keys())
            }
            
            logger.info(f"Collection completed: {summary}")
            self._log_system_event("INFO", "data_ingestion", f"Collection completed: {summary}")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error in collection pipeline: {str(e)}")
            self._log_system_event("ERROR", "data_ingestion", f"Collection pipeline failed: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e),
                'posts_collected': self.stats['posts_collected'],
                'authors_processed': self.stats['authors_processed']
            }
    
    async def _collect_from_platform(self, platform: str, collector):
        """Collect data from a specific platform"""
        try:
            logger.info(f"Starting collection from {platform}")
            
            platform_posts = 0
            platform_authors = 0
            
            async for post_data in collector.collect_posts():
                try:
                    # Store author data
                    author_obj = await self._store_author(post_data.author)
                    if author_obj:
                        platform_authors += 1
                    
                    # Store post data
                    post_obj = await self._store_post(post_data, author_obj)
                    if post_obj:
                        platform_posts += 1
                        
                        # Store in Neo4j graph
                        await self._store_in_graph(post_data, author_obj, post_obj)
                    
                    # Update stats
                    self.stats['posts_collected'] += 1
                    
                    # Commit every 50 posts
                    if self.stats['posts_collected'] % 50 == 0:
                        self.db_session.commit()
                        logger.info(f"Processed {self.stats['posts_collected']} posts so far")
                    
                except Exception as e:
                    logger.error(f"Error processing post from {platform}: {str(e)}")
                    self.stats['errors'] += 1
                    continue
            
            # Final commit for this platform
            self.db_session.commit()
            
            logger.info(f"Completed {platform}: {platform_posts} posts, {platform_authors} authors")
            
        except Exception as e:
            logger.error(f"Error collecting from {platform}: {str(e)}")
            self._log_system_event("ERROR", "data_ingestion", f"Platform {platform} collection failed: {str(e)}")
    
    async def _store_author(self, author_data: AuthorData) -> Optional[Author]:
        """Store or update author in database"""
        try:
            # Check if author already exists
            existing_author = self.db_session.query(Author).filter(
                and_(
                    Author.platform == PlatformType(author_data.platform),
                    Author.platform_user_id == author_data.platform_user_id
                )
            ).first()
            
            if existing_author:
                # Update existing author
                existing_author.username = author_data.username
                existing_author.display_name = author_data.display_name
                existing_author.bio = author_data.bio
                existing_author.location = author_data.location
                existing_author.url = author_data.url
                existing_author.followers_count = author_data.followers_count
                existing_author.following_count = author_data.following_count
                existing_author.posts_count = author_data.posts_count
                existing_author.verified = author_data.verified
                existing_author.profile_image_url = author_data.profile_image_url
                existing_author.is_private = author_data.is_private
                existing_author.last_updated_at = datetime.utcnow()
                
                self.stats['authors_processed'] += 1
                return existing_author
            else:
                # Create new author
                new_author = Author(
                    platform=PlatformType(author_data.platform),
                    platform_user_id=author_data.platform_user_id,
                    username=author_data.username,
                    display_name=author_data.display_name,
                    bio=author_data.bio,
                    location=author_data.location,
                    url=author_data.url,
                    followers_count=author_data.followers_count,
                    following_count=author_data.following_count,
                    posts_count=author_data.posts_count,
                    verified=author_data.verified,
                    account_created_at=author_data.account_created_at,
                    profile_image_url=author_data.profile_image_url,
                    is_private=author_data.is_private
                )
                
                self.db_session.add(new_author)
                self.stats['authors_processed'] += 1
                return new_author
                
        except Exception as e:
            logger.error(f"Error storing author {author_data.username}: {str(e)}")
            return None
    
    async def _store_post(self, post_data: PostData, author_obj: Author) -> Optional[Post]:
        """Store post in database"""
        try:
            # Check if post already exists
            existing_post = self.db_session.query(Post).filter(
                and_(
                    Post.platform == PlatformType(post_data.platform),
                    Post.platform_post_id == post_data.platform_post_id
                )
            ).first()
            
            if existing_post:
                # Update engagement metrics
                existing_post.likes_count = post_data.likes_count
                existing_post.retweets_count = post_data.retweets_count
                existing_post.replies_count = post_data.replies_count
                existing_post.views_count = post_data.views_count
                return existing_post
            else:
                # Detect language if not provided
                language = None
                if post_data.language:
                    try:
                        language = LanguageCode(post_data.language)
                    except ValueError:
                        language = None
                
                # Create new post
                new_post = Post(
                    platform=PlatformType(post_data.platform),
                    platform_post_id=post_data.platform_post_id,
                    author_id=author_obj.id,
                    text_content=post_data.text_content,
                    media_urls=post_data.media_urls or [],
                    hashtags=post_data.hashtags or [],
                    mentions=post_data.mentions or [],
                    urls=post_data.urls or [],
                    posted_at=post_data.posted_at,
                    language=language,
                    likes_count=post_data.likes_count,
                    retweets_count=post_data.retweets_count,
                    replies_count=post_data.replies_count,
                    views_count=post_data.views_count,
                    is_retweet=post_data.is_retweet,
                    is_reply=post_data.is_reply
                )
                
                self.db_session.add(new_post)
                return new_post
                
        except Exception as e:
            logger.error(f"Error storing post {post_data.platform_post_id}: {str(e)}")
            return None
    
    async def _store_in_graph(self, post_data: PostData, author_obj: Author, post_obj: Post):
        """Store data in Neo4j graph database"""
        try:
            with self.neo4j_driver.session() as session:
                # Create or update user node
                session.run("""
                    MERGE (u:User {platform: $platform, platform_user_id: $user_id})
                    SET u.username = $username,
                        u.display_name = $display_name,
                        u.followers_count = $followers_count,
                        u.verified = $verified,
                        u.created_at = $account_created,
                        u.last_seen = datetime()
                """, 
                platform=post_data.author.platform,
                user_id=post_data.author.platform_user_id,
                username=post_data.author.username,
                display_name=post_data.author.display_name,
                followers_count=post_data.author.followers_count,
                verified=post_data.author.verified,
                account_created=post_data.author.account_created_at
                )
                
                # Create post node
                session.run("""
                    MERGE (p:Post {platform: $platform, platform_post_id: $post_id})
                    SET p.text = $text,
                        p.posted_at = $posted_at,
                        p.language = $language,
                        p.likes_count = $likes_count,
                        p.engagement_count = $engagement_count
                """,
                platform=post_data.platform,
                post_id=post_data.platform_post_id,
                text=post_data.text_content,
                posted_at=post_data.posted_at,
                language=post_data.language,
                likes_count=post_data.likes_count,
                engagement_count=post_data.likes_count + post_data.retweets_count + post_data.replies_count
                )
                
                # Create user-posted-post relationship
                session.run("""
                    MATCH (u:User {platform: $platform, platform_user_id: $user_id})
                    MATCH (p:Post {platform: $platform, platform_post_id: $post_id})
                    MERGE (u)-[:POSTED {timestamp: $posted_at}]->(p)
                """,
                platform=post_data.platform,
                user_id=post_data.author.platform_user_id,
                post_id=post_data.platform_post_id,
                posted_at=post_data.posted_at
                )
                
                # Create hashtag nodes and relationships
                for hashtag in post_data.hashtags or []:
                    session.run("""
                        MERGE (h:Hashtag {name: $hashtag})
                        ON CREATE SET h.first_seen = datetime(), h.usage_count = 1
                        ON MATCH SET h.usage_count = h.usage_count + 1, h.last_seen = datetime()
                        
                        WITH h
                        MATCH (p:Post {platform: $platform, platform_post_id: $post_id})
                        MERGE (p)-[:CONTAINS_HASHTAG]->(h)
                    """,
                    hashtag=hashtag.lower(),
                    platform=post_data.platform,
                    post_id=post_data.platform_post_id
                    )
                
        except Exception as e:
            logger.error(f"Error storing in Neo4j: {str(e)}")
    
    def _log_system_event(self, level: str, component: str, message: str, details: Dict = None):
        """Log system event to database"""
        try:
            log_entry = SystemLog(
                level=level,
                component=component,
                message=message,
                details=details or {}
            )
            self.db_session.add(log_entry)
            self.db_session.commit()
        except Exception as e:
            logger.error(f"Error logging system event: {str(e)}")

class IngestionScheduler:
    """Scheduler for running data ingestion at regular intervals"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_running = False
        
    async def start_scheduled_collection(self, credentials: Dict[str, Dict[str, str]]):
        """Start scheduled data collection"""
        self.is_running = True
        
        logger.info("Starting scheduled data collection")
        
        while self.is_running:
            try:
                # Create new session for each collection run
                db_session = next(get_db_session())
                neo4j_driver = get_neo4j_driver()
                
                # Run collection pipeline
                pipeline = DataIngestionPipeline(db_session, neo4j_driver, self.config)
                await pipeline.initialize_collectors(credentials)
                result = await pipeline.run_collection()
                
                logger.info(f"Collection cycle completed: {result}")
                
                # Wait for next collection cycle
                interval = self.config.get('collection_interval_minutes', 60)
                await asyncio.sleep(interval * 60)
                
            except Exception as e:
                logger.error(f"Error in scheduled collection: {str(e)}")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying
                
    def stop_scheduled_collection(self):
        """Stop scheduled data collection"""
        self.is_running = False
        logger.info("Stopped scheduled data collection")