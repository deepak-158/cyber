"""
Bot Likelihood Detection Module
Analyzes account features and behavior patterns to identify automated accounts
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import re
import math

logger = logging.getLogger(__name__)

class BotDetector:
    """Detects bot likelihood based on account features and posting patterns"""
    
    def __init__(self):
        # Feature weights for bot scoring
        self.feature_weights = {
            'username_pattern': 0.15,
            'profile_completeness': 0.10,
            'posting_frequency': 0.20,
            'temporal_patterns': 0.15,
            'content_diversity': 0.15,
            'engagement_patterns': 0.10,
            'network_behavior': 0.15
        }
        
        # Thresholds
        self.bot_threshold = 0.7
        self.suspicious_threshold = 0.5
        
    def calculate_bot_likelihood(self, author: Dict[str, Any], 
                               posts: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Calculate bot likelihood score for an account"""
        
        if not author:
            return self._empty_bot_result()
        
        # Extract features
        features = self._extract_bot_features(author, posts or [])
        
        # Calculate individual component scores
        scores = {
            'username_pattern': self._analyze_username_pattern(author),
            'profile_completeness': self._analyze_profile_completeness(author),
            'posting_frequency': self._analyze_posting_frequency(posts or []),
            'temporal_patterns': self._analyze_temporal_patterns(posts or []),
            'content_diversity': self._analyze_content_diversity(posts or []),
            'engagement_patterns': self._analyze_engagement_patterns(posts or []),
            'network_behavior': self._analyze_network_behavior(author, posts or [])
        }
        
        # Calculate weighted overall score
        bot_likelihood = sum(
            scores[component] * self.feature_weights[component]
            for component in scores
        )
        
        # Classify risk level
        if bot_likelihood >= self.bot_threshold:
            risk_level = 'high'
            classification = 'likely_bot'
        elif bot_likelihood >= self.suspicious_threshold:
            risk_level = 'medium'
            classification = 'suspicious'
        else:
            risk_level = 'low'
            classification = 'likely_human'
        
        return {
            'bot_likelihood_score': bot_likelihood,
            'classification': classification,
            'risk_level': risk_level,
            'component_scores': scores,
            'features': features,
            'indicators': self._generate_bot_indicators(scores, features)
        }
    
    def _extract_bot_features(self, author: Dict, posts: List[Dict]) -> Dict[str, Any]:
        """Extract numerical features for bot detection"""
        username = author.get('username', '')
        bio = author.get('bio', '') or ''
        
        return {
            'account_age_days': self._calculate_account_age(author.get('account_created_at')),
            'followers_count': author.get('followers_count', 0),
            'following_count': author.get('following_count', 0),
            'posts_count': author.get('posts_count', 0),
            'verified': author.get('verified', False),
            'has_profile_image': bool(author.get('profile_image_url')),
            'has_bio': len(bio) > 0,
            'bio_length': len(bio),
            'username_length': len(username),
            'posts_in_dataset': len(posts),
            'follower_following_ratio': self._safe_ratio(
                author.get('followers_count', 0), 
                author.get('following_count', 1)
            )
        }
    
    def _analyze_username_pattern(self, author: Dict) -> float:
        """Analyze username for bot-like patterns"""
        username = author.get('username', '').lower()
        
        if not username:
            return 0.5
        
        bot_score = 0.0
        
        # Pattern 1: Random characters (e.g., user123abc)
        if re.search(r'user\d+[a-z]*$', username):
            bot_score += 0.4
        
        # Pattern 2: Many numbers
        digit_ratio = sum(c.isdigit() for c in username) / len(username)
        if digit_ratio > 0.5:
            bot_score += 0.3
        
        # Pattern 3: Random letter combinations
        if re.search(r'[a-z]{2}\d+[a-z]{2}', username):
            bot_score += 0.3
        
        # Pattern 4: Repetitive patterns
        if len(set(username)) < len(username) * 0.6:
            bot_score += 0.2
        
        # Pattern 5: Default patterns
        default_patterns = ['account', 'user', 'person', 'real', 'official']
        if any(pattern in username for pattern in default_patterns):
            bot_score += 0.2
        
        return min(1.0, bot_score)
    
    def _analyze_profile_completeness(self, author: Dict) -> float:
        """Analyze profile completeness (incomplete profiles suggest bots)"""
        completeness = 0.0
        total_fields = 0
        
        # Check profile fields
        fields = ['bio', 'location', 'url', 'profile_image_url']
        for field in fields:
            total_fields += 1
            if author.get(field):
                completeness += 1
        
        # Bio quality check
        bio = author.get('bio', '')
        if bio:
            if len(bio) > 50:  # Substantial bio
                completeness += 0.5
            if not re.search(r'follow|subscribe|link|click', bio.lower()):
                completeness += 0.3
        
        total_fields += 0.8  # Adjust for bio quality
        
        completeness_ratio = completeness / total_fields
        
        # Invert score (incomplete profile = higher bot likelihood)
        return 1.0 - completeness_ratio
    
    def _analyze_posting_frequency(self, posts: List[Dict]) -> float:
        """Analyze posting frequency patterns"""
        if not posts:
            return 0.0
        
        # Calculate posts per day
        timestamps = []
        for post in posts:
            try:
                ts = pd.to_datetime(post.get('posted_at'))
                timestamps.append(ts)
            except:
                continue
        
        if len(timestamps) < 2:
            return 0.0
        
        timestamps.sort()
        time_span = (timestamps[-1] - timestamps[0]).total_seconds() / (24 * 3600)
        
        if time_span == 0:
            return 1.0  # All posts at same time
        
        posts_per_day = len(timestamps) / time_span
        
        # Score based on posting frequency
        if posts_per_day > 50:  # Extremely high frequency
            return 1.0
        elif posts_per_day > 20:  # Very high frequency
            return 0.8
        elif posts_per_day > 10:  # High frequency
            return 0.6
        elif posts_per_day < 0.1:  # Very low frequency
            return 0.3
        else:
            return 0.0  # Normal frequency
    
    def _analyze_temporal_patterns(self, posts: List[Dict]) -> float:
        """Analyze temporal posting patterns for automation"""
        if len(posts) < 5:
            return 0.0
        
        timestamps = []
        for post in posts:
            try:
                ts = pd.to_datetime(post.get('posted_at'))
                timestamps.append(ts)
            except:
                continue
        
        if len(timestamps) < 5:
            return 0.0
        
        timestamps.sort()
        
        # Calculate intervals between posts
        intervals = []
        for i in range(1, len(timestamps)):
            interval = (timestamps[i] - timestamps[i-1]).total_seconds()
            intervals.append(interval)
        
        # Analyze patterns
        bot_score = 0.0
        
        # Pattern 1: Very regular intervals
        if len(intervals) > 0:
            interval_std = np.std(intervals)
            interval_mean = np.mean(intervals)
            
            if interval_mean > 0:
                cv = interval_std / interval_mean  # Coefficient of variation
                if cv < 0.1:  # Very regular
                    bot_score += 0.5
        
        # Pattern 2: Posts at exact hour intervals
        hour_posts = [ts.minute for ts in timestamps]
        if len(set(hour_posts)) == 1:  # All at same minute
            bot_score += 0.4
        
        # Pattern 3: No posts during night hours (bots often pause)
        hours = [ts.hour for ts in timestamps]
        night_hours = [h for h in hours if 0 <= h <= 6]
        if len(night_hours) == 0 and len(hours) > 10:
            bot_score += 0.3
        
        return min(1.0, bot_score)
    
    def _analyze_content_diversity(self, posts: List[Dict]) -> float:
        """Analyze content diversity (low diversity suggests automation)"""
        if not posts:
            return 0.0
        
        # Extract text content
        texts = [post.get('text_content', '') for post in posts]
        texts = [t for t in texts if t.strip()]
        
        if len(texts) < 2:
            return 0.0
        
        bot_score = 0.0
        
        # Pattern 1: Identical or near-identical posts
        unique_texts = set(texts)
        diversity_ratio = len(unique_texts) / len(texts)
        if diversity_ratio < 0.5:
            bot_score += 0.4
        
        # Pattern 2: Repetitive patterns in text
        all_text = ' '.join(texts).lower()
        words = all_text.split()
        if len(words) > 0:
            unique_words = set(words)
            word_diversity = len(unique_words) / len(words)
            if word_diversity < 0.3:
                bot_score += 0.3
        
        # Pattern 3: Excessive hashtag usage
        hashtag_counts = []
        for post in posts:
            hashtag_counts.append(len(post.get('hashtags', [])))
        
        if hashtag_counts:
            avg_hashtags = np.mean(hashtag_counts)
            if avg_hashtags > 5:  # Excessive hashtag use
                bot_score += 0.3
        
        return min(1.0, bot_score)
    
    def _analyze_engagement_patterns(self, posts: List[Dict]) -> float:
        """Analyze engagement patterns for bot-like behavior"""
        if not posts:
            return 0.0
        
        engagement_ratios = []
        for post in posts:
            likes = post.get('likes_count', 0)
            retweets = post.get('retweets_count', 0)
            replies = post.get('replies_count', 0)
            
            total_engagement = likes + retweets + replies
            
            # Calculate engagement ratios
            if total_engagement > 0:
                like_ratio = likes / total_engagement
                engagement_ratios.append({
                    'like_ratio': like_ratio,
                    'total_engagement': total_engagement
                })
        
        if not engagement_ratios:
            return 0.0
        
        bot_score = 0.0
        
        # Pattern 1: Very low engagement
        avg_engagement = np.mean([er['total_engagement'] for er in engagement_ratios])
        if avg_engagement < 1:
            bot_score += 0.4
        
        # Pattern 2: Unusual engagement ratios
        like_ratios = [er['like_ratio'] for er in engagement_ratios]
        if like_ratios:
            avg_like_ratio = np.mean(like_ratios)
            if avg_like_ratio > 0.9:  # Suspiciously high like ratio
                bot_score += 0.3
        
        return min(1.0, bot_score)
    
    def _analyze_network_behavior(self, author: Dict, posts: List[Dict]) -> float:
        """Analyze network behavior patterns"""
        bot_score = 0.0
        
        # Pattern 1: Extreme follower/following ratios
        followers = author.get('followers_count', 0)
        following = author.get('following_count', 0)
        
        if following > 0:
            ratio = followers / following
            if ratio > 100:  # Too many followers
                bot_score += 0.3
            elif ratio < 0.01:  # Too few followers
                bot_score += 0.4
        
        # Pattern 2: Following many, followed by few
        if following > 2000 and followers < 100:
            bot_score += 0.4
        
        # Pattern 3: Excessive mention usage
        if posts:
            mention_counts = [len(post.get('mentions', [])) for post in posts]
            avg_mentions = np.mean(mention_counts) if mention_counts else 0
            if avg_mentions > 3:
                bot_score += 0.3
        
        return min(1.0, bot_score)
    
    def _generate_bot_indicators(self, scores: Dict, features: Dict) -> List[str]:
        """Generate specific bot indicators"""
        indicators = []
        
        if scores['username_pattern'] > 0.5:
            indicators.append('suspicious_username_pattern')
        
        if scores['profile_completeness'] > 0.7:
            indicators.append('incomplete_profile')
        
        if scores['posting_frequency'] > 0.6:
            indicators.append('unusual_posting_frequency')
        
        if scores['temporal_patterns'] > 0.5:
            indicators.append('automated_timing_patterns')
        
        if scores['content_diversity'] > 0.5:
            indicators.append('low_content_diversity')
        
        if scores['engagement_patterns'] > 0.5:
            indicators.append('unusual_engagement_patterns')
        
        if scores['network_behavior'] > 0.5:
            indicators.append('suspicious_network_behavior')
        
        return indicators
    
    def _calculate_account_age(self, created_at) -> float:
        """Calculate account age in days"""
        if not created_at:
            return 0
        
        try:
            created_date = pd.to_datetime(created_at)
            now = pd.to_datetime(datetime.now())
            return (now - created_date).days
        except:
            return 0
    
    def _safe_ratio(self, numerator: float, denominator: float) -> float:
        """Calculate safe ratio avoiding division by zero"""
        if denominator == 0:
            return 0.0
        return numerator / denominator
    
    def _empty_bot_result(self) -> Dict[str, Any]:
        """Return empty result for invalid input"""
        return {
            'bot_likelihood_score': 0.0,
            'classification': 'unknown',
            'risk_level': 'low',
            'component_scores': {},
            'features': {},
            'indicators': []
        }
    
    def analyze_bot_network(self, authors: List[Dict], posts: List[Dict]) -> Dict[str, Any]:
        """Analyze for coordinated bot networks"""
        if len(authors) < 3:
            return {'network_detected': False, 'bot_accounts': [], 'network_score': 0.0}
        
        # Calculate bot likelihood for all authors
        bot_results = []
        for author in authors:
            author_posts = [p for p in posts if p.get('author', {}).get('platform_user_id') == 
                          author.get('platform_user_id')]
            result = self.calculate_bot_likelihood(author, author_posts)
            result['author'] = author
            bot_results.append(result)
        
        # Identify potential bots
        potential_bots = [r for r in bot_results if r['bot_likelihood_score'] > 0.5]
        
        # Analyze network characteristics
        network_score = 0.0
        if len(potential_bots) >= 3:
            # Similar creation times
            creation_times = []
            for bot in potential_bots:
                created_at = bot['author'].get('account_created_at')
                if created_at:
                    try:
                        creation_times.append(pd.to_datetime(created_at))
                    except:
                        continue
            
            if len(creation_times) >= 3:
                creation_times.sort()
                time_span = (creation_times[-1] - creation_times[0]).days
                if time_span < 30:  # Created within 30 days
                    network_score += 0.4
            
            # Similar behavioral patterns
            similar_behavior_pairs = 0
            total_pairs = len(potential_bots) * (len(potential_bots) - 1) / 2
            
            for i in range(len(potential_bots)):
                for j in range(i + 1, len(potential_bots)):
                    similarity = self._calculate_bot_similarity(
                        potential_bots[i], potential_bots[j]
                    )
                    if similarity > 0.7:
                        similar_behavior_pairs += 1
            
            if total_pairs > 0:
                behavior_similarity_ratio = similar_behavior_pairs / total_pairs
                network_score += behavior_similarity_ratio * 0.6
        
        return {
            'network_detected': network_score > 0.6,
            'bot_accounts': potential_bots,
            'network_score': min(1.0, network_score),
            'total_analyzed': len(authors),
            'potential_bots_count': len(potential_bots)
        }
    
    def _calculate_bot_similarity(self, bot1: Dict, bot2: Dict) -> float:
        """Calculate similarity between two potential bot accounts"""
        features1 = bot1['features']
        features2 = bot2['features']
        
        # Compare numerical features
        numerical_features = ['followers_count', 'following_count', 'account_age_days']
        similarities = []
        
        for feature in numerical_features:
            val1 = features1.get(feature, 0)
            val2 = features2.get(feature, 0)
            
            # Normalize and compare
            max_val = max(val1, val2, 1)
            similarity = 1 - abs(val1 - val2) / max_val
            similarities.append(similarity)
        
        return np.mean(similarities)

