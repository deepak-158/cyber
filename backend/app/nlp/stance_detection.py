"""
Stance Detection Module for Anti-India Narrative Identification
Detects stance towards India in text content across multiple languages
Uses simplified rule-based approaches
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Union, Tuple
import re
import random
import os

logger = logging.getLogger(__name__)

class StanceDetector:
    """Simplified stance detection for identifying anti-India narratives"""
    
    def __init__(self, model_cache_dir: str = "./models/checkpoints"):
        self.model_cache_dir = model_cache_dir
        
        # Stance categories
        self.stance_labels = {
            'anti_india': 'Content opposing or criticizing India',
            'pro_india': 'Content supporting or praising India', 
            'neutral': 'Content that is neutral about India',
            'not_relevant': 'Content not related to India'
        }
        
        # Target topics for stance detection
        self.india_topics = {
            'economy': ['economy', 'gdp', 'unemployment', 'poverty', 'economic growth', 'recession'],
            'politics': ['government', 'democracy', 'election', 'corruption', 'politics', 'modi', 'congress'],
            'military': ['military', 'army', 'defense', 'border', 'security', 'terrorism', 'war'],
            'society': ['culture', 'religion', 'hindu', 'muslim', 'caste', 'society', 'tradition'],
            'international': ['pakistan', 'china', 'relations', 'diplomacy', 'foreign policy', 'trade'],
            'kashmir': ['kashmir', 'article 370', 'pok', 'azad kashmir', 'loc', 'ceasefire'],
            'general': ['india', 'indian', 'bharat', 'hindustan', 'delhi', 'mumbai', 'bangalore']
        }
        
        # Load stance indicators
        self._load_stance_indicators()
        
        logger.info("Simplified stance detector initialized")
    

    
    def detect_stance(self, text: str, language: str = 'en') -> Dict[str, Union[float, str, Dict]]:
        """
        Detect stance towards India in the given text
        
        Args:
            text: Input text to analyze
            language: Language code of the text
            
        Returns:
            Dict containing:
            - stance_scores: Scores for each stance category
            - primary_stance: Main detected stance
            - confidence: Confidence in prediction
            - relevant_topics: India-related topics found
            - stance_indicators: Specific words/phrases that indicate stance
            - sentiment_scores: Overall sentiment analysis
        """
        if not text or len(text.strip()) < 3:
            return self._empty_stance_result()
        
        cleaned_text = self._preprocess_text(text)
        
        # Check if text is relevant to India
        relevance_result = self._check_india_relevance(cleaned_text)
        if not relevance_result['is_relevant']:
            return {
                'stance_scores': {'not_relevant': 1.0, 'anti_india': 0.0, 'pro_india': 0.0, 'neutral': 0.0},
                'primary_stance': 'not_relevant',
                'confidence': relevance_result['confidence'],
                'relevant_topics': [],
                'stance_indicators': [],
                'sentiment_scores': {'positive': 0.33, 'negative': 0.33, 'neutral': 0.34}
            }
        
        # Detect stance using rule-based approach
        rule_based_result = self._detect_with_rules(cleaned_text, language)
        sentiment_result = self._analyze_sentiment_simple(cleaned_text)
        
        # Combine results
        combined_result = self._combine_stance_results(
            rule_based_result, sentiment_result, relevance_result
        )
        
        return combined_result
    
    def _check_india_relevance(self, text: str) -> Dict[str, Union[bool, float, List[str]]]:
        """Check if text is relevant to India"""
        text_lower = text.lower()
        
        relevant_topics = []
        relevance_score = 0.0
        
        # Check for India-related keywords
        for topic, keywords in self.india_topics.items():
            found_keywords = [kw for kw in keywords if kw in text_lower]
            if found_keywords:
                relevant_topics.append(topic)
                relevance_score += len(found_keywords) * 0.1
        
        # Direct mentions of India
        india_mentions = len(re.findall(r'\b(india|indian|bharat|hindustan)\b', text_lower))
        relevance_score += india_mentions * 0.2
        
        # Normalize score
        relevance_score = min(1.0, relevance_score)
        
        is_relevant = relevance_score > 0.3 or len(relevant_topics) > 0
        
        return {
            'is_relevant': is_relevant,
            'confidence': relevance_score,
            'relevant_topics': relevant_topics
        }
    

    
    def _detect_with_rules(self, text: str, language: str) -> Dict:
        """Rule-based stance detection"""
        text_lower = text.lower()
        
        # Initialize scores
        anti_india_score = 0.0
        pro_india_score = 0.0
        neutral_score = 0.0
        
        stance_indicators = []
        
        # Anti-India indicators
        anti_indicators = self.stance_indicators['anti_india'][language]
        for indicator in anti_indicators:
            if indicator.lower() in text_lower:
                anti_india_score += 0.3
                stance_indicators.append(f"anti: {indicator}")
        
        # Pro-India indicators  
        pro_indicators = self.stance_indicators['pro_india'][language]
        for indicator in pro_indicators:
            if indicator.lower() in text_lower:
                pro_india_score += 0.3
                stance_indicators.append(f"pro: {indicator}")
        
        # Context-based scoring
        context_score = self._analyze_context(text_lower)
        anti_india_score += context_score['anti_india']
        pro_india_score += context_score['pro_india']
        
        # If no clear indicators, lean towards neutral
        if anti_india_score == 0 and pro_india_score == 0:
            neutral_score = 0.8
        else:
            neutral_score = max(0.0, 1.0 - anti_india_score - pro_india_score)
        
        # Normalize scores
        total_score = anti_india_score + pro_india_score + neutral_score
        if total_score > 0:
            anti_india_score /= total_score
            pro_india_score /= total_score
            neutral_score /= total_score
        
        stance_scores = {
            'anti_india': min(1.0, anti_india_score),
            'pro_india': min(1.0, pro_india_score),
            'neutral': min(1.0, neutral_score)
        }
        
        primary_stance = max(stance_scores, key=stance_scores.get)
        confidence = stance_scores[primary_stance]
        
        return {
            'stance_scores': stance_scores,
            'primary_stance': primary_stance,
            'confidence': confidence,
            'stance_indicators': stance_indicators,
            'method': 'rule_based'
        }
    
    def _analyze_context(self, text: str) -> Dict[str, float]:
        """Analyze context for stance indicators"""
        anti_score = 0.0
        pro_score = 0.0
        
        # Economic criticism patterns
        economic_negative = [
            'economy collaps', 'unemployment high', 'poverty increas',
            'economic crisis', 'gdp fall', 'recession', 'inflation'
        ]
        for pattern in economic_negative:
            if pattern in text:
                anti_score += 0.2
        
        # Economic praise patterns
        economic_positive = [
            'economy grow', 'gdp increas', 'economic succes',
            'development', 'progress', 'prosperity', 'growth'
        ]
        for pattern in economic_positive:
            if pattern in text:
                pro_score += 0.2
        
        # Security/military context
        if any(word in text for word in ['terrorist', 'attack', 'violence', 'conflict']):
            # Check if India is portrayed as victim or aggressor
            if any(phrase in text for phrase in ['india attack', 'india aggress', 'india occupi']):
                anti_score += 0.3
            elif any(phrase in text for phrase in ['attack on india', 'terror in india', 'victim']):
                pro_score += 0.2
        
        # International relations
        if any(word in text for word in ['pakistan', 'china', 'border', 'dispute']):
            if any(phrase in text for phrase in ['india wrong', 'india fault', 'india aggressive']):
                anti_score += 0.2
            elif any(phrase in text for phrase in ['india defend', 'india right', 'support india']):
                pro_score += 0.2
        
        return {'anti_india': min(0.5, anti_score), 'pro_india': min(0.5, pro_score)}
    
    def _analyze_sentiment_simple(self, text: str) -> Dict:
        """Simple rule-based sentiment analysis"""
        text_lower = text.lower()
        
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love', 'like', 'support', 'praise', 'success', 'progress', 'development']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'hate', 'dislike', 'fail', 'failure', 'crisis', 'problem', 'issue', 'corrupt', 'weak']
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        total = positive_count + negative_count
        if total == 0:
            return {'positive': 0.33, 'negative': 0.33, 'neutral': 0.34}
        
        positive_score = positive_count / total
        negative_score = negative_count / total
        neutral_score = max(0.0, 1.0 - positive_score - negative_score)
        
        return {
            'positive': positive_score,
            'negative': negative_score,
            'neutral': neutral_score
        }
    
    def _combine_stance_results(self, rule_result: Dict, sentiment_result: Dict,
                              relevance_result: Dict) -> Dict:
        """Combine results from rule-based stance detection and sentiment analysis"""
        
        # Use rule-based results as primary
        final_stance_scores = rule_result['stance_scores'].copy()
        
        # Add not_relevant score
        final_stance_scores['not_relevant'] = 0.0
        
        # Determine primary stance
        primary_stance = max(final_stance_scores, key=final_stance_scores.get)
        confidence = final_stance_scores[primary_stance]
        
        # Get stance indicators
        stance_indicators = rule_result.get('stance_indicators', [])
        
        return {
            'stance_scores': final_stance_scores,
            'primary_stance': primary_stance,
            'confidence': confidence,
            'relevant_topics': relevance_result['relevant_topics'],
            'stance_indicators': stance_indicators,
            'sentiment_scores': sentiment_result
        }
    
    def _load_stance_indicators(self):
        """Load stance indicator words/phrases for different languages"""
        self.stance_indicators = {
            'anti_india': {
                'en': [
                    'india fail', 'india collaps', 'india weak', 'india corrupt',
                    'india terror', 'india occupi', 'india aggress', 'india evil',
                    'hate india', 'destroy india', 'india enemy', 'india bad',
                    'india wrong', 'india lies', 'india propaganda', 'fake india',
                    'india oppress', 'india violat', 'india illegal', 'india fraud'
                ],
                'hi': [
                    'भारत बुरा', 'भारत गलत', 'भारत दुश्मन', 'भारत कमजोर',
                    'भारत झूठ', 'भारत धोखा', 'भारत अत्याचार', 'भारत नफरत'
                ],
                'ur': [
                    'بھارت برا', 'بھارت غلط', 'بھارت دشمن', 'بھارت کمزور',
                    'بھارت جھوٹ', 'بھارت دھوکہ'
                ],
                'mixed': [
                    'india bad hai', 'india ganda hai', 'india galat hai',
                    'india bekar hai', 'india nautanki', 'india fake hai'
                ]
            },
            'pro_india': {
                'en': [
                    'india great', 'india strong', 'india success', 'india grow',
                    'love india', 'proud india', 'india good', 'india right',
                    'india develop', 'india progress', 'india superpower', 'jai hind',
                    'bharat mata', 'incredible india', 'shining india', 'india rise'
                ],
                'hi': [
                    'भारत महान', 'भारत अच्छा', 'भारत मजबूत', 'भारत प्रगति',
                    'जय हिंद', 'भारत माता', 'वंदे मातरम्', 'भारत गर्व'
                ],
                'ur': [
                    'بھارت اچھا', 'بھارت مضبوط', 'بھارت ترقی'
                ],
                'mixed': [
                    'india accha hai', 'india best hai', 'india strong hai',
                    'proud of india', 'jai hind', 'bharat mata ki jai'
                ]
            }
        }
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for stance detection"""
        # Remove URLs
        text = re.sub(r'http[s]?://\S+', '', text)
        
        # Remove excessive punctuation but keep sentence structure
        text = re.sub(r'[!?.]{3,}', '...', text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def _empty_stance_result(self) -> Dict:
        """Return empty result for invalid input"""
        return {
            'stance_scores': {'not_relevant': 1.0, 'anti_india': 0.0, 'pro_india': 0.0, 'neutral': 0.0},
            'primary_stance': 'not_relevant',
            'confidence': 1.0,
            'relevant_topics': [],
            'stance_indicators': [],
            'sentiment_scores': {'positive': 0.33, 'negative': 0.33, 'neutral': 0.34}
        }
    
    def detect_batch_stance(self, texts: List[str], languages: List[str] = None) -> List[Dict]:
        """Detect stance for a batch of texts"""
        if languages is None:
            languages = ['en'] * len(texts)
        
        results = []
        for text, lang in zip(texts, languages):
            result = self.detect_stance(text, lang)
            results.append(result)
        
        return results
    
    def get_stance_summary(self, texts: List[str], languages: List[str] = None) -> Dict:
        """Generate stance analysis summary for multiple texts"""
        results = self.detect_batch_stance(texts, languages)
        
        total_texts = len(texts)
        relevant_texts = sum(1 for r in results if r['primary_stance'] != 'not_relevant')
        
        stance_distribution = {}
        for stance in ['anti_india', 'pro_india', 'neutral', 'not_relevant']:
            count = sum(1 for r in results if r['primary_stance'] == stance)
            stance_distribution[stance] = count
        
        # Calculate average stance scores
        avg_stance_scores = {}
        for stance in ['anti_india', 'pro_india', 'neutral']:
            avg_score = sum(r['stance_scores'][stance] for r in results) / total_texts
            avg_stance_scores[stance] = avg_score
        
        # Find most common topics
        all_topics = []
        for result in results:
            all_topics.extend(result['relevant_topics'])
        
        topic_counts = {}
        for topic in all_topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        return {
            'total_texts': total_texts,
            'relevant_texts': relevant_texts,
            'relevance_rate': relevant_texts / total_texts,
            'stance_distribution': stance_distribution,
            'average_stance_scores': avg_stance_scores,
            'common_topics': sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            'detailed_results': results
        }

def create_stance_detector(model_cache_dir: str = "./models/checkpoints") -> StanceDetector:
    """Factory function to create a stance detector instance"""
    return StanceDetector(model_cache_dir)

# Example usage
if __name__ == "__main__":
    detector = StanceDetector()
    
    test_texts = [
        "India is a great country with rich culture and heritage",
        "India's economy is collapsing and unemployment is at record high",
        "यह भारत के लिए गर्व का विषय है",  # Hindi pro-India
        "भारत की अर्थव्यवस्था बहुत खराब है",  # Hindi anti-India  
        "India accha country hai but government bahut corrupt hai",  # Hinglish mixed
        "The weather is nice today",  # Not relevant
        "Kashmir issue needs international intervention urgently",
        "India's space program achievements are remarkable"
    ]
    
    for text in test_texts:
        result = detector.detect_stance(text)
        print(f"Text: {text}")
        print(f"Primary Stance: {result['primary_stance']}")
        print(f"Confidence: {result['confidence']:.3f}")
        print(f"Stance Scores: {result['stance_scores']}")
        print(f"Topics: {result['relevant_topics']}")
        print("-" * 50)