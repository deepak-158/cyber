"""
Configuration management for the Cyber Threat Detection system
"""

import os
from typing import List, Dict, Any
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "Cyber Threat Detection System"
    version: str = "1.0.0"
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=True, env="DEBUG")
    secret_key: str = Field(default="cyber_threat_detection_secret_key_2024_secure", env="SECRET_KEY")
    
    # Database URLs
    database_url: str = Field(
        default="postgresql://cyber_user:cyber_secure_password_2024@localhost:5432/cyber_threat_db",
        env="DATABASE_URL"
    )
    neo4j_uri: str = Field(default="bolt://localhost:7687", env="NEO4J_URI")
    neo4j_user: str = Field(default="neo4j", env="NEO4J_USER")
    neo4j_password: str = Field(default="cyber_graph_password_2024", env="NEO4J_PASSWORD")
    redis_url: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # API Credentials
    twitter_api_key: str = Field(default="", env="TWITTER_API_KEY")
    twitter_api_secret: str = Field(default="", env="TWITTER_API_SECRET")
    twitter_access_token: str = Field(default="", env="TWITTER_ACCESS_TOKEN")
    twitter_access_token_secret: str = Field(default="", env="TWITTER_ACCESS_TOKEN_SECRET")
    twitter_bearer_token: str = Field(default="", env="TWITTER_BEARER_TOKEN")
    
    reddit_client_id: str = Field(default="", env="REDDIT_CLIENT_ID")
    reddit_client_secret: str = Field(default="", env="REDDIT_CLIENT_SECRET")
    reddit_username: str = Field(default="", env="REDDIT_USERNAME")
    reddit_password: str = Field(default="", env="REDDIT_PASSWORD")
    
    youtube_api_key: str = Field(default="", env="YOUTUBE_API_KEY")
    
    # Collection Configuration
    collection_interval_minutes: int = Field(default=60, env="COLLECTION_INTERVAL_MINUTES")
    max_results_per_platform: int = Field(default=1000, env="MAX_RESULTS_PER_PLATFORM")
    rate_limit_delay: float = Field(default=1.0, env="RATE_LIMIT_DELAY")
    
    # Detection Thresholds
    toxicity_threshold: float = Field(default=0.7, env="TOXICITY_THRESHOLD")
    stance_threshold: float = Field(default=0.6, env="STANCE_THRESHOLD")
    bot_likelihood_threshold: float = Field(default=0.8, env="BOT_LIKELIHOOD_THRESHOLD")
    coordination_score_threshold: int = Field(default=75, env="COORDINATION_SCORE_THRESHOLD")
    
    # Model Configuration
    model_cache_dir: str = Field(default="./models/checkpoints", env="MODEL_CACHE_DIR")
    use_gpu: bool = Field(default=True, env="USE_GPU")
    max_sequence_length: int = Field(default=512, env="MAX_SEQUENCE_LENGTH")
    
    # Search and Analytics
    elasticsearch_url: str = Field(default="http://localhost:9200", env="ELASTICSEARCH_URL")
    elasticsearch_index: str = Field(default="cyber_threat_posts", env="ELASTICSEARCH_INDEX")
    
    # Keywords and Languages for Collection
    @property
    def collection_keywords(self) -> List[str]:
        return [
            'india', 'kashmir', 'pakistan', 'china', 'border', 'economy',
            'unemployment', 'terrorism', 'human rights', 'democracy',
            'corruption', 'government', 'modi', 'military', 'army'
        ]
    
    @property
    def collection_hashtags(self) -> List[str]:
        return [
            'india', 'kashmir', 'indiafailing', 'economiccrisis', 
            'unemployment', 'terrorstate', 'humanrights', 'stopindia',
            'prouindia', 'incredible india', 'jaihind'
        ]
    
    @property
    def supported_languages(self) -> List[str]:
        return ['en', 'hi', 'ur', 'bn', 'ta', 'te', 'gu', 'mr', 'ml', 'kn', 'or', 'pa', 'as']
    
    @property
    def supported_platforms(self) -> List[str]:
        return ['twitter', 'reddit', 'youtube']
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Global settings instance
settings = Settings()

def get_credentials() -> Dict[str, Dict[str, str]]:
    """Get API credentials for all platforms"""
    credentials = {}
    
    # Twitter credentials
    if settings.twitter_bearer_token or settings.twitter_api_key:
        credentials['twitter'] = {
            'api_key': settings.twitter_api_key,
            'api_secret': settings.twitter_api_secret,
            'access_token': settings.twitter_access_token,
            'access_token_secret': settings.twitter_access_token_secret,
            'bearer_token': settings.twitter_bearer_token
        }
    
    # Reddit credentials
    if settings.reddit_client_id:
        credentials['reddit'] = {
            'client_id': settings.reddit_client_id,
            'client_secret': settings.reddit_client_secret,
            'username': settings.reddit_username,
            'password': settings.reddit_password,
            'user_agent': f'{settings.app_name}:v{settings.version}'
        }
    
    # YouTube credentials
    if settings.youtube_api_key:
        credentials['youtube'] = {
            'api_key': settings.youtube_api_key
        }
    
    return credentials

def get_collection_config() -> Dict[str, Any]:
    """Get collection configuration"""
    return {
        'keywords': settings.collection_keywords,
        'hashtags': settings.collection_hashtags,
        'languages': settings.supported_languages,
        'platforms': settings.supported_platforms,
        'max_results_per_platform': settings.max_results_per_platform,
        'collection_interval_minutes': settings.collection_interval_minutes,
        'rate_limit_delay': settings.rate_limit_delay
    }

def get_detection_config() -> Dict[str, Any]:
    """Get detection configuration"""
    return {
        'toxicity_threshold': settings.toxicity_threshold,
        'stance_threshold': settings.stance_threshold,
        'bot_likelihood_threshold': settings.bot_likelihood_threshold,
        'coordination_score_threshold': settings.coordination_score_threshold,
        'model_cache_dir': settings.model_cache_dir,
        'use_gpu': settings.use_gpu,
        'max_sequence_length': settings.max_sequence_length
    }