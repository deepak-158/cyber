"""
Coordination Detection Module
Detects coordinated inauthentic behavior (CIB) using graph analysis,
text similarity, timing patterns, and behavioral analysis
"""

import logging
import numpy as np
import pandas as pd
import networkx as nx
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime, timedelta
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict, Counter
import itertools
import math

logger = logging.getLogger(__name__)

class CoordinationDetector:
    """Detects coordinated inauthentic behavior across social media accounts"""
    
    def __init__(self):
        # Similarity thresholds
        self.text_similarity_threshold = 0.8
        self.timing_threshold_minutes = 30
        self.behavioral_similarity_threshold = 0.7
        
        # Coordination scoring weights
        self.weights = {
            'text_similarity': 0.3,
            'timing_coordination': 0.25,
            'behavioral_patterns': 0.2,
            'network_structure': 0.15,
            'amplification_patterns': 0.1
        }
        
        # Minimum thresholds for coordination
        self.min_accounts_for_coordination = 3
        self.min_coordination_score = 0.6
    
    def detect_coordination(self, posts: List[Dict[str, Any]], 
                          authors: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Detect coordinated behavior patterns
        
        Args:
            posts: List of post dictionaries
            authors: List of author dictionaries (optional, extracted from posts if not provided)
            
        Returns:
            Dict containing coordination analysis results
        """
        if not posts or len(posts) < self.min_accounts_for_coordination:
            return self._empty_coordination_result()
        
        logger.info(f"Analyzing {len(posts)} posts for coordination patterns")
        
        # Extract authors if not provided
        if authors is None:
            authors = self._extract_authors_from_posts(posts)
        
        # Build interaction network
        network = self._build_interaction_network(posts, authors)
        
        # Detect text similarity coordination
        text_coordination = self._detect_text_similarity_coordination(posts)
        
        # Detect timing coordination
        timing_coordination = self._detect_timing_coordination(posts)
        
        # Detect behavioral coordination
        behavioral_coordination = self._detect_behavioral_coordination(authors, posts)
        
        # Analyze network structure
        network_analysis = self._analyze_network_structure(network)
        
        # Detect amplification patterns
        amplification_patterns = self._detect_amplification_patterns(posts)
        
        # Calculate overall coordination score
        coordination_score = self._calculate_coordination_score({
            'text_similarity': text_coordination,
            'timing_coordination': timing_coordination,
            'behavioral_patterns': behavioral_coordination,
            'network_structure': network_analysis,
            'amplification_patterns': amplification_patterns
        })
        
        # Identify coordinated groups
        coordinated_groups = self._identify_coordinated_groups(
            text_coordination, timing_coordination, behavioral_coordination
        )
        
        return {
            'total_posts': len(posts),
            'total_authors': len(authors),
            'coordination_score': coordination_score,
            'suspected_coordination': coordination_score > self.min_coordination_score,
            'text_coordination': text_coordination,
            'timing_coordination': timing_coordination,
            'behavioral_coordination': behavioral_coordination,
            'network_analysis': network_analysis,
            'amplification_patterns': amplification_patterns,
            'coordinated_groups': coordinated_groups,
            'risk_indicators': self._generate_risk_indicators(coordination_score, coordinated_groups)
        }
    
    def _extract_authors_from_posts(self, posts: List[Dict]) -> List[Dict]:
        """Extract unique authors from posts"""
        authors_dict = {}
        
        for post in posts:
            author = post.get('author', {})
            if isinstance(author, dict):
                user_id = author.get('platform_user_id') or author.get('username')
                if user_id and user_id not in authors_dict:
                    authors_dict[user_id] = author
        
        return list(authors_dict.values())
    
    def _build_interaction_network(self, posts: List[Dict], authors: List[Dict]) -> nx.Graph:
        """Build social interaction network from posts and authors"""
        G = nx.Graph()
        
        # Add author nodes
        for author in authors:
            user_id = author.get('platform_user_id') or author.get('username')
            if user_id:
                G.add_node(user_id, **author)
        
        # Add edges based on interactions
        for post in posts:
            author_id = post.get('author', {}).get('platform_user_id') or post.get('author', {}).get('username')
            
            # Mentions create edges
            mentions = post.get('mentions', [])
            for mention in mentions:
                if mention in G.nodes and author_id in G.nodes and mention != author_id:
                    if G.has_edge(author_id, mention):
                        G[author_id][mention]['weight'] += 1
                    else:
                        G.add_edge(author_id, mention, weight=1, interaction_type='mention')
            
            # Replies create edges (if parent post author is known)
            if post.get('is_reply') and post.get('parent_post_id'):
                # This would need parent post author lookup in a real implementation
                pass
        
        return G
    
    def _detect_text_similarity_coordination(self, posts: List[Dict]) -> Dict[str, Any]:
        """Detect coordination based on text similarity"""
        text_coordination = {
            'similar_content_groups': [],
            'similarity_scores': [],
            'copy_paste_evidence': [],
            'coordination_strength': 0.0
        }
        
        if len(posts) < 2:
            return text_coordination
        
        # Extract text content
        texts = []
        post_metadata = []
        
        for i, post in enumerate(posts):
            text = post.get('text_content', '').strip()
            if text:
                texts.append(text)
                post_metadata.append({
                    'index': i,
                    'post_id': post.get('platform_post_id'),
                    'author': post.get('author', {}).get('username', 'unknown'),
                    'timestamp': post.get('posted_at')
                })
        
        if len(texts) < 2:
            return text_coordination
        
        # Calculate text similarity matrix
        try:
            vectorizer = TfidfVectorizer(
                ngram_range=(1, 3),
                max_features=1000,
                stop_words='english'
            )
            
            tfidf_matrix = vectorizer.fit_transform(texts)
            similarity_matrix = cosine_similarity(tfidf_matrix)
            
            # Find highly similar pairs
            similar_pairs = []
            for i in range(len(texts)):
                for j in range(i + 1, len(texts)):
                    similarity = similarity_matrix[i][j]
                    if similarity > self.text_similarity_threshold:
                        similar_pairs.append({
                            'post1': post_metadata[i],
                            'post2': post_metadata[j],
                            'similarity': similarity,
                            'text1': texts[i][:100] + '...' if len(texts[i]) > 100 else texts[i],
                            'text2': texts[j][:100] + '...' if len(texts[j]) > 100 else texts[j]
                        })
            
            # Group similar content
            similar_groups = self._group_similar_content(similar_pairs)
            
            # Calculate coordination strength
            coordination_strength = len(similar_pairs) / max(1, len(texts) * (len(texts) - 1) / 2)
            
            text_coordination.update({
                'similar_content_groups': similar_groups,
                'similarity_scores': [pair['similarity'] for pair in similar_pairs],
                'copy_paste_evidence': similar_pairs,
                'coordination_strength': coordination_strength
            })
            
        except Exception as e:
            logger.error(f"Error in text similarity analysis: {str(e)}")
        
        return text_coordination
    
    def _group_similar_content(self, similar_pairs: List[Dict]) -> List[Dict]:
        """Group posts with similar content"""
        groups = []
        processed_posts = set()
        
        for pair in similar_pairs:
            post1_id = pair['post1']['post_id']
            post2_id = pair['post2']['post_id']
            
            # Check if posts are already in a group
            found_group = None
            for group in groups:
                if post1_id in [p['post_id'] for p in group['posts']] or \
                   post2_id in [p['post_id'] for p in group['posts']]:
                    found_group = group
                    break
            
            if found_group:
                # Add to existing group
                if post1_id not in [p['post_id'] for p in found_group['posts']]:
                    found_group['posts'].append(pair['post1'])
                if post2_id not in [p['post_id'] for p in found_group['posts']]:
                    found_group['posts'].append(pair['post2'])
                found_group['avg_similarity'] = np.mean([
                    p['similarity'] for p in similar_pairs 
                    if p['post1']['post_id'] in [post['post_id'] for post in found_group['posts']] and
                       p['post2']['post_id'] in [post['post_id'] for post in found_group['posts']]
                ])
            else:
                # Create new group
                groups.append({
                    'posts': [pair['post1'], pair['post2']],
                    'avg_similarity': pair['similarity'],
                    'size': 2
                })
        
        # Update group sizes
        for group in groups:
            group['size'] = len(group['posts'])
        
        return sorted(groups, key=lambda x: x['size'], reverse=True)
    
    def _detect_timing_coordination(self, posts: List[Dict]) -> Dict[str, Any]:
        """Detect coordination based on posting timing patterns"""
        timing_coordination = {
            'synchronized_bursts': [],
            'timing_clusters': [],
            'coordination_strength': 0.0,
            'temporal_patterns': {}
        }
        
        if len(posts) < 2:
            return timing_coordination
        
        # Parse timestamps
        timestamped_posts = []
        for post in posts:
            try:
                timestamp = pd.to_datetime(post.get('posted_at'))
                timestamped_posts.append({
                    'timestamp': timestamp,
                    'post_id': post.get('platform_post_id'),
                    'author': post.get('author', {}).get('username', 'unknown'),
                    'platform': post.get('platform')
                })
            except:
                continue
        
        if len(timestamped_posts) < 2:
            return timing_coordination
        
        # Sort by timestamp
        timestamped_posts.sort(key=lambda x: x['timestamp'])
        
        # Find synchronized clusters
        timing_clusters = []
        current_cluster = [timestamped_posts[0]]
        
        for i in range(1, len(timestamped_posts)):
            time_diff = (timestamped_posts[i]['timestamp'] - 
                        current_cluster[-1]['timestamp']).total_seconds() / 60
            
            if time_diff <= self.timing_threshold_minutes:
                current_cluster.append(timestamped_posts[i])
            else:
                if len(current_cluster) >= self.min_accounts_for_coordination:
                    timing_clusters.append({
                        'posts': current_cluster,
                        'start_time': current_cluster[0]['timestamp'],
                        'end_time': current_cluster[-1]['timestamp'],
                        'duration_minutes': (current_cluster[-1]['timestamp'] - 
                                           current_cluster[0]['timestamp']).total_seconds() / 60,
                        'size': len(current_cluster),
                        'unique_authors': len(set(p['author'] for p in current_cluster))
                    })
                current_cluster = [timestamped_posts[i]]
        
        # Check last cluster
        if len(current_cluster) >= self.min_accounts_for_coordination:
            timing_clusters.append({
                'posts': current_cluster,
                'start_time': current_cluster[0]['timestamp'],
                'end_time': current_cluster[-1]['timestamp'],
                'duration_minutes': (current_cluster[-1]['timestamp'] - 
                                   current_cluster[0]['timestamp']).total_seconds() / 60,
                'size': len(current_cluster),
                'unique_authors': len(set(p['author'] for p in current_cluster))
            })
        
        # Calculate coordination strength
        coordinated_posts = sum(cluster['size'] for cluster in timing_clusters)
        coordination_strength = coordinated_posts / len(timestamped_posts)
        
        # Analyze temporal patterns
        temporal_patterns = self._analyze_temporal_patterns(timestamped_posts)
        
        timing_coordination.update({
            'timing_clusters': timing_clusters,
            'coordination_strength': coordination_strength,
            'temporal_patterns': temporal_patterns
        })
        
        return timing_coordination
    
    def _analyze_temporal_patterns(self, timestamped_posts: List[Dict]) -> Dict[str, Any]:
        """Analyze temporal posting patterns"""
        if not timestamped_posts:
            return {}
        
        timestamps = [post['timestamp'] for post in timestamped_posts]
        
        # Hour of day distribution
        hours = [ts.hour for ts in timestamps]
        hour_dist = dict(Counter(hours))
        
        # Day of week distribution
        days = [ts.weekday() for ts in timestamps]
        day_dist = dict(Counter(days))
        
        # Calculate posting intervals
        intervals = []
        for i in range(1, len(timestamps)):
            interval = (timestamps[i] - timestamps[i-1]).total_seconds() / 60
            intervals.append(interval)
        
        return {
            'hour_distribution': hour_dist,
            'day_distribution': day_dist,
            'avg_interval_minutes': np.mean(intervals) if intervals else 0,
            'std_interval_minutes': np.std(intervals) if intervals else 0,
            'min_interval_minutes': np.min(intervals) if intervals else 0
        }
    
    def _detect_behavioral_coordination(self, authors: List[Dict], posts: List[Dict]) -> Dict[str, Any]:
        """Detect coordination based on behavioral patterns"""
        behavioral_coordination = {
            'similar_profiles': [],
            'coordinated_behaviors': [],
            'coordination_strength': 0.0
        }
        
        if len(authors) < 2:
            return behavioral_coordination
        
        # Extract behavioral features for each author
        author_features = {}
        for author in authors:
            user_id = author.get('platform_user_id') or author.get('username')
            if user_id:
                author_features[user_id] = self._extract_behavioral_features(author, posts)
        
        # Find similar behavioral patterns
        similar_pairs = []
        author_ids = list(author_features.keys())
        
        for i in range(len(author_ids)):
            for j in range(i + 1, len(author_ids)):
                similarity = self._calculate_behavioral_similarity(
                    author_features[author_ids[i]], 
                    author_features[author_ids[j]]
                )
                
                if similarity > self.behavioral_similarity_threshold:
                    similar_pairs.append({
                        'author1': author_ids[i],
                        'author2': author_ids[j],
                        'similarity': similarity,
                        'features1': author_features[author_ids[i]],
                        'features2': author_features[author_ids[j]]
                    })
        
        # Calculate coordination strength
        max_possible_pairs = len(author_ids) * (len(author_ids) - 1) / 2
        coordination_strength = len(similar_pairs) / max(1, max_possible_pairs)
        
        behavioral_coordination.update({
            'similar_profiles': similar_pairs,
            'coordination_strength': coordination_strength
        })
        
        return behavioral_coordination
    
    def _extract_behavioral_features(self, author: Dict, posts: List[Dict]) -> Dict[str, Any]:
        """Extract behavioral features for an author"""
        user_id = author.get('platform_user_id') or author.get('username')
        
        # Get posts by this author
        author_posts = [p for p in posts if p.get('author', {}).get('platform_user_id') == user_id or 
                       p.get('author', {}).get('username') == user_id]
        
        features = {
            # Profile features
            'followers_count': author.get('followers_count', 0),
            'following_count': author.get('following_count', 0),
            'posts_count': author.get('posts_count', 0),
            'verified': author.get('verified', False),
            'account_age_days': self._calculate_account_age(author.get('account_created_at')),
            
            # Posting behavior
            'posts_in_dataset': len(author_posts),
            'avg_post_length': np.mean([len(p.get('text_content', '')) for p in author_posts]) if author_posts else 0,
            'hashtag_usage_rate': np.mean([len(p.get('hashtags', [])) for p in author_posts]) if author_posts else 0,
            'mention_usage_rate': np.mean([len(p.get('mentions', [])) for p in author_posts]) if author_posts else 0,
            'url_sharing_rate': np.mean([len(p.get('urls', [])) for p in author_posts]) if author_posts else 0,
            
            # Engagement patterns
            'avg_likes': np.mean([p.get('likes_count', 0) for p in author_posts]) if author_posts else 0,
            'avg_retweets': np.mean([p.get('retweets_count', 0) for p in author_posts]) if author_posts else 0,
            'avg_replies': np.mean([p.get('replies_count', 0) for p in author_posts]) if author_posts else 0
        }
        
        return features
    
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
    
    def _calculate_behavioral_similarity(self, features1: Dict, features2: Dict) -> float:
        """Calculate behavioral similarity between two authors"""
        # Normalize features and calculate cosine similarity
        feature_keys = [
            'followers_count', 'following_count', 'account_age_days',
            'avg_post_length', 'hashtag_usage_rate', 'mention_usage_rate',
            'avg_likes', 'avg_retweets'
        ]
        
        vector1 = []
        vector2 = []
        
        for key in feature_keys:
            val1 = features1.get(key, 0)
            val2 = features2.get(key, 0)
            
            # Normalize large values
            if key in ['followers_count', 'following_count', 'avg_likes', 'avg_retweets']:
                val1 = math.log(val1 + 1)
                val2 = math.log(val2 + 1)
            
            vector1.append(val1)
            vector2.append(val2)
        
        # Calculate cosine similarity
        try:
            dot_product = np.dot(vector1, vector2)
            norm1 = np.linalg.norm(vector1)
            norm2 = np.linalg.norm(vector2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return max(0.0, similarity)
            
        except:
            return 0.0
    
    def _analyze_network_structure(self, network: nx.Graph) -> Dict[str, Any]:
        """Analyze network structure for coordination patterns"""
        analysis = {
            'node_count': network.number_of_nodes(),
            'edge_count': network.number_of_edges(),
            'density': 0.0,
            'clustering_coefficient': 0.0,
            'connected_components': 0,
            'suspicious_patterns': []
        }
        
        if network.number_of_nodes() < 2:
            return analysis
        
        try:
            # Basic network metrics
            analysis['density'] = nx.density(network)
            analysis['clustering_coefficient'] = nx.average_clustering(network)
            analysis['connected_components'] = nx.number_connected_components(network)
            
            # Detect suspicious patterns
            suspicious_patterns = []
            
            # High clustering with low density (potential bot networks)
            if analysis['clustering_coefficient'] > 0.7 and analysis['density'] < 0.3:
                suspicious_patterns.append('high_clustering_low_density')
            
            # Star-like structures (potential amplification networks)
            degrees = dict(network.degree())
            max_degree = max(degrees.values()) if degrees else 0
            avg_degree = np.mean(list(degrees.values())) if degrees else 0
            
            if max_degree > 3 * avg_degree and max_degree > 10:
                suspicious_patterns.append('star_network_structure')
            
            analysis['suspicious_patterns'] = suspicious_patterns
            
        except Exception as e:
            logger.error(f"Error in network analysis: {str(e)}")
        
        return analysis
    
    def _detect_amplification_patterns(self, posts: List[Dict]) -> Dict[str, Any]:
        """Detect artificial amplification patterns"""
        amplification = {
            'rapid_amplification_events': [],
            'coordinated_amplification': [],
            'amplification_strength': 0.0
        }
        
        # Group posts by content similarity and analyze amplification timing
        # This is a simplified version - full implementation would be more complex
        hashtag_groups = defaultdict(list)
        
        for post in posts:
            hashtags = post.get('hashtags', [])
            for hashtag in hashtags:
                hashtag_groups[hashtag].append(post)
        
        # Analyze amplification for each hashtag
        rapid_events = []
        for hashtag, hashtag_posts in hashtag_groups.items():
            if len(hashtag_posts) >= 5:  # Minimum threshold
                # Check if posts are clustered in time
                timestamps = []
                for post in hashtag_posts:
                    try:
                        ts = pd.to_datetime(post.get('posted_at'))
                        timestamps.append(ts)
                    except:
                        continue
                
                if len(timestamps) >= 5:
                    timestamps.sort()
                    time_span = (timestamps[-1] - timestamps[0]).total_seconds() / 3600
                    
                    if time_span < 2:  # All posts within 2 hours
                        rapid_events.append({
                            'hashtag': hashtag,
                            'post_count': len(hashtag_posts),
                            'time_span_hours': time_span,
                            'amplification_rate': len(hashtag_posts) / max(1, time_span)
                        })
        
        amplification['rapid_amplification_events'] = rapid_events
        amplification['amplification_strength'] = len(rapid_events) / max(1, len(hashtag_groups))
        
        return amplification
    
    def _calculate_coordination_score(self, components: Dict[str, Dict]) -> float:
        """Calculate overall coordination score"""
        score = 0.0
        
        # Text similarity component
        text_strength = components['text_similarity'].get('coordination_strength', 0)
        score += text_strength * self.weights['text_similarity']
        
        # Timing coordination component
        timing_strength = components['timing_coordination'].get('coordination_strength', 0)
        score += timing_strength * self.weights['timing_coordination']
        
        # Behavioral patterns component
        behavioral_strength = components['behavioral_patterns'].get('coordination_strength', 0)
        score += behavioral_strength * self.weights['behavioral_patterns']
        
        # Network structure component
        network_indicators = len(components['network_structure'].get('suspicious_patterns', []))
        network_strength = min(1.0, network_indicators / 3)  # Normalize
        score += network_strength * self.weights['network_structure']
        
        # Amplification patterns component
        amplification_strength = components['amplification_patterns'].get('amplification_strength', 0)
        score += amplification_strength * self.weights['amplification_patterns']
        
        return min(1.0, score)
    
    def _identify_coordinated_groups(self, text_coord: Dict, timing_coord: Dict, 
                                   behavioral_coord: Dict) -> List[Dict]:
        """Identify specific coordinated groups"""
        groups = []
        
        # Groups from text similarity
        for group in text_coord.get('similar_content_groups', []):
            if group['size'] >= self.min_accounts_for_coordination:
                groups.append({
                    'type': 'text_similarity',
                    'members': [post['author'] for post in group['posts']],
                    'size': group['size'],
                    'evidence': f"Similar content (avg similarity: {group['avg_similarity']:.2f})",
                    'risk_level': 'high' if group['avg_similarity'] > 0.9 else 'medium'
                })
        
        # Groups from timing coordination
        for cluster in timing_coord.get('timing_clusters', []):
            if cluster['size'] >= self.min_accounts_for_coordination:
                groups.append({
                    'type': 'timing_coordination',
                    'members': list(set(post['author'] for post in cluster['posts'])),
                    'size': cluster['size'],
                    'evidence': f"Synchronized posting within {cluster['duration_minutes']:.1f} minutes",
                    'risk_level': 'high' if cluster['duration_minutes'] < 5 else 'medium'
                })
        
        return groups
    
    def _generate_risk_indicators(self, coordination_score: float, 
                                groups: List[Dict]) -> List[str]:
        """Generate risk indicators based on analysis"""
        indicators = []
        
        if coordination_score > 0.8:
            indicators.append('extremely_high_coordination')
        elif coordination_score > 0.6:
            indicators.append('high_coordination')
        
        if any(group['risk_level'] == 'high' for group in groups):
            indicators.append('high_risk_coordinated_groups')
        
        text_similarity_groups = [g for g in groups if g['type'] == 'text_similarity']
        if text_similarity_groups:
            indicators.append('copy_paste_behavior')
        
        timing_groups = [g for g in groups if g['type'] == 'timing_coordination']
        if timing_groups:
            indicators.append('synchronized_posting')
        
        return indicators
    
    def _empty_coordination_result(self) -> Dict[str, Any]:
        """Return empty result when coordination analysis is not possible"""
        return {
            'total_posts': 0,
            'total_authors': 0,
            'coordination_score': 0.0,
            'suspected_coordination': False,
            'text_coordination': {'coordination_strength': 0.0},
            'timing_coordination': {'coordination_strength': 0.0},
            'behavioral_coordination': {'coordination_strength': 0.0},
            'network_analysis': {'suspicious_patterns': []},
            'amplification_patterns': {'amplification_strength': 0.0},
            'coordinated_groups': [],
            'risk_indicators': []
        }

def create_coordination_detector() -> CoordinationDetector:
    """Factory function to create a coordination detector instance"""
    return CoordinationDetector()

# Example usage
if __name__ == "__main__":
    detector = CoordinationDetector()
    
    # Sample coordinated posts for testing
    from datetime import datetime, timedelta
    
    base_time = datetime.now()
    sample_posts = [
        {
            'platform_post_id': 'post_1',
            'text_content': "India's economy is completely failing! Unemployment at record high! #IndiaFailing",
            'posted_at': base_time,
            'author': {'platform_user_id': 'user_1', 'username': 'account_1'},
            'hashtags': ['IndiaFailing'],
            'platform': 'twitter'
        },
        {
            'platform_post_id': 'post_2', 
            'text_content': "India's economy is completely failing! Unemployment at record high! #IndiaFailing",
            'posted_at': base_time + timedelta(minutes=5),
            'author': {'platform_user_id': 'user_2', 'username': 'account_2'},
            'hashtags': ['IndiaFailing'],
            'platform': 'twitter'
        },
        {
            'platform_post_id': 'post_3',
            'text_content': "Economic crisis in India worsening every day #IndiaFailing #Crisis",
            'posted_at': base_time + timedelta(minutes=10),
            'author': {'platform_user_id': 'user_3', 'username': 'account_3'},
            'hashtags': ['IndiaFailing', 'Crisis'],
            'platform': 'twitter'
        }
    ]
    
    result = detector.detect_coordination(sample_posts)
    
    print("Coordination Detection Results:")
    print(f"Coordination Score: {result['coordination_score']:.2f}")
    print(f"Suspected Coordination: {result['suspected_coordination']}")
    print(f"Text Coordination Strength: {result['text_coordination']['coordination_strength']:.2f}")
    print(f"Timing Coordination Strength: {result['timing_coordination']['coordination_strength']:.2f}")
    print(f"Coordinated Groups: {len(result['coordinated_groups'])}")
    print(f"Risk Indicators: {result['risk_indicators']}")
    
    for i, group in enumerate(result['coordinated_groups']):
        print(f"\nGroup {i+1} ({group['type']}):")
        print(f"  Members: {group['members']}")
        print(f"  Evidence: {group['evidence']}")
        print(f"  Risk Level: {group['risk_level']}")