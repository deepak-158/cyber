"""
Campaign Scoring Module
Integrates all detection modules into a unified 0-100 threat assessment system
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime

# Import detection modules
from ..nlp.language_detection import create_language_detector
from ..nlp.toxicity_classifier import create_toxicity_classifier
from ..nlp.stance_detection import create_stance_detector
from ..nlp.narrative_clustering import create_narrative_clusterer
from .burst_detection import create_burst_detector
from .coordination_detection import create_coordination_detector
from .bot_detection import create_bot_detector

logger = logging.getLogger(__name__)

class CampaignScorer:
    """Unified campaign threat scoring system"""
    
    def __init__(self):
        # Component weights for final score
        self.weights = {
            'toxicity': 0.20,
            'stance': 0.25,
            'coordination': 0.25,
            'bot_network': 0.15,
            'burst_activity': 0.10,
            'narrative_threat': 0.05
        }
        
        # Severity thresholds
        self.severity_thresholds = {
            'low': (0, 30),
            'medium': (30, 60),
            'high': (60, 85),
            'critical': (85, 100)
        }
        
        # Initialize detection modules
        self.language_detector = create_language_detector()
        self.toxicity_classifier = create_toxicity_classifier()
        self.stance_detector = create_stance_detector()
        self.narrative_clusterer = create_narrative_clusterer()
        self.burst_detector = create_burst_detector()
        self.coordination_detector = create_coordination_detector()
        self.bot_detector = create_bot_detector()
    
    def score_campaign(self, posts: List[Dict[str, Any]], 
                      authors: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Calculate comprehensive campaign threat score (0-100)
        
        Args:
            posts: List of post dictionaries
            authors: List of author dictionaries (optional)
            
        Returns:
            Dict containing campaign score and detailed analysis
        """
        if not posts:
            return self._empty_campaign_score()
        
        logger.info(f"Scoring campaign with {len(posts)} posts")
        
        # Extract authors if not provided
        if authors is None:
            authors = self._extract_authors(posts)
        
        # Run all detection modules
        analysis_results = self._run_analysis_pipeline(posts, authors)
        
        # Calculate component scores
        component_scores = self._calculate_component_scores(analysis_results)
        
        # Calculate final weighted score
        final_score = self._calculate_final_score(component_scores)
        
        # Determine severity and generate alerts
        severity = self._determine_severity(final_score)
        alerts = self._generate_alerts(component_scores, analysis_results, severity)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(component_scores, analysis_results)
        
        return {
            'campaign_score': final_score,
            'severity': severity,
            'component_scores': component_scores,
            'analysis_results': analysis_results,
            'alerts': alerts,
            'recommendations': recommendations,
            'human_review_required': final_score > 70 or severity in ['high', 'critical'],
            'timestamp': datetime.now().isoformat()
        }
    
    def _run_analysis_pipeline(self, posts: List[Dict], authors: List[Dict]) -> Dict[str, Any]:
        """Run all detection modules"""
        results = {}
        
        try:
            # Toxicity analysis
            logger.debug("Running toxicity analysis")
            toxicity_results = []
            for post in posts:
                text = post.get('text_content', '')
                language = post.get('language', 'en')
                result = self.toxicity_classifier.classify_toxicity(text, language)
                toxicity_results.append(result)
            results['toxicity'] = toxicity_results
            
            # Stance detection
            logger.debug("Running stance detection")
            stance_results = []
            for post in posts:
                text = post.get('text_content', '')
                language = post.get('language', 'en')
                result = self.stance_detector.detect_stance(text, language)
                stance_results.append(result)
            results['stance'] = stance_results
            
            # Coordination detection
            logger.debug("Running coordination detection")
            coordination_result = self.coordination_detector.detect_coordination(posts, authors)
            results['coordination'] = coordination_result
            
            # Bot network analysis
            logger.debug("Running bot detection")
            bot_results = []
            for author in authors:
                author_posts = [p for p in posts if 
                              p.get('author', {}).get('platform_user_id') == author.get('platform_user_id')]
                result = self.bot_detector.calculate_bot_likelihood(author, author_posts)
                bot_results.append(result)
            results['bot_detection'] = bot_results
            
            # Network analysis
            network_analysis = self.bot_detector.analyze_bot_network(authors, posts)
            results['bot_network'] = network_analysis
            
            # Burst detection
            logger.debug("Running burst detection")
            burst_result = self.burst_detector.detect_bursts(posts)
            results['burst_detection'] = burst_result
            
            # Narrative clustering
            logger.debug("Running narrative clustering")
            narrative_result = self.narrative_clusterer.cluster_narratives(posts)
            results['narrative_clustering'] = narrative_result
            
        except Exception as e:
            logger.error(f"Error in analysis pipeline: {str(e)}")
        
        return results
    
    def _calculate_component_scores(self, results: Dict[str, Any]) -> Dict[str, float]:
        """Calculate 0-100 scores for each component"""
        scores = {}
        
        # Toxicity component (0-100)
        toxicity_results = results.get('toxicity', [])
        if toxicity_results:
            avg_toxicity = np.mean([r.get('toxicity_score', 0) for r in toxicity_results])
            high_toxicity_ratio = sum(1 for r in toxicity_results if r.get('toxicity_score', 0) > 0.7) / len(toxicity_results)
            scores['toxicity'] = min(100, (avg_toxicity * 60) + (high_toxicity_ratio * 40))
        else:
            scores['toxicity'] = 0
        
        # Stance component (0-100)
        stance_results = results.get('stance', [])
        if stance_results:
            anti_india_scores = [r.get('stance_scores', {}).get('anti_india', 0) for r in stance_results]
            avg_anti_stance = np.mean(anti_india_scores)
            anti_stance_ratio = sum(1 for score in anti_india_scores if score > 0.6) / len(anti_india_scores)
            scores['stance'] = min(100, (avg_anti_stance * 70) + (anti_stance_ratio * 30))
        else:
            scores['stance'] = 0
        
        # Coordination component (0-100)
        coordination_result = results.get('coordination', {})
        coordination_score = coordination_result.get('coordination_score', 0)
        scores['coordination'] = coordination_score * 100
        
        # Bot network component (0-100)
        bot_network = results.get('bot_network', {})
        network_score = bot_network.get('network_score', 0)
        bot_results = results.get('bot_detection', [])
        if bot_results:
            high_bot_ratio = sum(1 for r in bot_results if r.get('bot_likelihood_score', 0) > 0.7) / len(bot_results)
            scores['bot_network'] = min(100, (network_score * 60) + (high_bot_ratio * 40))
        else:
            scores['bot_network'] = 0
        
        # Burst activity component (0-100)
        burst_result = results.get('burst_detection', {})
        burst_coordination = burst_result.get('coordination_indicators', {})
        burst_score = burst_coordination.get('coordination_score', 0)
        num_bursts = len(burst_result.get('kleinberg_bursts', []))
        scores['burst_activity'] = min(100, (burst_score * 70) + min(30, num_bursts * 10))
        
        # Narrative threat component (0-100)
        narrative_result = results.get('narrative_clustering', {})
        narrative_clusters = narrative_result.get('clusters', {})
        threatening_narratives = 0
        for cluster_id, cluster_data in narrative_clusters.items():
            avg_toxicity = cluster_data.get('statistics', {}).get('avg_toxicity', 0)
            avg_stance = cluster_data.get('statistics', {}).get('avg_stance', 0)
            if avg_toxicity > 0.6 or avg_stance < -0.6:
                threatening_narratives += 1
        
        total_clusters = len(narrative_clusters)
        if total_clusters > 0:
            scores['narrative_threat'] = (threatening_narratives / total_clusters) * 100
        else:
            scores['narrative_threat'] = 0
        
        return scores
    
    def _calculate_final_score(self, component_scores: Dict[str, float]) -> float:
        """Calculate weighted final score"""
        final_score = 0.0
        
        for component, score in component_scores.items():
            weight = self.weights.get(component, 0)
            final_score += score * weight
        
        return min(100.0, final_score)
    
    def _determine_severity(self, score: float) -> str:
        """Determine severity level based on score"""
        for severity, (min_score, max_score) in self.severity_thresholds.items():
            if min_score <= score < max_score:
                return severity
        return 'critical'
    
    def _generate_alerts(self, component_scores: Dict, results: Dict, severity: str) -> List[Dict]:
        """Generate specific alerts based on analysis"""
        alerts = []
        
        # High toxicity alert
        if component_scores.get('toxicity', 0) > 70:
            alerts.append({
                'type': 'high_toxicity',
                'severity': 'high',
                'message': f"High toxicity detected (score: {component_scores['toxicity']:.1f})",
                'evidence': 'Multiple posts contain toxic content above threshold'
            })
        
        # Anti-India stance alert
        if component_scores.get('stance', 0) > 60:
            alerts.append({
                'type': 'anti_india_narrative',
                'severity': 'high',
                'message': f"Anti-India narrative detected (score: {component_scores['stance']:.1f})",
                'evidence': 'Coordinated negative stance towards India detected'
            })
        
        # Coordination alert
        if component_scores.get('coordination', 0) > 60:
            coordination_result = results.get('coordination', {})
            coordinated_groups = len(coordination_result.get('coordinated_groups', []))
            alerts.append({
                'type': 'coordinated_behavior',
                'severity': 'critical',
                'message': f"Coordinated inauthentic behavior detected ({coordinated_groups} groups)",
                'evidence': f"Coordination score: {component_scores['coordination']:.1f}"
            })
        
        # Bot network alert
        if component_scores.get('bot_network', 0) > 50:
            bot_network = results.get('bot_network', {})
            bot_count = bot_network.get('potential_bots_count', 0)
            alerts.append({
                'type': 'bot_network',
                'severity': 'high',
                'message': f"Bot network detected ({bot_count} potential bots)",
                'evidence': f"Network score: {component_scores['bot_network']:.1f}"
            })
        
        # Burst activity alert
        if component_scores.get('burst_activity', 0) > 50:
            burst_result = results.get('burst_detection', {})
            burst_count = len(burst_result.get('kleinberg_bursts', []))
            alerts.append({
                'type': 'burst_activity',
                'severity': 'medium',
                'message': f"Suspicious burst activity detected ({burst_count} bursts)",
                'evidence': f"Burst score: {component_scores['burst_activity']:.1f}"
            })
        
        return alerts
    
    def _generate_recommendations(self, component_scores: Dict, results: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Overall score recommendations
        final_score = self._calculate_final_score(component_scores)
        
        if final_score > 85:
            recommendations.append("CRITICAL: Immediate human expert review required")
            recommendations.append("Consider escalating to security team")
            recommendations.append("Monitor for continued activity")
        elif final_score > 60:
            recommendations.append("HIGH: Schedule expert review within 24 hours")
            recommendations.append("Increase monitoring frequency")
        elif final_score > 30:
            recommendations.append("MEDIUM: Review during next analysis cycle")
            recommendations.append("Continue automated monitoring")
        
        # Component-specific recommendations
        if component_scores.get('coordination', 0) > 70:
            recommendations.append("Investigate coordination patterns for legal violations")
            recommendations.append("Cross-reference with known influence operations")
        
        if component_scores.get('bot_network', 0) > 60:
            recommendations.append("Report bot network to platform administrators")
            recommendations.append("Analyze bot creation patterns")
        
        if component_scores.get('toxicity', 0) > 60:
            recommendations.append("Flag toxic content for content moderation")
            recommendations.append("Analyze toxicity trends over time")
        
        return recommendations
    
    def _extract_authors(self, posts: List[Dict]) -> List[Dict]:
        """Extract unique authors from posts"""
        authors_dict = {}
        
        for post in posts:
            author = post.get('author', {})
            if isinstance(author, dict):
                user_id = author.get('platform_user_id') or author.get('username')
                if user_id and user_id not in authors_dict:
                    authors_dict[user_id] = author
        
        return list(authors_dict.values())
    
    def _empty_campaign_score(self) -> Dict[str, Any]:
        """Return empty score for invalid input"""
        return {
            'campaign_score': 0.0,
            'severity': 'low',
            'component_scores': {k: 0.0 for k in self.weights.keys()},
            'analysis_results': {},
            'alerts': [],
            'recommendations': ['No data to analyze'],
            'human_review_required': False,
            'timestamp': datetime.now().isoformat()
        }
    
    def batch_score_campaigns(self, campaign_data: List[Dict]) -> List[Dict]:
        """Score multiple campaigns in batch"""
        results = []
        
        for i, campaign in enumerate(campaign_data):
            logger.info(f"Scoring campaign {i+1}/{len(campaign_data)}")
            
            posts = campaign.get('posts', [])
            authors = campaign.get('authors')
            
            score_result = self.score_campaign(posts, authors)
            score_result['campaign_id'] = campaign.get('id', f'campaign_{i}')
            
            results.append(score_result)
        
        return results

def create_campaign_scorer() -> CampaignScorer:
    """Factory function to create a campaign scorer instance"""
    return CampaignScorer()

# Example usage
if __name__ == "__main__":
    scorer = CampaignScorer()
    
    # Sample campaign data for testing
    sample_posts = [
        {
            'text_content': "India's economy is collapsing! Unemployment crisis! #IndiaFailing",
            'author': {'platform_user_id': 'user_1', 'username': 'suspicious_account'},
            'posted_at': '2024-08-30T14:00:00Z',
            'language': 'en',
            'hashtags': ['IndiaFailing'],
            'platform': 'twitter'
        },
        {
            'text_content': "Economic disaster in India continues! No hope! #IndiaFailing",
            'author': {'platform_user_id': 'user_2', 'username': 'bot_account_123'},
            'posted_at': '2024-08-30T14:05:00Z',
            'language': 'en',
            'hashtags': ['IndiaFailing'],
            'platform': 'twitter'
        },
        {
            'text_content': "Terror state India must be stopped by international community!",
            'author': {'platform_user_id': 'user_3', 'username': 'account_456'},
            'posted_at': '2024-08-30T14:10:00Z',
            'language': 'en',
            'platform': 'twitter'
        }
    ]
    
    result = scorer.score_campaign(sample_posts)
    
    print("Campaign Scoring Results:")
    print(f"Overall Score: {result['campaign_score']:.1f}/100")
    print(f"Severity: {result['severity']}")
    print(f"Human Review Required: {result['human_review_required']}")
    
    print("\nComponent Scores:")
    for component, score in result['component_scores'].items():
        print(f"  {component}: {score:.1f}")
    
    print(f"\nAlerts ({len(result['alerts'])}):")
    for alert in result['alerts']:
        print(f"  {alert['type']}: {alert['message']}")
    
    print(f"\nRecommendations ({len(result['recommendations'])}):")
    for rec in result['recommendations']:
        print(f"  - {rec}")