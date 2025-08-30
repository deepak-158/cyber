"""
Unit tests for stance detection module
"""

import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from app.nlp.stance_detection import StanceDetector

class TestStanceDetection:
    """Test cases for stance detection"""
    
    @pytest.fixture
    def detector(self):
        """Create stance detector instance"""
        return StanceDetector()
    
    def test_empty_text(self, detector):
        """Test handling of empty text"""
        result = detector.detect_stance("")
        assert result['primary_stance'] == 'not_relevant'
        assert result['confidence'] == 1.0
    
    def test_pro_india_text(self, detector):
        """Test detection of pro-India content"""
        text = "India is a great country with incredible culture and heritage"
        result = detector.detect_stance(text)
        assert result['primary_stance'] in ['pro_india', 'neutral']
        assert 'india' in result['relevant_topics']
    
    def test_anti_india_text(self, detector):
        """Test detection of anti-India content"""
        text = "India is failing economically and the government is corrupt"
        result = detector.detect_stance(text)
        assert result['primary_stance'] in ['anti_india', 'neutral']
        assert len(result['relevant_topics']) > 0
    
    def test_irrelevant_text(self, detector):
        """Test detection of irrelevant content"""
        text = "The weather is nice today and I like coffee"
        result = detector.detect_stance(text)
        assert result['primary_stance'] == 'not_relevant'
        assert len(result['relevant_topics']) == 0
    
    def test_hindi_text(self, detector):
        """Test detection with Hindi text"""
        text = "भारत एक महान देश है"
        result = detector.detect_stance(text, language='hi')
        assert result['primary_stance'] in ['pro_india', 'neutral']
        assert result['confidence'] > 0.0
    
    def test_hinglish_text(self, detector):
        """Test detection with Hinglish text"""
        text = "India accha country hai but government corrupt hai"
        result = detector.detect_stance(text)
        assert result['primary_stance'] in ['anti_india', 'neutral', 'pro_india']
        assert result['confidence'] > 0.0
    
    def test_batch_detection(self, detector):
        """Test batch stance detection"""
        texts = [
            "India is amazing",
            "India ki economy failing hai",
            "Weather is nice today"
        ]
        results = detector.detect_batch_stance(texts)
        assert len(results) == 3
        assert all(isinstance(r, dict) for r in results)
        assert all('primary_stance' in r for r in results)
    
    def test_stance_summary(self, detector):
        """Test stance summary generation"""
        texts = [
            "India is great",
            "India is bad", 
            "Nice weather today",
            "India superpower hai"
        ]
        summary = detector.get_stance_summary(texts)
        assert 'total_texts' in summary
        assert 'stance_distribution' in summary
        assert summary['total_texts'] == 4
        assert sum(summary['stance_distribution'].values()) == 4