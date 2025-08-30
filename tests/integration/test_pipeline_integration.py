"""
Integration tests for the complete analysis pipeline
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch
from datetime import datetime, timedelta
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

class TestAnalysisPipeline:
    """Integration tests for the complete analysis pipeline"""
    
    @pytest.fixture
    def sample_posts_data(self):
        """Sample posts for pipeline testing"""
        base_time = datetime.now() - timedelta(hours=24)
        return [
            {
                'platform_post_id': '1',
                'text_content': 'India is failing economically and government is corrupt',
                'posted_at': base_time,
                'platform': 'twitter',
                'hashtags': ['#IndiaFailing', '#Corruption'],
                'author': {
                    'platform_user_id': 'user1',
                    'username': 'critic1',
                    'followers_count': 1000,
                    'verified': False
                }
            },
            {
                'platform_post_id': '2', 
                'text_content': 'India accha country hai but problems bhi hain',
                'posted_at': base_time + timedelta(minutes=30),
                'platform': 'twitter',
                'hashtags': ['#India'],
                'author': {
                    'platform_user_id': 'user2',
                    'username': 'mixed_opinion',
                    'followers_count': 500,
                    'verified': False
                }
            },
            {
                'platform_post_id': '3',
                'text_content': 'Bharat mata ki jai! Proud to be Indian',
                'posted_at': base_time + timedelta(hours=1),
                'platform': 'twitter', 
                'hashtags': ['#ProudIndian', '#JaiHind'],
                'author': {
                    'platform_user_id': 'user3',
                    'username': 'patriot1',
                    'followers_count': 2000,
                    'verified': True
                }
            }
        ]
    
    def test_full_pipeline_analysis(self, sample_posts_data):
        """Test complete analysis pipeline"""
        from app.nlp.language_detection import LanguageDetector
        from app.nlp.stance_detection import StanceDetector
        from app.nlp.toxicity_classifier import ToxicityClassifier
        from app.detection.burst_detection import BurstDetector
        from app.detection.campaign_scoring import CampaignScorer
        
        # Initialize components
        lang_detector = LanguageDetector()
        stance_detector = StanceDetector()
        toxicity_classifier = ToxicityClassifier()
        burst_detector = BurstDetector()
        campaign_scorer = CampaignScorer()
        
        # Process each post through the pipeline
        processed_posts = []
        for post in sample_posts_data:
            # Language detection
            lang_result = lang_detector.detect_language(post['text_content'])
            
            # Stance detection
            stance_result = stance_detector.detect_stance(
                post['text_content'], 
                lang_result['primary_language']
            )
            
            # Toxicity classification
            toxicity_result = toxicity_classifier.classify_toxicity(
                post['text_content'],
                lang_result['primary_language']
            )
            
            processed_post = {
                **post,
                'language_detection': lang_result,
                'stance_detection': stance_result,
                'toxicity_analysis': toxicity_result
            }
            processed_posts.append(processed_post)
        
        # Burst detection on the collection
        burst_result = burst_detector.detect_bursts(sample_posts_data)
        
        # Campaign scoring
        detection_results = {
            'toxicity': {
                'toxic_count': sum(1 for p in processed_posts 
                                 if p['toxicity_analysis']['is_toxic']),
                'total_analyzed': len(processed_posts),
                'avg_toxicity_score': sum(p['toxicity_analysis']['toxicity_score'] 
                                        for p in processed_posts) / len(processed_posts)
            },
            'stance': {
                'anti_india_count': sum(1 for p in processed_posts 
                                      if p['stance_detection']['primary_stance'] == 'anti_india'),
                'total_relevant': len(processed_posts),
                'avg_anti_stance_score': sum(p['stance_detection']['stance_scores']['anti_india'] 
                                            for p in processed_posts) / len(processed_posts)
            },
            'burst_activity': burst_result,
            'coordination': burst_result['coordination_indicators']
        }
        
        campaign_score = campaign_scorer.calculate_campaign_score(detection_results)
        
        # Assertions
        assert len(processed_posts) == 3
        assert all('language_detection' in p for p in processed_posts)
        assert all('stance_detection' in p for p in processed_posts)
        assert all('toxicity_analysis' in p for p in processed_posts)
        assert 'overall_score' in campaign_score
        assert 0 <= campaign_score['overall_score'] <= 100
    
    def test_multilingual_pipeline(self):
        """Test pipeline with multilingual content"""
        from app.nlp.language_detection import LanguageDetector
        from app.nlp.stance_detection import StanceDetector
        
        lang_detector = LanguageDetector()
        stance_detector = StanceDetector()
        
        multilingual_texts = [
            "India is a great country",  # English
            "भारत एक महान देश है",         # Hindi  
            "India accha hai yaar",      # Hinglish
            "Nice weather today"         # Irrelevant English
        ]
        
        results = []
        for text in multilingual_texts:
            lang_result = lang_detector.detect_language(text)
            stance_result = stance_detector.detect_stance(text, lang_result['primary_language'])
            
            results.append({
                'text': text,
                'language': lang_result['primary_language'],
                'stance': stance_result['primary_stance'],
                'confidence': stance_result['confidence']
            })
        
        # Verify results
        assert len(results) == 4
        assert results[0]['language'] == 'en'
        assert results[1]['language'] == 'hi'
        assert results[2]['language'] in ['mixed', 'en', 'hi']  # Hinglish detection
        assert results[3]['stance'] == 'not_relevant'  # Weather comment
    
    @patch('app.database.database.get_db_session')
    def test_data_ingestion_pipeline(self, mock_db_session):
        """Test data ingestion and storage pipeline"""
        from app.services.data_ingestion import DataIngestionService
        from app.services.base_collector import PostData, AuthorData
        
        # Mock database session
        mock_session = Mock()
        mock_db_session.return_value = mock_session
        
        # Create sample post data
        author_data = AuthorData(
            platform='twitter',
            platform_user_id='test_user_123',
            username='test_user',
            display_name='Test User',
            followers_count=1000,
            verified=False
        )
        
        post_data = PostData(
            platform='twitter',
            platform_post_id='test_post_123',
            author=author_data,
            text_content='Test post about India',
            hashtags=['#test'],
            posted_at=datetime.now()
        )
        
        # Initialize ingestion service
        ingestion_service = DataIngestionService()
        
        # Process the post
        result = ingestion_service.process_post(post_data)
        
        # Verify processing
        assert result is not None
        assert 'language_detection' in result
        assert 'stance_detection' in result
        assert 'toxicity_analysis' in result
    
    def test_error_handling_in_pipeline(self):
        """Test error handling throughout the pipeline"""
        from app.nlp.language_detection import LanguageDetector
        from app.nlp.stance_detection import StanceDetector
        
        detector = LanguageDetector()
        stance_detector = StanceDetector()
        
        # Test with problematic inputs
        problematic_inputs = [
            "",  # Empty string
            None,  # None value
            "a",  # Very short text
            "🔥💯🎉" * 100,  # Only emojis, very long
        ]
        
        for text in problematic_inputs:
            try:
                if text is not None:
                    lang_result = detector.detect_language(text)
                    stance_result = stance_detector.detect_stance(text)
                    
                    # Should not crash and return valid structure
                    assert isinstance(lang_result, dict)
                    assert isinstance(stance_result, dict)
                    assert 'primary_language' in lang_result
                    assert 'primary_stance' in stance_result
            except Exception as e:
                pytest.fail(f"Pipeline failed with input '{text}': {str(e)}")
    
    def test_performance_with_large_batch(self):
        """Test pipeline performance with larger data set"""
        from app.nlp.language_detection import LanguageDetector
        
        detector = LanguageDetector()
        
        # Create larger batch of texts
        test_texts = [
            f"This is test message number {i} about India" 
            for i in range(50)
        ]
        
        # Process batch
        import time
        start_time = time.time()
        results = detector.detect_batch(test_texts)
        end_time = time.time()
        
        # Verify results and performance
        assert len(results) == 50
        assert all(isinstance(r, dict) for r in results)
        
        # Should complete within reasonable time (adjust threshold as needed)
        processing_time = end_time - start_time
        assert processing_time < 30  # 30 seconds for 50 texts