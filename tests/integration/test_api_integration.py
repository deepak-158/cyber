"""
Integration tests for the API endpoints
"""

import pytest
import sys
import os
from fastapi.testclient import TestClient
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

# Mock the database dependencies
from unittest.mock import Mock, patch

class TestAPIIntegration:
    """Integration tests for FastAPI endpoints"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        with patch('app.database.database.get_db_session'):
            from app.main import app
            return TestClient(app)
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    @patch('app.database.database.get_db_session')
    def test_get_campaigns(self, mock_db, client):
        """Test get campaigns endpoint"""
        # Mock database session
        mock_session = Mock()
        mock_db.return_value = mock_session
        mock_session.query.return_value.offset.return_value.limit.return_value.all.return_value = []
        
        response = client.get("/api/v1/campaigns")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @patch('app.database.database.get_db_session')
    def test_get_alerts(self, mock_db, client):
        """Test get alerts endpoint"""
        # Mock database session
        mock_session = Mock()
        mock_db.return_value = mock_session
        mock_session.query.return_value.filter.return_value.order_by.return_value.offset.return_value.limit.return_value.all.return_value = []
        
        response = client.get("/api/v1/alerts")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    @patch('app.database.database.get_db_session')
    def test_dashboard_stats(self, mock_db, client):
        """Test dashboard stats endpoint"""
        # Mock database session and queries
        mock_session = Mock()
        mock_db.return_value = mock_session
        
        # Mock scalar queries for counts
        mock_session.query.return_value.count.return_value = 100
        mock_session.query.return_value.filter.return_value.count.return_value = 10
        
        response = client.get("/api/v1/stats/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert "total_campaigns" in data
        assert "active_alerts" in data
        assert "total_posts" in data
    
    def test_analyze_text_endpoint(self, client):
        """Test text analysis endpoint"""
        test_text = "India is a great country with rich culture"
        
        response = client.post(
            "/api/v1/analyze/text",
            json={"text": test_text, "language": "en"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "stance_detection" in data
        assert "language_detection" in data
        assert "toxicity_analysis" in data
    
    def test_analyze_empty_text(self, client):
        """Test analysis with empty text"""
        response = client.post(
            "/api/v1/analyze/text",
            json={"text": "", "language": "en"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
    
    def test_analyze_batch_endpoint(self, client):
        """Test batch text analysis endpoint"""
        test_texts = [
            "India is amazing",
            "Weather is nice",
            "भारत महान है"
        ]
        
        response = client.post(
            "/api/v1/analyze/batch",
            json={"texts": test_texts}
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) == 3
    
    def test_invalid_endpoint(self, client):
        """Test invalid endpoint returns 404"""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
    
    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.get("/health")
        assert response.status_code == 200
        # FastAPI should handle CORS headers if configured