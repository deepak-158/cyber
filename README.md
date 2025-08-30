# Cyber Threat Detection: Anti-India Campaigns on Social Platforms

A comprehensive cybersecurity system for detecting, analyzing, and visualizing coordinated influence campaigns targeting India on social media platforms.

## 🎯 Project Overview

This system employs advanced AI/ML techniques to:
- **Collect** data from multiple social platforms (Twitter/X, Reddit, YouTube)
- **Detect** harmful narratives targeting India (stance detection, toxicity analysis, propaganda techniques)
- **Identify** coordinated inauthentic behavior (CIB) using graph analysis and burst detection
- **Provide** real-time alerts with comprehensive dashboards
- **Support** multilingual content (English, Hindi, Hinglish, and other Indian languages)
- **Ensure** ethical AI practices with human-in-the-loop validation

## 🛠️ Technical Architecture

### Backend Stack
- **FastAPI**: REST API backend
- **PostgreSQL**: Structured data storage
- **Neo4j**: Graph database for social network analysis
- **Redis**: Caching and session management
- **Elasticsearch**: Advanced text search and analytics

### AI/ML Pipeline
- **Language Detection**: Multi-language support with Hinglish detection
- **Toxicity Classification**: Multilingual toxic content detection
- **Stance Detection**: Anti-India narrative identification
- **Narrative Clustering**: Thematic content grouping using embeddings
- **Burst Detection**: Temporal anomaly detection for coordination
- **Bot Likelihood**: Automated account detection

### Frontend
- **Streamlit**: Interactive dashboard for monitoring and analysis
- **Jupyter**: Research environment for model development

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.9+ (for local development)
- 16GB+ RAM recommended
- GPU support recommended for ML models

### 1. Clone and Setup
```bash
cd c:\Users\dipak\OneDrive\Desktop\cyber
```

### 2. Environment Configuration
Create `.env` file:
```bash
# Database Configuration
DATABASE_URL=postgresql://cyber_user:cyber_secure_password_2024@localhost:5432/cyber_threat_db
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=cyber_graph_password_2024
REDIS_URL=redis://localhost:6379

# API Keys (Optional - system works with sample data)
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
TWITTER_BEARER_TOKEN=your_bearer_token

REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password

# Security
SECRET_KEY=cyber_threat_detection_secret_key_2024_secure
ENVIRONMENT=development
```

### 3. Start Services
```bash
docker-compose up -d
```

This will start:
- **PostgreSQL** (port 5432)
- **Neo4j** (ports 7474, 7687)
- **Redis** (port 6379)
- **Elasticsearch** (port 9200)
- **Kibana** (port 5601)
- **Backend API** (port 8000)
- **Frontend Dashboard** (port 8501)
- **Jupyter Lab** (port 8888)

### 4. Access Services
- **Main Dashboard**: http://localhost:8501
- **API Documentation**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474
- **Jupyter Lab**: http://localhost:8888 (token: `cyber_research_token_2024`)
- **Kibana**: http://localhost:5601

## 📊 Key Features

### 1. Data Collection
- **Multi-platform support**: Twitter/X, Reddit, YouTube comments
- **Real-time streaming**: Continuous data ingestion
- **API integration**: Official APIs with fallback to sample data
- **Rate limiting**: Respects platform API limits

### 2. Language Processing
- **Language Detection**: Supports 14+ languages including Indian languages
- **Hinglish Support**: Advanced code-mixing detection
- **Toxicity Analysis**: Multilingual toxic content classification
- **Stance Detection**: Anti-India narrative identification

### 3. Coordination Detection
- **Graph Analysis**: Social network relationship mapping
- **Burst Detection**: Temporal activity anomalies
- **Bot Detection**: Automated account identification
- **Campaign Scoring**: 0-100 threat level assessment

### 4. Monitoring Dashboard
- **Real-time Alerts**: Live threat notifications
- **Interactive Graphs**: Network visualization
- **Narrative Analysis**: Content clustering and trends
- **Audit Trail**: Complete decision transparency

## 🔧 Development Setup

### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend
pip install streamlit plotly pandas
streamlit run dashboard.py
```

### Database Migration
```bash
# PostgreSQL setup
docker exec -it cyber_postgres psql -U cyber_user -d cyber_threat_db -f /docker-entrypoint-initdb.d/init_db.sql

