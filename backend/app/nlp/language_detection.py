"""
Multilingual Language Detection Module
Detects languages with focus on Indian languages and mixed content (Hinglish)
"""

import logging
from typing import Dict, List, Optional, Tuple
import re
import langdetect
from langdetect import detect, detect_langs
from langdetect.lang_detect_exception import LangDetectException
import langid
import unicodedata

logger = logging.getLogger(__name__)

class LanguageDetector:
    """Advanced language detection with support for Indian languages and code-mixing"""
    
    def __init__(self):
        self.supported_languages = {
            'en': 'English',
            'hi': 'Hindi',
            'mr': 'Marathi',
            'ta': 'Tamil',
            'te': 'Telugu',
            'gu': 'Gujarati',
            'bn': 'Bengali',
            'kn': 'Kannada',
            'ml': 'Malayalam',
            'or': 'Odia',
            'pa': 'Punjabi',
            'as': 'Assamese',
            'ur': 'Urdu',
            'ne': 'Nepali'
        }
        
        # Hindi/Devanagari script characters range
        self.devanagari_range = (0x0900, 0x097F)
        
        # Common Hindi/English mixed patterns
        self.hinglish_patterns = [
            r'\b(aur|hai|hain|kar|ke|ki|ko|me|se|pe|par|kya|kyun|kaise|kab|kahan|who|what|when|where|why|how)\b',
            r'\b(yaar|bhai|dude|bro|sir|ji|sahab|uncle|aunty)\b',
            r'\b(accha|theek|sahi|galat|wrong|right|good|bad|nice|awesome|cool)\b'
        ]
        
        # Configure langid
        langid.set_languages(['en', 'hi', 'ur', 'bn', 'ta', 'te', 'gu', 'mr', 'ml', 'kn', 'or', 'pa', 'as'])
    
    def detect_language(self, text: str) -> Dict[str, any]:
        """
        Detect language of text with confidence scores
        
        Returns:
            Dict containing:
            - primary_language: Most likely language code
            - confidence: Confidence score (0-1)
            - all_probabilities: Dict of all language probabilities
            - is_mixed: Boolean indicating if text contains multiple languages
            - mixed_languages: List of detected languages if mixed
        """
        if not text or len(text.strip()) < 3:
            return {
                'primary_language': 'unknown',
                'confidence': 0.0,
                'all_probabilities': {},
                'is_mixed': False,
                'mixed_languages': []
            }
        
        cleaned_text = self._preprocess_text(text)
        
        # Check for obvious script-based detection first
        script_detection = self._detect_by_script(cleaned_text)
        if script_detection:
            return script_detection
        
        # Use multiple detection methods
        langdetect_result = self._detect_with_langdetect(cleaned_text)
        langid_result = self._detect_with_langid(cleaned_text)
        
        # Check for code-mixing (Hinglish)
        mixing_result = self._detect_code_mixing(cleaned_text)
        
        # Combine results with confidence weighting
        final_result = self._combine_detection_results(
            langdetect_result, langid_result, mixing_result, cleaned_text
        )
        
        return final_result
    
    def _preprocess_text(self, text: str) -> str:
        """Clean and preprocess text for language detection"""
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove mentions and hashtags for cleaner detection
        text = re.sub(r'@\w+|#\w+', '', text)
        
        # Remove excessive punctuation and special characters
        text = re.sub(r'[^\w\s\u0900-\u097F]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    def _detect_by_script(self, text: str) -> Optional[Dict]:
        """Detect language based on script/character ranges"""
        if not text:
            return None
        
        # Count characters in different scripts
        devanagari_chars = 0
        latin_chars = 0
        total_chars = 0
        
        for char in text:
            if char.isalpha():
                total_chars += 1
                code_point = ord(char)
                
                if self.devanagari_range[0] <= code_point <= self.devanagari_range[1]:
                    devanagari_chars += 1
                elif 'a' <= char.lower() <= 'z':
                    latin_chars += 1
        
        if total_chars == 0:
            return None
        
        devanagari_ratio = devanagari_chars / total_chars
        latin_ratio = latin_chars / total_chars
        
        # Strong Devanagari presence suggests Hindi
        if devanagari_ratio > 0.7:
            return {
                'primary_language': 'hi',
                'confidence': min(0.95, devanagari_ratio),
                'all_probabilities': {'hi': devanagari_ratio, 'en': 1 - devanagari_ratio},
                'is_mixed': devanagari_ratio < 0.9,
                'mixed_languages': ['hi', 'en'] if devanagari_ratio < 0.9 else ['hi']
            }
        
        # Mixed script suggests Hinglish
        if devanagari_ratio > 0.1 and latin_ratio > 0.3:
            return {
                'primary_language': 'mixed',
                'confidence': 0.8,
                'all_probabilities': {'hi': devanagari_ratio, 'en': latin_ratio, 'mixed': 0.6},
                'is_mixed': True,
                'mixed_languages': ['hi', 'en']
            }
        
        return None
    
    def _detect_with_langdetect(self, text: str) -> Dict:
        """Use langdetect library for detection"""
        try:
            # Single language detection
            primary_lang = detect(text)
            
            # Multiple language probabilities
            lang_probs = detect_langs(text)
            probabilities = {lang.lang: lang.prob for lang in lang_probs}
            
            confidence = probabilities.get(primary_lang, 0.0)
            
            return {
                'primary_language': primary_lang,
                'confidence': confidence,
                'all_probabilities': probabilities
            }
            
        except LangDetectException:
            return {
                'primary_language': 'unknown',
                'confidence': 0.0,
                'all_probabilities': {}
            }
    
    def _detect_with_langid(self, text: str) -> Dict:
        """Use langid library for detection"""
        try:
            lang, confidence = langid.classify(text)
            
            return {
                'primary_language': lang,
                'confidence': confidence,
                'all_probabilities': {lang: confidence}
            }
            
        except Exception as e:
            logger.warning(f"langid detection failed: {str(e)}")
            return {
                'primary_language': 'unknown',
                'confidence': 0.0,
                'all_probabilities': {}
            }
    
    def _detect_code_mixing(self, text: str) -> Dict:
        """Detect code-mixing patterns, particularly Hinglish"""
        hinglish_score = 0.0
        
        # Check for common Hinglish patterns
        for pattern in self.hinglish_patterns:
            matches = re.findall(pattern, text.lower())
            hinglish_score += len(matches) * 0.1
        
        # Check for transliterated Hindi words (common patterns)
        transliteration_patterns = [
            r'\b(kya|hai|hain|main|mein|aur|yeh|woh|koi|kuch|sab|log|time|life|love|feel|think|know)\b',
            r'\b(accha|theek|sahi|bas|bhot|bohot|zyada|kam|jaldi|der|paisa|paise)\b',
            r'\b(ghar|office|school|college|family|friends|party|movie|song|game)\b'
        ]
        
        for pattern in transliteration_patterns:
            matches = re.findall(pattern, text.lower())
            hinglish_score += len(matches) * 0.15
        
        # Normalize score
        hinglish_score = min(1.0, hinglish_score)
        
        is_hinglish = hinglish_score > 0.3
        
        return {
            'is_hinglish': is_hinglish,
            'hinglish_score': hinglish_score,
            'confidence': hinglish_score if is_hinglish else 0.0
        }
    
    def _combine_detection_results(self, langdetect_result: Dict, langid_result: Dict, 
                                 mixing_result: Dict, text: str) -> Dict:
        """Combine results from multiple detection methods"""
        
        # Check for Hinglish first
        if mixing_result.get('is_hinglish', False) and mixing_result['hinglish_score'] > 0.5:
            return {
                'primary_language': 'mixed',
                'confidence': mixing_result['confidence'],
                'all_probabilities': {
                    'mixed': mixing_result['hinglish_score'],
                    'hi': 0.4,
                    'en': 0.4
                },
                'is_mixed': True,
                'mixed_languages': ['hi', 'en']
            }
        
        # Weight the results
        langdetect_weight = 0.6
        langid_weight = 0.4
        
        # Get primary languages
        langdetect_lang = langdetect_result.get('primary_language', 'unknown')
        langid_lang = langid_result.get('primary_language', 'unknown')
        
        # If both agree and confidence is high, use that
        if (langdetect_lang == langid_lang and 
            langdetect_result.get('confidence', 0) > 0.7):
            return {
                'primary_language': langdetect_lang,
                'confidence': langdetect_result['confidence'],
                'all_probabilities': langdetect_result.get('all_probabilities', {}),
                'is_mixed': False,
                'mixed_languages': []
            }
        
        # Combine probabilities with weights
        all_probs = {}
        
        # Add langdetect probabilities
        for lang, prob in langdetect_result.get('all_probabilities', {}).items():
            all_probs[lang] = all_probs.get(lang, 0) + prob * langdetect_weight
        
        # Add langid probabilities
        for lang, prob in langid_result.get('all_probabilities', {}).items():
            all_probs[lang] = all_probs.get(lang, 0) + prob * langid_weight
        
        # Find primary language
        if all_probs:
            primary_lang = max(all_probs, key=all_probs.get)
            confidence = all_probs[primary_lang]
        else:
            primary_lang = 'unknown'
            confidence = 0.0
        
        # Check for mixed content
        is_mixed = False
        mixed_languages = []
        
        if len(all_probs) > 1:
            sorted_probs = sorted(all_probs.items(), key=lambda x: x[1], reverse=True)
            if len(sorted_probs) >= 2 and sorted_probs[1][1] > 0.2:
                is_mixed = True
                mixed_languages = [sorted_probs[0][0], sorted_probs[1][0]]
        
        return {
            'primary_language': primary_lang,
            'confidence': confidence,
            'all_probabilities': all_probs,
            'is_mixed': is_mixed,
            'mixed_languages': mixed_languages
        }
    
    def get_language_name(self, lang_code: str) -> str:
        """Get full language name from code"""
        return self.supported_languages.get(lang_code, lang_code)
    
    def is_indian_language(self, lang_code: str) -> bool:
        """Check if language code represents an Indian language"""
        indian_languages = {'hi', 'mr', 'ta', 'te', 'gu', 'bn', 'kn', 'ml', 'or', 'pa', 'as', 'ur'}
        return lang_code in indian_languages
    
    def detect_batch(self, texts: List[str]) -> List[Dict]:
        """Detect languages for a batch of texts"""
        results = []
        for text in texts:
            result = self.detect_language(text)
            results.append(result)
        return results

def create_language_detector() -> LanguageDetector:
    """Factory function to create a language detector instance"""
    return LanguageDetector()

# Example usage and testing
if __name__ == "__main__":
    detector = LanguageDetector()
    
    # Test cases
    test_texts = [
        "This is a simple English text.",
        "यह एक हिंदी वाक्य है।",
        "Yaar, main office ja raha hun. See you later!",  # Hinglish
        "India ki economy bahut strong hai bro.",  # Hinglish
        "আমি বাংলা ভাষায় কথা বলি।",  # Bengali
        "இது தமிழ் மொழியில் உள்ளது।",  # Tamil
        "ఇది తెలుగు భాషలో ఉంది।",  # Telugu
    ]
    
    for text in test_texts:
        result = detector.detect_language(text)
        print(f"Text: {text}")
        print(f"Result: {result}")
        print("-" * 50)