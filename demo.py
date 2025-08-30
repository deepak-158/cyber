#!/usr/bin/env python3
"""
Demo script to showcase the Cyber Threat Detection System capabilities
This demonstrates the core functionality without requiring full infrastructure
"""

import sys
import os
import json
from datetime import datetime, timedelta

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def demo_language_detection():
    """Demonstrate language detection capabilities"""
    print("🔍 LANGUAGE DETECTION DEMO")
    print("=" * 50)
    
    try:
        from app.nlp.language_detection import LanguageDetector
        detector = LanguageDetector()
        
        test_texts = [
            "This is a simple English text about India's economy.",
            "यह एक हिंदी वाक्य है जो भारत के बारे में है।",
            "India accha country hai but problems bhi hain yaar.",  # Hinglish
            "आज मौसम बहुत अच्छा है।",
            "Nice weather today, isn't it?"
        ]
        
        for i, text in enumerate(test_texts, 1):
            result = detector.detect_language(text)
            print(f"{i}. Text: {text}")
            print(f"   Language: {result['primary_language']} ({result['confidence']:.2f})")
            print(f"   Mixed: {result['is_mixed']}")
            print()
            
    except ImportError as e:
        print(f"⚠️  Language detection requires: {e}")
        print("📦 Run: pip install langdetect langid")

def demo_stance_detection():
    """Demonstrate stance detection capabilities"""
    print("\n🎯 STANCE DETECTION DEMO")
    print("=" * 50)
    
    try:
        from app.nlp.stance_detection import StanceDetector
        detector = StanceDetector()
        
        test_texts = [
            "India is a great country with rich cultural heritage",
            "India's economy is failing and unemployment is rising",
            "भारत महान है और हमें गर्व होना चाहिए",
            "India accha hai but government corrupt hai",
            "The weather is really nice today"
        ]
        
        for i, text in enumerate(test_texts, 1):
            result = detector.detect_stance(text)
            print(f"{i}. Text: {text}")
            print(f"   Stance: {result['primary_stance']} ({result['confidence']:.2f})")
            print(f"   Topics: {result['relevant_topics']}")
            print()
            
    except ImportError as e:
        print(f"⚠️  Stance detection requires: {e}")
        print("📦 Some dependencies may need to be installed")

def demo_burst_detection():
    """Demonstrate burst detection capabilities"""
    print("\n💥 BURST DETECTION DEMO")
    print("=" * 50)
    
    try:
        from app.detection.burst_detection import BurstDetector
        detector = BurstDetector()
        
        # Create sample time series data
        base_time = datetime.now() - timedelta(hours=48)
        sample_posts = []
        
        # Normal activity
        for hour in range(48):
            posts_this_hour = 2 if hour not in range(12, 16) else 15  # Burst in hours 12-15
            for post_num in range(posts_this_hour):
                sample_posts.append({
                    'posted_at': base_time + timedelta(hours=hour, minutes=post_num*4),
                    'platform': 'twitter',
                    'hashtags': ['#crisis'] if hour in range(12, 16) else ['#general'],
                    'author': {'username': f'user_{post_num % 5}'}
                })
        
        result = detector.detect_bursts(sample_posts)
        
        print(f"📊 Analyzed {result['total_posts']} posts over {result['time_span_hours']} hours")
        print(f"🔥 Kleinberg bursts detected: {len(result['kleinberg_bursts'])}")
        print(f"📈 Z-score anomalies: {len(result['zscore_anomalies'])}")
        print(f"⚠️  Coordination suspected: {result['coordination_indicators']['suspected_coordination']}")
        print(f"📊 Coordination score: {result['coordination_indicators']['coordination_score']:.2f}")
        
        if result['kleinberg_bursts']:
            burst = result['kleinberg_bursts'][0]
            print(f"\n🎯 First burst details:")
            print(f"   Duration: {burst['duration_hours']} hours")
            print(f"   Intensity: {burst['intensity']:.2f}")
            print(f"   Posts: {burst['total_posts']}")
        
    except ImportError as e:
        print(f"⚠️  Burst detection requires: {e}")

