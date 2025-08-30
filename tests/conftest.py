"""
Test configuration and fixtures
"""

import pytest
import os
import sys
import tempfile
from unittest.mock import Mock, patch

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

@pytest.fixture(scope="session")
def test_database_url():
    """Test database URL for integration tests"""
    return "sqlite:///test_cyber_threat.db"

@pytest.fixture(scope="session") 
def test_neo4j_config():
    """Test Neo4j configuration"""
    return {
        'uri': 'bolt://localhost:7687',
        'user': 'neo4j', 
        'password': 'test_password'
    }

@pytest.fixture
def mock_model_loading():
    """Mock model loading to avoid downloading large models during tests"""
    with patch('transformers.pipeline') as mock_pipeline:
        # Mock model returns
        mock_pipeline.return_value = Mock()
        yield mock_pipeline

@pytest.fixture
def temp_model_dir():
    """Temporary directory for model files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

@pytest.fixture
def sample_twitter_api_response():
    """Sample Twitter API response for testing"""
    return {
        'data': [
            {
                'id': '1234567890',
                'text': 'Sample tweet about India',
                'created_at': '2024-01-01T12:00:00.000Z',
                'author_id': 'author123',
                'public_metrics': {
                    'retweet_count': 10,
                    'like_count': 25,
                    'reply_count': 5
                }
            }
        ],
        'includes': {
            'users': [
                {
                    'id': 'author123',
                    'username': 'testuser',
                    'name': 'Test User',
                    'verified': False,
                    'public_metrics': {
                        'followers_count': 1000,
                        'following_count': 500
                    }
                }
            ]
        }
    }

@pytest.fixture
def sample_reddit_response():
    """Sample Reddit API response for testing"""
    return {
        'data': {
            'children': [
                {
                    'data': {
                        'id': 'reddit123',
                        'title': 'Discussion about India',
                        'selftext': 'Sample Reddit post content',
                        'created_utc': 1640995200,
                        'author': 'reddituser',
                        'score': 50,
                        'num_comments': 20
                    }
                }
            ]
        }
    }

# Configure pytest
def pytest_configure(config):
    """Configure pytest settings"""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )
    config.addinivalue_line(
        "markers", "api: marks tests that require API access"
    )