def create_bot_detector() -> BotDetector:
    """Factory function to create a bot detector instance"""
    return BotDetector()

# Example usage
if __name__ == "__main__":
    detector = BotDetector()
    
    # Sample bot-like account
    bot_account = {
        'username': 'user123abc',
        'followers_count': 50,
        'following_count': 2000,
        'verified': False,
        'bio': '',
        'account_created_at': '2023-12-01T00:00:00Z'
    }
    
    # Sample legitimate account
    human_account = {
        'username': 'john_doe_journalist',
        'followers_count': 5000,
        'following_count': 800,
        'verified': True,
        'bio': 'Journalist covering tech and politics. Views my own.',
        'account_created_at': '2018-03-15T00:00:00Z'
    }
    
    bot_result = detector.calculate_bot_likelihood(bot_account)
    human_result = detector.calculate_bot_likelihood(human_account)
    
    print("Bot Account Analysis:")
    print(f"Bot Likelihood: {bot_result['bot_likelihood_score']:.2f}")
    print(f"Classification: {bot_result['classification']}")
    print(f"Indicators: {bot_result['indicators']}")
    
    print("\nHuman Account Analysis:")
    print(f"Bot Likelihood: {human_result['bot_likelihood_score']:.2f}")
    print(f"Classification: {human_result['classification']}")
    print(f"Indicators: {human_result['indicators']}")