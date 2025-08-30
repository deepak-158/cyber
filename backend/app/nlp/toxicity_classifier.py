"""
Simplified Toxicity Classification Module
Detects toxic, abusive, and harmful content using rule-based approach
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Union, Tuple
import re
import random

logger = logging.getLogger(__name__)

class ToxicityClassifier:
    """Simplified toxicity classifier with rule-based approach for demo"""
    
    def __init__(self, model_cache_dir: str = "./models/checkpoints"):
        self.model_cache_dir = model_cache_dir
        
        # Toxic word lists for different languages
        self.toxic_words = {
            'en': self._load_english_toxic_words(),
            'hi': self._load_hindi_toxic_words(),
            'ur': self._load_urdu_toxic_words(),
            'mixed': self._load_hinglish_toxic_words()
        }
        
        # Severity levels
        self.severity_levels = {
            'low': (0.3, 0.5),
            'medium': (0.5, 0.7),
            'high': (0.7, 0.85),
            'severe': (0.85, 1.0)
        }
        
        logger.info("Simplified toxicity classifier initialized")
    
    def classify_toxicity(self, text: str, language: str = 'en') -> Dict[str, Union[float, str, Dict]]:
        """
        Classify toxicity of text using simplified rule-based approach
        """
        if not text or len(text.strip()) < 3:
            return self._empty_result()
        
        cleaned_text = self._preprocess_text(text)
        result = self._classify_with_rules(cleaned_text, language)
        result['severity_level'] = self._get_severity_level(result['toxicity_score'])
        
        return result
        
    def _classify_with_rules(self, text: str, language: str) -> Dict:
        """Classify using rule-based approach"""
        toxic_score = 0.0
        toxic_categories = []
        
        # Get relevant toxic word lists
        word_lists = [self.toxic_words.get(language, [])]
        if language in ['hi', 'ur']:
            word_lists.append(self.toxic_words.get('mixed', []))
        
        text_lower = text.lower()
        
        # Check for toxic words
        total_words = len(text.split())
        toxic_word_count = 0
        
        for word_list in word_lists:
            for toxic_word in word_list:
                if toxic_word.lower() in text_lower:
                    toxic_word_count += 1
                    toxic_categories.append('offensive_language')
        
        # Calculate base score from word matches
        if total_words > 0:
            word_ratio = min(toxic_word_count / total_words, 1.0)
            toxic_score = word_ratio * 0.8
        
        # Add some randomness for demo purposes (simulate ML uncertainty)
        if toxic_score > 0:
            toxic_score += random.uniform(0.1, 0.3)
            toxic_score = min(toxic_score, 1.0)
        
        # Check for common toxic patterns
        toxic_patterns = [
            r'\b(hate|kill|die|death)\b',
            r'\b(stupid|idiot|fool|dumb)\b',
            r'\b(threat|violence|attack)\b'
        ]
        
        for pattern in toxic_patterns:
            if re.search(pattern, text_lower):
                toxic_score = max(toxic_score, 0.6)
                toxic_categories.append('hate_speech')
        
        # Ensure minimum score for detected toxicity
        if toxic_categories and toxic_score < 0.3:
            toxic_score = 0.3
        
        return {
            'toxicity_score': float(toxic_score),
            'confidence': 0.7 if toxic_score > 0.3 else 0.9,
            'toxic_categories': list(set(toxic_categories)),
            'model_used': 'rule_based'
        }
    
    def _empty_result(self) -> Dict:
        """Return empty toxicity result"""
        return {
            'toxicity_score': 0.0,
            'severity_level': 'none',
            'confidence': 1.0,
            'toxic_categories': [],
            'model_used': 'none'
        }
    
    def _preprocess_text(self, text: str) -> str:
        """Clean and preprocess text"""
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _get_severity_level(self, score: float) -> str:
        """Determine severity level from toxicity score"""
        if score < 0.3:
            return 'none'
        for level, (min_score, max_score) in self.severity_levels.items():
            if min_score <= score < max_score:
                return level
        return 'severe'
    
    def _load_english_toxic_words(self) -> List[str]:
        """Load English toxic words list"""
        return [
            'hate', 'kill', 'die', 'death', 'stupid', 'idiot', 'fool', 'dumb',
            'threat', 'violence', 'attack', 'destroy', 'evil', 'terrorist',
            'bomb', 'explosive', 'weapon', 'murder', 'assassinate'
        ]
    
    def _load_hindi_toxic_words(self) -> List[str]:
        """Load Hindi toxic words list"""
        return [
            'मूर्ख', 'बेवकूफ', 'गधा', 'कमीना', 'हरामी', 'साला',
            'मार', 'मारना', 'हत्या', 'खत्म'
        ]
    
    def _load_urdu_toxic_words(self) -> List[str]:
        """Load Urdu toxic words list"""
        return [
            'بیوقوف', 'احمق', 'گدھا', 'کمینہ', 'حرامی',
            'مار', 'مارنا', 'قتل', 'ختم'
        ]
    
    def _load_hinglish_toxic_words(self) -> List[str]:
        """Load Hinglish/mixed language toxic words"""
        return [
            'bakwas', 'faltu', 'pagal', 'stupid', 'bewakoof',
            'maar', 'khatam', 'badtameez', 'ghatiya'
        ]


def create_toxicity_classifier(model_cache_dir: str = "./models/checkpoints") -> ToxicityClassifier:
    """Factory function to create a toxicity classifier instance"""
    return ToxicityClassifier(model_cache_dir)