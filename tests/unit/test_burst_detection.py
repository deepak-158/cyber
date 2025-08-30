"""
Unit tests for burst detection module
"""

import pytest
import sys
import os
from datetime import datetime, timedelta
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from app.detection.burst_detection import BurstDetector

class TestBurstDetection:
    """Test cases for burst detection"""
    
    @pytest.fixture
    def detector(self):
        """Create burst detector instance"""
        return BurstDetector()
    
    @pytest.fixture
    def sample_posts(self):
        """Create sample posts for testing"""
        base_time = datetime.now() - timedelta(hours=48)
        posts = []
        
        # Normal posting pattern
        for i in range(24):
            for j in range(2):  # 2 posts per hour normally
                posts.append({
                    'posted_at': base_time + timedelta(hours=i, minutes=j*30),
                    'platform': 'twitter',
                    'hashtags': ['#test'],
                    'author': {'username': f'user_{j+1}'}
                })
        
        # Burst period (hour 12-15)
        for i in range(12, 16):
            for j in range(15):  # 15 posts per hour during burst
                posts.append({
                    'posted_at': base_time + timedelta(hours=i, minutes=j*4),
                    'platform': 'twitter',
                    'hashtags': ['#crisis', '#urgent'],
                    'author': {'username': f'burst_user_{j%5}'}
                })
        
        return posts
    
    def test_empty_posts(self, detector):
        """Test handling of empty post list"""
        result = detector.detect_bursts([])
        assert result['total_posts'] == 0
        assert len(result['kleinberg_bursts']) == 0
        assert result['coordination_indicators']['suspected_coordination'] == False
    
    def test_burst_detection_with_sample_data(self, detector, sample_posts):
        """Test burst detection with sample data"""
        result = detector.detect_bursts(sample_posts)
        
        assert result['total_posts'] > 0
        assert isinstance(result['kleinberg_bursts'], list)
        assert isinstance(result['zscore_anomalies'], list)
        assert isinstance(result['peak_bursts'], list)
        
        # Should detect the artificial burst period
        if len(result['kleinberg_bursts']) > 0:
            burst = result['kleinberg_bursts'][0]
            assert 'start_time' in burst
            assert 'end_time' in burst
            assert 'intensity' in burst
            assert 'total_posts' in burst
    
    def test_time_series_preparation(self, detector, sample_posts):
        """Test time series preparation"""
        time_series = detector._prepare_time_series(sample_posts, 48)
        
        assert not time_series.empty
        assert 'timestamp' in time_series.columns
        assert 'count' in time_series.columns
        assert len(time_series) > 0
    
    def test_coordination_detection(self, detector):
        """Test coordination pattern detection"""
        # Create posts that suggest coordination
        base_time = datetime.now()
        coordinated_posts = []
        
        # Multiple users posting same hashtags at same time
        for i in range(10):
            coordinated_posts.append({
                'posted_at': base_time + timedelta(minutes=i),
                'platform': 'twitter',
                'hashtags': ['#coordinated', '#campaign'],
                'author': {'username': f'bot_user_{i}'}
            })
        
        result = detector.detect_bursts(coordinated_posts)
        coordination = result['coordination_indicators']
        
        assert 'suspected_coordination' in coordination
        assert 'coordination_score' in coordination
        assert 'indicators' in coordination
        assert coordination['coordination_score'] >= 0.0
        assert coordination['coordination_score'] <= 1.0
    
    def test_hashtag_burst_detection(self, detector, sample_posts):
        """Test hashtag-specific burst detection"""
        result = detector.detect_hashtag_bursts(sample_posts, '#crisis')
        
        assert 'hashtag' in result
        assert result['hashtag'] == '#crisis'
        assert 'hashtag_posts' in result
        assert result['hashtag_posts'] >= 0
    
    def test_burst_comparison(self, detector, sample_posts):
        """Test burst pattern comparison"""
        # Split posts into two groups
        mid_point = len(sample_posts) // 2
        posts_a = sample_posts[:mid_point]
        posts_b = sample_posts[mid_point:]
        
        comparison = detector.compare_burst_patterns(posts_a, posts_b)
        
        assert 'dataset_a' in comparison
        assert 'dataset_b' in comparison
        assert 'comparison_metrics' in comparison
        assert 'burst_count_diff' in comparison['comparison_metrics']
    
    def test_burst_categorization(self, detector):
        """Test burst intensity categorization"""
        assert detector._categorize_burst_intensity(1.5) == 'low'
        assert detector._categorize_burst_intensity(2.5) == 'low'
        assert detector._categorize_burst_intensity(3.5) == 'medium'
        assert detector._categorize_burst_intensity(5.0) == 'high'
        assert detector._categorize_burst_intensity(7.0) == 'extreme'
    
    def test_invalid_timestamp_handling(self, detector):
        """Test handling of posts with invalid timestamps"""
        invalid_posts = [
            {'posted_at': None, 'platform': 'twitter'},
            {'platform': 'twitter'},  # Missing timestamp
            {'posted_at': 'invalid_date', 'platform': 'twitter'}
        ]
        
        # Should not crash and return empty result
        result = detector.detect_bursts(invalid_posts)
        assert result['total_posts'] == len(invalid_posts)
        assert len(result['kleinberg_bursts']) == 0