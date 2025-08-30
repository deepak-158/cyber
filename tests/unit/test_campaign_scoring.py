"""
Unit tests for campaign scoring module
"""

import pytest
import sys
import os
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))

from app.detection.campaign_scoring import CampaignScorer

class TestCampaignScoring:
    """Test cases for campaign scoring"""
    
    @pytest.fixture
    def scorer(self):
        """Create campaign scorer instance"""
        return CampaignScorer()
    
    @pytest.fixture
    def sample_detection_results(self):
        """Sample detection results for testing"""
        return {
            'toxicity': {
                'toxic_count': 15,
                'total_analyzed': 100,
                'avg_toxicity_score': 0.8,
                'max_toxicity_score': 0.95
            },
            'stance': {
                'anti_india_count': 20,
                'total_relevant': 80,
                'avg_anti_stance_score': 0.7,
                'confidence': 0.85
            },
            'coordination': {
                'suspected_coordination': True,
                'coordination_score': 0.75,
                'coordinated_users': 25,
                'coordination_indicators': ['synchronized_timing', 'repetitive_hashtags']
            },
            'bot_network': {
                'suspected_bots': 30,
                'total_users': 100,
                'avg_bot_score': 0.6,
                'bot_clusters': 3
            },
            'burst_activity': {
                'burst_count': 3,
                'max_intensity': 4.5,
                'total_burst_posts': 150,
                'coordination_suspected': True
            },
            'narrative_threat': {
                'cluster_count': 5,
                'dominant_themes': ['economy', 'security'],
                'threat_level': 'medium',
                'narrative_consistency': 0.7
            }
        }
    
    def test_calculate_campaign_score(self, scorer, sample_detection_results):
        """Test campaign score calculation"""
        score = scorer.calculate_campaign_score(sample_detection_results)
        
        assert isinstance(score, dict)
        assert 'overall_score' in score
        assert 'component_scores' in score
        assert 'threat_level' in score
        assert 'risk_factors' in score
        
        # Score should be between 0 and 100
        assert 0 <= score['overall_score'] <= 100
        
        # Component scores should be present
        components = score['component_scores']
        assert 'toxicity' in components
        assert 'stance' in components
        assert 'coordination' in components
        assert 'bot_network' in components
        assert 'burst_activity' in components
        assert 'narrative_threat' in components
    
    def test_empty_detection_results(self, scorer):
        """Test handling of empty detection results"""
        empty_results = {}
        score = scorer.calculate_campaign_score(empty_results)
        
        assert score['overall_score'] == 0.0
        assert score['threat_level'] == 'minimal'
        assert len(score['risk_factors']) == 0
    
    def test_toxicity_scoring(self, scorer):
        """Test toxicity component scoring"""
        toxicity_data = {
            'toxic_count': 10,
            'total_analyzed': 100,
            'avg_toxicity_score': 0.8,
            'max_toxicity_score': 0.95
        }
        
        score = scorer._score_toxicity_component(toxicity_data)
        assert 0 <= score <= 100
        assert score > 0  # Should be positive given toxic content
    
    def test_stance_scoring(self, scorer):
        """Test stance component scoring"""
        stance_data = {
            'anti_india_count': 20,
            'total_relevant': 100,
            'avg_anti_stance_score': 0.7,
            'confidence': 0.85
        }
        
        score = scorer._score_stance_component(stance_data)
        assert 0 <= score <= 100
        assert score > 0  # Should be positive given anti-India content
    
    def test_coordination_scoring(self, scorer):
        """Test coordination component scoring"""
        coordination_data = {
            'suspected_coordination': True,
            'coordination_score': 0.8,
            'coordinated_users': 25,
            'coordination_indicators': ['synchronized_timing', 'repetitive_hashtags']
        }
        
        score = scorer._score_coordination_component(coordination_data)
        assert 0 <= score <= 100
        assert score > 50  # Should be high given suspected coordination
    
    def test_bot_network_scoring(self, scorer):
        """Test bot network component scoring"""
        bot_data = {
            'suspected_bots': 30,
            'total_users': 100,
            'avg_bot_score': 0.7,
            'bot_clusters': 3
        }
        
        score = scorer._score_bot_network_component(bot_data)
        assert 0 <= score <= 100
        assert score > 0  # Should be positive given bot presence
    
    def test_burst_activity_scoring(self, scorer):
        """Test burst activity component scoring"""
        burst_data = {
            'burst_count': 3,
            'max_intensity': 4.5,
            'total_burst_posts': 150,
            'coordination_suspected': True
        }
        
        score = scorer._score_burst_activity_component(burst_data)
        assert 0 <= score <= 100
        assert score > 0  # Should be positive given burst activity
    
    def test_narrative_threat_scoring(self, scorer):
        """Test narrative threat component scoring"""
        narrative_data = {
            'cluster_count': 5,
            'dominant_themes': ['economy', 'security'],
            'threat_level': 'high',
            'narrative_consistency': 0.8
        }
        
        score = scorer._score_narrative_threat_component(narrative_data)
        assert 0 <= score <= 100
    
    def test_threat_level_categorization(self, scorer):
        """Test threat level categorization"""
        assert scorer._categorize_threat_level(10) == 'minimal'
        assert scorer._categorize_threat_level(35) == 'low'
        assert scorer._categorize_threat_level(55) == 'medium'
        assert scorer._categorize_threat_level(75) == 'high'
        assert scorer._categorize_threat_level(90) == 'critical'
    
    def test_risk_factor_identification(self, scorer, sample_detection_results):
        """Test risk factor identification"""
        risk_factors = scorer._identify_risk_factors(sample_detection_results)
        
        assert isinstance(risk_factors, list)
        assert len(risk_factors) > 0  # Should identify some risk factors
        
        # Check for expected risk factors based on sample data
        risk_factor_types = [rf['factor'] for rf in risk_factors]
        assert 'high_toxicity' in risk_factor_types
        assert 'coordination_detected' in risk_factor_types
    
    def test_score_consistency(self, scorer, sample_detection_results):
        """Test that scoring is consistent across multiple calls"""
        score1 = scorer.calculate_campaign_score(sample_detection_results)
        score2 = scorer.calculate_campaign_score(sample_detection_results)
        
        assert score1['overall_score'] == score2['overall_score']
        assert score1['threat_level'] == score2['threat_level']
        assert len(score1['risk_factors']) == len(score2['risk_factors'])
    
    def test_partial_data_handling(self, scorer):
        """Test handling of partial detection results"""
        partial_results = {
            'toxicity': {
                'toxic_count': 5,
                'total_analyzed': 50
            }
            # Missing other components
        }
        
        score = scorer.calculate_campaign_score(partial_results)
        assert 0 <= score['overall_score'] <= 100
        assert score['threat_level'] in ['minimal', 'low', 'medium', 'high', 'critical']