def demo_campaign_scoring():
    """Demonstrate campaign scoring capabilities"""
    print("\n🏆 CAMPAIGN SCORING DEMO")
    print("=" * 50)
    
    try:
        from app.detection.campaign_scoring import CampaignScorer
        scorer = CampaignScorer()
        
        # Sample detection results
        sample_results = {
            'toxicity': {
                'toxic_count': 15,
                'total_analyzed': 100,
                'avg_toxicity_score': 0.8
            },
            'stance': {
                'anti_india_count': 25,
                'total_relevant': 80,
                'avg_anti_stance_score': 0.7
            },
            'coordination': {
                'suspected_coordination': True,
                'coordination_score': 0.75,
                'coordinated_users': 30
            },
            'bot_network': {
                'suspected_bots': 20,
                'total_users': 100,
                'avg_bot_score': 0.6
            }
        }
        
        campaign_score = scorer.calculate_campaign_score(sample_results)
        
        print(f"🎯 Overall Campaign Score: {campaign_score['overall_score']:.1f}/100")
        print(f"⚠️  Threat Level: {campaign_score['threat_level'].upper()}")
        print(f"\n📊 Component Scores:")
        for component, score in campaign_score['component_scores'].items():
            print(f"   {component.replace('_', ' ').title()}: {score:.1f}")
        
        print(f"\n🚨 Risk Factors ({len(campaign_score['risk_factors'])}):")
        for risk in campaign_score['risk_factors'][:3]:  # Show top 3
            print(f"   • {risk['factor']}: {risk['description']}")
        
    except ImportError as e:
        print(f"⚠️  Campaign scoring requires: {e}")

def demo_sample_analysis():
    """Demonstrate end-to-end analysis on sample data"""
    print("\n🔬 SAMPLE DATA ANALYSIS DEMO")
    print("=" * 50)
    
    sample_posts = [
        {
            'text': "India is failing economically, unemployment everywhere!",
            'platform': 'twitter',
            'hashtags': ['#IndiaFailing', '#Economic Crisis'],
            'posted_at': datetime.now() - timedelta(minutes=30)
        },
        {
            'text': "Proud to be Indian! Jai Hind! 🇮🇳",
            'platform': 'twitter',
            'hashtags': ['#ProudIndian', '#JaiHind'],
            'posted_at': datetime.now() - timedelta(minutes=15)
        },
        {
            'text': "India accha country hai but corruption bahut zyada hai",
            'platform': 'twitter',
            'hashtags': ['#India', '#Corruption'],
            'posted_at': datetime.now() - timedelta(minutes=5)
        }
    ]
    
    print("📝 Sample Posts Analysis:")
    for i, post in enumerate(sample_posts, 1):
        print(f"\n{i}. {post['text']}")
        print(f"   Platform: {post['platform']}")
        print(f"   Hashtags: {', '.join(post['hashtags'])}")
        print(f"   Posted: {post['posted_at'].strftime('%Y-%m-%d %H:%M')}")
    
    print(f"\n✅ System would analyze these posts for:")
    print("   • Language detection (English/Hindi/Hinglish)")
    print("   • Stance towards India (Pro/Anti/Neutral)")
    print("   • Toxicity levels")
    print("   • Coordination patterns")
    print("   • Bot likelihood scores")
    print("   • Narrative clustering")
    print("   • Temporal burst detection")

def show_system_overview():
    """Show system capabilities overview"""
    print("🛡️  CYBER THREAT DETECTION SYSTEM")
    print("=" * 60)
    print("🎯 CAPABILITIES:")
    print("   ✅ Multi-platform data collection (Twitter, Reddit, YouTube)")
    print("   ✅ Multilingual processing (English, Hindi, Hinglish + 12 more)")
    print("   ✅ Anti-India narrative detection")
    print("   ✅ Toxicity classification")
    print("   ✅ Coordinated behavior detection")
    print("   ✅ Bot network identification")
    print("   ✅ Temporal burst analysis")
    print("   ✅ Campaign threat scoring (0-100)")
    print("   ✅ Real-time alerting")
    print("   ✅ Interactive dashboard")
    print("   ✅ Ethical AI safeguards")
    
    print("\n🏗️  ARCHITECTURE:")
    print("   📊 Streamlit Dashboard (Port 8501)")
    print("   🔗 FastAPI Backend (Port 8000)")
    print("   🗄️  PostgreSQL Database")
    print("   🕸️  Neo4j Graph Database")
    print("   🔴 Redis Cache")
    print("   🐳 Docker Containerized")
    
    print("\n📦 DEPLOYMENT:")
    print("   • docker-compose up -d")
    print("   • python quick_start.py")
    print("   • Automated setup and initialization")

def main():
    """Main demo function"""
    show_system_overview()
    
    print("\n" + "="*60)
    print("🚀 RUNNING COMPONENT DEMOS...")
    print("="*60)
    
    # Run individual component demos
    demo_language_detection()
    demo_stance_detection()
    demo_burst_detection()
    demo_campaign_scoring()
    demo_sample_analysis()
    
    print("\n" + "="*60)
    print("✅ DEMO COMPLETED!")
    print("📖 For full documentation, see README.md")
    print("⚙️  To start the complete system: python quick_start.py")
    print("🧪 To run tests: python run_tests.py")
    print("="*60)

if __name__ == "__main__":
    main()