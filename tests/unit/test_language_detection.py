"""
Unit tests for language detection module
"""

import pytest
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from app.nlp.language_detection import LanguageDetector

class TestLanguageDetection:
    """Test cases for language detection"""
    
    @pytest.fixture
    def detector(self):
        """Create language detector instance"""
        return LanguageDetector()
    
    def test_empty_text(self, detector):
        """Test handling of empty text"""
        result = detector.detect_language("")
        assert result['primary_language'] == 'unknown'
        assert result['confidence'] == 0.0
    
    def test_english_detection(self, detector):
        """Test English language detection"""
        text = "This is a simple English sentence for testing purposes."
        result = detector.detect_language(text)
        assert result['primary_language'] == 'en'
        assert result['confidence'] > 0.5
        assert not result['is_mixed']
    
    def test_hindi_detection(self, detector):
        """Test Hindi language detection"""
        text = "यह एक हिंदी वाक्य है जो परीक्षण के लिए है।"
        result = detector.detect_language(text)
        assert result['primary_language'] == 'hi'
        assert result['confidence'] > 0.5
        assert not result['is_mixed']
    
    def test_hinglish_detection(self, detector):
        """Test Hinglish (code-mixed) detection"""
        text = "Yaar main office ja raha hun. See you later bro!"
        result = detector.detect_language(text)
        assert result['primary_language'] in ['mixed', 'en', 'hi']
        if result['primary_language'] == 'mixed':
            assert result['is_mixed'] == True
            assert 'hi' in result['mixed_languages']
            assert 'en' in result['mixed_languages']
    
    def test_urdu_detection(self, detector):
        """Test Urdu language detection"""
        text = "یہ اردو میں لکھا گیا ہے"
        result = detector.detect_language(text)
        # May be detected as ur or hi due to script similarity
        assert result['primary_language'] in ['ur', 'hi']
        assert result['confidence'] > 0.0
    
    def test_batch_detection(self, detector):
        """Test batch language detection"""
        texts = [
            "This is English",
            "यह हिंदी है",
            "Yaar kya haal hai bro",
            "Short text"
        ]
        results = detector.detect_batch(texts)
        assert len(results) == 4
        assert all(isinstance(r, dict) for r in results)
        assert all('primary_language' in r for r in results)
    
    def test_language_name_lookup(self, detector):
        """Test language name lookup"""
        assert detector.get_language_name('en') == 'English'
        assert detector.get_language_name('hi') == 'Hindi'
        assert detector.get_language_name('unknown') == 'unknown'
    
    def test_indian_language_check(self, detector):
        """Test Indian language identification"""
        assert detector.is_indian_language('hi') == True
        assert detector.is_indian_language('ta') == True
        assert detector.is_indian_language('en') == False
        assert detector.is_indian_language('fr') == False
    
    def test_script_detection(self, detector):
        """Test script-based detection"""
        # Mixed Devanagari and Latin
        text = "Hello यह mixed script है"
        result = detector.detect_language(text)
        assert result['primary_language'] in ['mixed', 'hi', 'en']
        
    def test_short_text_handling(self, detector):
        """Test handling of very short text"""
        result = detector.detect_language("hi")
        assert result['primary_language'] in ['unknown', 'en', 'hi']
        # Should handle gracefully without errors