# Neo4j setup
docker exec -it cyber_neo4j cypher-shell -u neo4j -p cyber_graph_password_2024 -f /var/lib/neo4j/import/neo4j_schema.cypher
```

## 📁 Project Structure

```
cyber/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/               # API endpoints
│   │   ├── core/              # Core configuration
│   │   ├── models/            # SQLAlchemy models
│   │   ├── services/          # Business logic
│   │   │   ├── base_collector.py
│   │   │   ├── twitter_collector.py
│   │   │   ├── reddit_collector.py
│   │   │   └── data_ingestion.py
│   │   ├── nlp/               # NLP modules
│   │   │   ├── language_detection.py
│   │   │   ├── toxicity_classifier.py
│   │   │   └── stance_detection.py
│   │   ├── detection/         # Coordination detection
│   │   └── database/          # Database utilities
│   │       ├── init_db.sql
│   │       └── neo4j_schema.cypher
├── frontend/                   # Streamlit dashboard
├── data/                      # Data storage
│   ├── raw/                   # Raw collected data
│   ├── processed/             # Processed data
│   └── samples/               # Sample datasets
├── models/                    # ML model storage
│   └── checkpoints/           # Model checkpoints
├── docs/                      # Documentation
├── tests/                     # Test suites
├── config/                    # Configuration files
├── scripts/                   # Utility scripts
├── docker-compose.yml         # Container orchestration
└── requirements.txt           # Python dependencies
```

## 🔍 API Endpoints

### Data Collection
- `POST /api/v1/collect/start` - Start data collection
- `GET /api/v1/collect/status` - Collection status
- `POST /api/v1/collect/stop` - Stop collection

### Analysis
- `POST /api/v1/analyze/text` - Analyze single text
- `GET /api/v1/campaigns` - List detected campaigns
- `GET /api/v1/campaigns/{id}` - Campaign details
- `GET /api/v1/alerts` - Active alerts

### Monitoring
- `GET /api/v1/stats/dashboard` - Dashboard statistics
- `GET /api/v1/health` - System health check

## 🤖 Machine Learning Models

### Language Detection
- **Primary**: Custom multilingual detector
- **Fallback**: langdetect + langid
- **Specialty**: Hinglish code-mixing detection

### Toxicity Classification
- **English**: unitary/toxic-bert
- **Multilingual**: martin-ha/toxic-comment-model
- **Fallback**: Rule-based classification

### Stance Detection
- **Primary**: facebook/bart-large-mnli (zero-shot)
- **Sentiment**: cardiffnlp/twitter-xlm-roberta-base-sentiment
- **Fallback**: Rule-based stance indicators

## ⚡ Performance Optimization

### Caching Strategy
- **Redis**: API response caching
- **Model Caching**: Persistent model loading
- **Database**: Materialized views for statistics

### Scaling Considerations
- **Horizontal Scaling**: Multiple worker containers
- **Database Partitioning**: Time-based post partitioning
- **GPU Acceleration**: CUDA support for ML models

## 🔒 Security & Privacy

### Data Protection
- **Anonymization**: User data pseudonymization
- **Encryption**: Data at rest and in transit
- **Access Control**: Role-based permissions

### Ethical Considerations
- **Human Oversight**: Required validation for critical decisions
- **Bias Mitigation**: Regular model bias testing
- **Transparency**: Complete audit trails
- **Privacy by Design**: Minimal data collection

## 🚨 Alert Types

### Severity Levels
1. **LOW** (0.3-0.5): Minor suspicious activity
2. **MEDIUM** (0.5-0.7): Moderate coordination detected
3. **HIGH** (0.7-0.85): Significant campaign activity
4. **CRITICAL** (0.85-1.0): Severe coordinated attack

### Alert Categories
- **Burst Activity**: Unusual posting patterns
- **Bot Networks**: Automated account coordination
- **Narrative Amplification**: Coordinated message spreading
- **Toxic Content**: High-toxicity content waves

## 📈 Monitoring & Analytics

### Key Metrics
- **Collection Rate**: Posts per hour by platform
- **Detection Accuracy**: Model performance metrics
- **Campaign Coverage**: Detected vs. actual campaigns
- **Response Time**: Alert to resolution time

### Dashboards
1. **Real-time Monitoring**: Live activity feeds
2. **Campaign Analysis**: Detailed investigation tools
3. **Model Performance**: ML model statistics
4. **System Health**: Infrastructure monitoring

## 🔧 Configuration

### Collection Settings
```python
COLLECTION_CONFIG = {
    'keywords': ['india', 'kashmir', 'pakistan'],
    'languages': ['en', 'hi', 'ur'],
    'max_results_per_platform': 1000,
    'collection_interval_minutes': 60,
    'rate_limit_delay': 1.0
}
```

### Detection Thresholds
```python
DETECTION_THRESHOLDS = {
    'toxicity_threshold': 0.7,
    'stance_threshold': 0.6,
    'bot_likelihood_threshold': 0.8,
    'coordination_score_threshold': 75
}
```

## 🧪 Testing

### Unit Tests
```bash
pytest tests/unit/ -v
```

### Integration Tests
```bash
pytest tests/integration/ -v
```

### Load Testing
```bash
pytest tests/load/ -v
```

## 📚 Additional Resources

### Documentation
- [Ethics Guidelines](docs/ethics.md)
- [API Reference](docs/api.md)
- [Model Documentation](docs/models.md)
- [Deployment Guide](docs/deployment.md)

### Research Papers
- Coordinated Inauthentic Behavior Detection
- Multilingual Stance Detection
- Social Media Influence Campaigns

## 🤝 Contributing

### Development Guidelines
1. Follow PEP 8 style guidelines
2. Write comprehensive tests
3. Document all functions
4. Respect ethical guidelines

### Reporting Issues
- Use GitHub issues for bug reports
- Include system information
- Provide reproducible examples

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Transformers library by Hugging Face
- Neo4j Graph Database
- Streamlit framework
- PostgreSQL database
- Research community for stance detection and coordination analysis

## 📞 Support

For technical support or questions:
- GitHub Issues: [Project Issues](https://github.com/your-repo/issues)
- Documentation: [Wiki](https://github.com/your-repo/wiki)
- Email: support@cyberthreatdetection.com

---

**⚠️ Important Notice**: This system is designed for research and legitimate cybersecurity purposes only. It should be used responsibly with proper human oversight and in compliance with applicable laws and platform terms of service.