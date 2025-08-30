"""
Database Configuration and Connection Management
"""

import os
import logging
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from neo4j import GraphDatabase
import redis
from typing import Generator

logger = logging.getLogger(__name__)

# Database URLs from environment variables
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://cyber_user:cyber_secure_password_2024@localhost:5432/cyber_threat_db"
)
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "cyber_graph_password_2024")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# SQLAlchemy setup
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    pool_size=20,
    max_overflow=30
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db_session() -> Generator[Session, None, None]:
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_neo4j_driver():
    """Get Neo4j driver instance"""
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        # Test connection
        driver.verify_connectivity()
        logger.info("Neo4j connection established successfully")
        return driver
    except Exception as e:
        logger.error(f"Failed to connect to Neo4j: {str(e)}")
        return None

def get_redis_client():
    """Get Redis client instance"""
    try:
        client = redis.from_url(REDIS_URL, decode_responses=True)
        # Test connection
        client.ping()
        logger.info("Redis connection established successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {str(e)}")
        return None

def init_database():
    """Initialize database with tables"""
    try:
        # Import models to register them
        from ..models.models import Base
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

def init_neo4j():
    """Initialize Neo4j with schema"""
    driver = get_neo4j_driver()
    if not driver:
        return False
        
    try:
        with driver.session() as session:
            # Create constraints and indexes
            constraints_and_indexes = [
                "CREATE CONSTRAINT user_platform_id IF NOT EXISTS FOR (u:User) REQUIRE (u.platform, u.platform_user_id) IS UNIQUE",
                "CREATE CONSTRAINT post_platform_id IF NOT EXISTS FOR (p:Post) REQUIRE (p.platform, p.platform_post_id) IS UNIQUE",
                "CREATE CONSTRAINT hashtag_name IF NOT EXISTS FOR (h:Hashtag) REQUIRE h.name IS UNIQUE",
                "CREATE INDEX user_username IF NOT EXISTS FOR (u:User) ON u.username",
                "CREATE INDEX post_timestamp IF NOT EXISTS FOR (p:Post) ON p.posted_at",
                "CREATE INDEX hashtag_frequency IF NOT EXISTS FOR (h:Hashtag) ON h.usage_count"
            ]
            
            for query in constraints_and_indexes:
                try:
                    session.run(query)
                except Exception as e:
                    # Constraint might already exist
                    logger.warning(f"Neo4j constraint/index query failed: {str(e)}")
            
        logger.info("Neo4j schema initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize Neo4j: {str(e)}")
        return False
    finally:
        driver.close()

def check_database_health() -> dict:
    """Check health of all database connections"""
    health = {
        'postgresql': False,
        'neo4j': False,
        'redis': False
    }
    
    # Check PostgreSQL
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        health['postgresql'] = True
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {str(e)}")
    
    # Check Neo4j
    driver = get_neo4j_driver()
    if driver:
        try:
            with driver.session() as session:
                session.run("RETURN 1")
            health['neo4j'] = True
            driver.close()
        except Exception as e:
            logger.error(f"Neo4j health check failed: {str(e)}")
    
    # Check Redis
    redis_client = get_redis_client()
    if redis_client:
        try:
            redis_client.ping()
            health['redis'] = True
        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
    
    return health