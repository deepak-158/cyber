"""
Narrative Clustering Module
Groups posts into thematic narratives using sentence embeddings and HDBSCAN clustering
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from sentence_transformers import SentenceTransformer
import hdbscan
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import os
from collections import Counter
import re

logger = logging.getLogger(__name__)

class NarrativeClusterer:
    """Clusters posts into thematic narratives using semantic embeddings"""
    
    def __init__(self, model_cache_dir: str = "./models/checkpoints"):
        self.model_cache_dir = model_cache_dir
        self.embedding_model = None
        self.clusterer = None
        self.vectorizer = None
        
        # Clustering parameters
        self.min_cluster_size = 5
        self.min_samples = 3
        self.cluster_selection_epsilon = 0.3
        
        # Narrative categories for India-related content
        self.predefined_narratives = {
            'economic_doom': {
                'keywords': ['economy', 'unemployment', 'gdp', 'recession', 'crisis', 'collapse', 'fail'],
                'description': 'Narratives about economic failure and crisis'
            },
            'terrorism_accusations': {
                'keywords': ['terror', 'terrorist', 'attack', 'bomb', 'violence', 'threat'],
                'description': 'Accusations of terrorism or violent activities'
            },
            'kashmir_conflict': {
                'keywords': ['kashmir', 'occupation', 'human rights', 'violation', 'oppression'],
                'description': 'Content about Kashmir conflict and human rights'
            },
            'international_isolation': {
                'keywords': ['isolated', 'alone', 'enemy', 'sanctions', 'boycott', 'international'],
                'description': 'Narratives about international isolation'
            },
            'religious_division': {
                'keywords': ['hindu', 'muslim', 'religious', 'communal', 'riot', 'violence'],
                'description': 'Content promoting religious division'
            },
            'achievement_celebration': {
                'keywords': ['proud', 'achievement', 'success', 'space', 'technology', 'growth'],
                'description': 'Positive narratives about achievements'
            },
            'legitimate_criticism': {
                'keywords': ['policy', 'government', 'reform', 'improvement', 'analysis'],
                'description': 'Legitimate policy criticism and analysis'
            }
        }
        
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize embedding and clustering models"""
        try:
            logger.info("Loading sentence embedding model...")
            # Use multilingual sentence transformer
            self.embedding_model = SentenceTransformer(
                'paraphrase-multilingual-MiniLM-L12-v2'
            )
            
            # Initialize HDBSCAN clusterer
            self.clusterer = hdbscan.HDBSCAN(
                min_cluster_size=self.min_cluster_size,
                min_samples=self.min_samples,
                cluster_selection_epsilon=self.cluster_selection_epsilon,
                metric='euclidean'
            )
            
            # Initialize TF-IDF vectorizer for keyword extraction
            self.vectorizer = TfidfVectorizer(
                max_features=100,
                ngram_range=(1, 3),
                stop_words='english',
                lowercase=True
            )
            
            logger.info("Narrative clustering models initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing clustering models: {str(e)}")
            raise
    
    def cluster_narratives(self, posts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Cluster posts into narrative themes
        
        Args:
            posts: List of post dictionaries with text content
            
        Returns:
            Dict containing cluster assignments, keywords, and statistics
        """
        if not posts or len(posts) < self.min_cluster_size:
            return self._empty_clustering_result()
        
        # Extract text content
        texts = [post.get('text_content', '') for post in posts]
        texts = [text for text in texts if text.strip()]
        
        if len(texts) < self.min_cluster_size:
            return self._empty_clustering_result()
        
        logger.info(f"Clustering {len(texts)} posts into narrative themes")
        
        # Generate embeddings
        embeddings = self._generate_embeddings(texts)
        
        # Perform clustering
        cluster_labels = self._perform_clustering(embeddings)
        
        # Extract cluster characteristics
        clusters = self._extract_cluster_characteristics(texts, cluster_labels, posts)
        
        # Map to predefined narratives
        narrative_mapping = self._map_to_predefined_narratives(clusters)
        
        # Generate final result
        result = {
            'total_posts': len(posts),
            'clustered_posts': len(texts),
            'num_clusters': len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0),
            'noise_posts': list(cluster_labels).count(-1),
            'clusters': clusters,
            'narrative_mapping': narrative_mapping,
            'cluster_assignments': cluster_labels.tolist(),
            'embeddings': embeddings.tolist() if embeddings is not None else []
        }
        
        return result
    
    def _generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate sentence embeddings for texts"""
        try:
            # Clean texts
            cleaned_texts = [self._clean_text(text) for text in texts]
            
            # Generate embeddings
            embeddings = self.embedding_model.encode(
                cleaned_texts,
                convert_to_numpy=True,
                show_progress_bar=True
            )
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            return None
    
    def _perform_clustering(self, embeddings: np.ndarray) -> np.ndarray:
        """Perform HDBSCAN clustering on embeddings"""
        try:
            cluster_labels = self.clusterer.fit_predict(embeddings)
            
            num_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
            noise_points = list(cluster_labels).count(-1)
            
            logger.info(f"Clustering completed: {num_clusters} clusters, {noise_points} noise points")
            
            return cluster_labels
            
        except Exception as e:
            logger.error(f"Error in clustering: {str(e)}")
            return np.array([-1] * len(embeddings))
    
    def _extract_cluster_characteristics(self, texts: List[str], labels: np.ndarray, 
                                       posts: List[Dict]) -> Dict[int, Dict]:
        """Extract characteristics for each cluster"""
        clusters = {}
        
        unique_labels = set(labels)
        for label in unique_labels:
            if label == -1:  # Skip noise cluster
                continue
            
            # Get texts in this cluster
            cluster_indices = np.where(labels == label)[0]
            cluster_texts = [texts[i] for i in cluster_indices]
            cluster_posts = [posts[i] for i in cluster_indices if i < len(posts)]
            
            # Extract keywords using TF-IDF
            keywords = self._extract_cluster_keywords(cluster_texts)
            
            # Calculate cluster statistics
            stats = self._calculate_cluster_stats(cluster_posts)
            
            # Get representative texts
            representative_texts = self._get_representative_texts(cluster_texts, max_texts=3)
            
            clusters[int(label)] = {
                'size': len(cluster_texts),
                'keywords': keywords,
                'representative_texts': representative_texts,
                'statistics': stats,
                'post_indices': cluster_indices.tolist()
            }
        
        return clusters
    
    def _extract_cluster_keywords(self, texts: List[str]) -> List[str]:
        """Extract representative keywords for a cluster"""
        try:
            if len(texts) < 2:
                return []
            
            # Combine all texts in cluster
            combined_text = ' '.join(texts)
            
            # Use TF-IDF to find important terms
            tfidf_matrix = self.vectorizer.fit_transform([combined_text])
            feature_names = self.vectorizer.get_feature_names_out()
            tfidf_scores = tfidf_matrix.toarray()[0]
            
            # Get top keywords
            top_indices = np.argsort(tfidf_scores)[::-1][:10]
            keywords = [feature_names[i] for i in top_indices if tfidf_scores[i] > 0]
            
            return keywords
            
        except Exception as e:
            logger.warning(f"Error extracting keywords: {str(e)}")
            return []
    
    def _calculate_cluster_stats(self, posts: List[Dict]) -> Dict[str, Any]:
        """Calculate statistics for a cluster"""
        if not posts:
            return {}
        
        # Extract available metrics
        toxicity_scores = [p.get('toxicity_score', 0) for p in posts if 'toxicity_score' in p]
        stance_scores = [p.get('stance_score', 0) for p in posts if 'stance_score' in p]
        engagement_counts = [
            p.get('likes_count', 0) + p.get('retweets_count', 0) + p.get('replies_count', 0)
            for p in posts
        ]
        
        # Language distribution
        languages = [p.get('language', 'unknown') for p in posts]
        language_dist = dict(Counter(languages))
        
        # Platform distribution
        platforms = [p.get('platform', 'unknown') for p in posts]
        platform_dist = dict(Counter(platforms))
        
        stats = {
            'avg_toxicity': np.mean(toxicity_scores) if toxicity_scores else 0,
            'avg_stance': np.mean(stance_scores) if stance_scores else 0,
            'avg_engagement': np.mean(engagement_counts) if engagement_counts else 0,
            'language_distribution': language_dist,
            'platform_distribution': platform_dist,
            'time_span': self._calculate_time_span(posts)
        }
        
        return stats
    
    def _calculate_time_span(self, posts: List[Dict]) -> Dict[str, Any]:
        """Calculate time span for cluster posts"""
        try:
            from datetime import datetime
            
            timestamps = []
            for post in posts:
                if 'posted_at' in post:
                    if isinstance(post['posted_at'], str):
                        # Parse ISO format timestamp
                        timestamp = datetime.fromisoformat(post['posted_at'].replace('Z', '+00:00'))
                        timestamps.append(timestamp)
                    elif isinstance(post['posted_at'], datetime):
                        timestamps.append(post['posted_at'])
            
            if not timestamps:
                return {}
            
            timestamps.sort()
            return {
                'start_time': timestamps[0].isoformat(),
                'end_time': timestamps[-1].isoformat(),
                'duration_hours': (timestamps[-1] - timestamps[0]).total_seconds() / 3600
            }
            
        except Exception as e:
            logger.warning(f"Error calculating time span: {str(e)}")
            return {}
    
    def _get_representative_texts(self, texts: List[str], max_texts: int = 3) -> List[str]:
        """Get most representative texts from cluster"""
        if len(texts) <= max_texts:
            return texts
        
        # For now, return first few texts (could be improved with centroid calculation)
        return texts[:max_texts]
    
    def _map_to_predefined_narratives(self, clusters: Dict[int, Dict]) -> Dict[int, str]:
        """Map clusters to predefined narrative categories"""
        mapping = {}
        
        for cluster_id, cluster_data in clusters.items():
            keywords = cluster_data.get('keywords', [])
            
            best_match = 'other'
            best_score = 0
            
            # Check similarity to predefined narratives
            for narrative_name, narrative_info in self.predefined_narratives.items():
                narrative_keywords = narrative_info['keywords']
                
                # Calculate keyword overlap score
                overlap = len(set(keywords) & set(narrative_keywords))
                if overlap > best_score:
                    best_score = overlap
                    best_match = narrative_name
            
            mapping[cluster_id] = best_match
        
        return mapping
    
    def _clean_text(self, text: str) -> str:
        """Clean text for embedding generation"""
        # Remove URLs
        text = re.sub(r'http[s]?://\S+', '', text)
        
        # Remove excessive punctuation
        text = re.sub(r'[!?.]{3,}', '...', text)
        
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def _empty_clustering_result(self) -> Dict[str, Any]:
        """Return empty result when clustering is not possible"""
        return {
            'total_posts': 0,
            'clustered_posts': 0,
            'num_clusters': 0,
            'noise_posts': 0,
            'clusters': {},
            'narrative_mapping': {},
            'cluster_assignments': [],
            'embeddings': []
        }
    
    def find_similar_narratives(self, new_posts: List[Dict], existing_clusters: Dict) -> Dict[str, Any]:
        """Find which existing narratives new posts belong to"""
        if not new_posts or not existing_clusters:
            return {'assignments': [], 'similarities': []}
        
        # Generate embeddings for new posts
        new_texts = [post.get('text_content', '') for post in new_posts]
        new_embeddings = self._generate_embeddings(new_texts)
        
        if new_embeddings is None:
            return {'assignments': [], 'similarities': []}
        
        assignments = []
        similarities = []
        
        # For each new post, find most similar existing cluster
        for i, embedding in enumerate(new_embeddings):
            best_cluster = -1
            best_similarity = 0
            
            for cluster_id, cluster_data in existing_clusters.items():
                if 'centroid' in cluster_data:
                    similarity = cosine_similarity(
                        [embedding], [cluster_data['centroid']]
                    )[0][0]
                    
                    if similarity > best_similarity:
                        best_similarity = similarity
                        best_cluster = cluster_id
            
            assignments.append(best_cluster)
            similarities.append(best_similarity)
        
        return {
            'assignments': assignments,
            'similarities': similarities
        }
    
    def update_cluster_model(self, all_posts: List[Dict]) -> Dict[str, Any]:
        """Update clustering model with new data"""
        logger.info("Updating narrative clustering model with new data")
        
        # Re-cluster all posts
        result = self.cluster_narratives(all_posts)
        
        # Save updated model (implement persistence if needed)
        logger.info("Clustering model updated successfully")
        
        return result
    
    def get_narrative_evolution(self, posts_by_time: List[List[Dict]]) -> Dict[str, Any]:
        """Analyze how narratives evolve over time"""
        evolution = {
            'time_periods': len(posts_by_time),
            'narrative_trends': {},
            'emerging_narratives': [],
            'declining_narratives': []
        }
        
        period_clusters = []
        
        # Cluster each time period
        for period_posts in posts_by_time:
            if period_posts:
                clusters = self.cluster_narratives(period_posts)
                period_clusters.append(clusters)
            else:
                period_clusters.append(self._empty_clustering_result())
        
        # Analyze trends
        narrative_counts = {}
        for clusters in period_clusters:
            for cluster_id, narrative in clusters.get('narrative_mapping', {}).items():
                if narrative not in narrative_counts:
                    narrative_counts[narrative] = []
                narrative_counts[narrative].append(clusters['clusters'][cluster_id]['size'])
        
        evolution['narrative_trends'] = narrative_counts
        
        return evolution

def create_narrative_clusterer(model_cache_dir: str = "./models/checkpoints") -> NarrativeClusterer:
    """Factory function to create a narrative clusterer instance"""
    return NarrativeClusterer(model_cache_dir)

# Example usage
if __name__ == "__main__":
    clusterer = NarrativeClusterer()
    
    # Sample posts for testing
    sample_posts = [
        {
            'text_content': "India's economy is collapsing! Unemployment at all time high!",
            'toxicity_score': 0.7,
            'stance_score': -0.8,
            'platform': 'twitter',
            'language': 'en'
        },
        {
            'text_content': "Economic crisis in India continues to worsen with no solutions in sight",
            'toxicity_score': 0.6,
            'stance_score': -0.7,
            'platform': 'reddit',
            'language': 'en'
        },
        {
            'text_content': "Kashmir situation needs international intervention urgently",
            'toxicity_score': 0.5,
            'stance_score': -0.6,
            'platform': 'twitter',
            'language': 'en'
        },
        {
            'text_content': "Human rights violations in Kashmir continue to increase",
            'toxicity_score': 0.6,
            'stance_score': -0.7,
            'platform': 'reddit',
            'language': 'en'
        },
        {
            'text_content': "India's space program achievements are remarkable and cost-effective",
            'toxicity_score': 0.1,
            'stance_score': 0.8,
            'platform': 'twitter',
            'language': 'en'
        }
    ]
    
    result = clusterer.cluster_narratives(sample_posts)
    
    print("Clustering Results:")
    print(f"Number of clusters: {result['num_clusters']}")
    print(f"Noise posts: {result['noise_posts']}")
    
    for cluster_id, cluster_data in result['clusters'].items():
        narrative = result['narrative_mapping'].get(cluster_id, 'other')
        print(f"\nCluster {cluster_id} ({narrative}):")
        print(f"  Size: {cluster_data['size']}")
        print(f"  Keywords: {cluster_data['keywords'][:5]}")
        print(f"  Avg Toxicity: {cluster_data['statistics'].get('avg_toxicity', 0):.2f}")
        print(f"  Avg Stance: {cluster_data['statistics'].get('avg_stance', 0):.2f}")