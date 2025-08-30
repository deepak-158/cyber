"""
FastAPI Backend Main Application
Provides REST API endpoints for the Cyber Threat Detection system
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import asyncio

from .core.config import settings
from .database.database import get_db_session, check_database_health
from .models.models import Post, Author, Campaign, Alert
from .services.data_ingestion import DataIngestionPipeline
from .detection.campaign_scoring import create_campaign_scorer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Cyber Threat Detection API",
    description="REST API for detecting and analyzing coordinated influence campaigns",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
campaign_scorer = create_campaign_scorer()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Cyber Threat Detection API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        db_health = check_database_health()
        
        return {
            "status": "healthy" if all(db_health.values()) else "degraded",
            "timestamp": datetime.now().isoformat(),
            "services": db_health,
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service unavailable")

# Campaign Endpoints
@app.get("/api/v1/campaigns")
async def get_campaigns(
    skip: int = 0,
    limit: int = 100,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db_session)
):
    """Get list of detected campaigns"""
    try:
        query = db.query(Campaign)
        
        if severity:
            query = query.filter(Campaign.detection_details.op('->')('severity').astext == severity)
        
        if status:
            query = query.filter(Campaign.status == status)
        
        campaigns = query.offset(skip).limit(limit).all()
        
        return {
            "campaigns": [
                {
                    "id": str(campaign.id),
                    "name": campaign.name,
                    "campaign_score": campaign.campaign_score,
                    "status": campaign.status.value,
                    "platforms": campaign.platforms,
                    "languages": campaign.languages,
                    "detected_start_time": campaign.detected_start_time.isoformat(),
                    "total_posts": campaign.total_posts,
                    "unique_authors": campaign.unique_authors
                }
                for campaign in campaigns
            ],
            "total": len(campaigns),
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Error getting campaigns: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/v1/campaigns/{campaign_id}")
async def get_campaign(campaign_id: str, db: Session = Depends(get_db_session)):
    """Get detailed campaign information"""
    try:
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        
        # Get associated posts and alerts
        posts = db.query(Post).join(CampaignPost).filter(
            CampaignPost.campaign_id == campaign_id
        ).limit(100).all()
        
        alerts = db.query(Alert).filter(Alert.campaign_id == campaign_id).all()
        
        return {
            "id": str(campaign.id),
            "name": campaign.name,
            "description": campaign.description,
            "campaign_score": campaign.campaign_score,
            "confidence_score": campaign.confidence_score,
            "status": campaign.status.value,
            "platforms": campaign.platforms,
            "languages": campaign.languages,
            "keywords": campaign.keywords,
            "hashtags": campaign.hashtags,
            "detected_start_time": campaign.detected_start_time.isoformat(),
            "detected_end_time": campaign.detected_end_time.isoformat() if campaign.detected_end_time else None,
            "total_posts": campaign.total_posts,
            "unique_authors": campaign.unique_authors,
            "detection_methods": campaign.detection_methods,
            "detection_details": campaign.detection_details,
            "human_reviewed": campaign.human_reviewed,
            "posts": [
                {
                    "id": str(post.id),
                    "platform_post_id": post.platform_post_id,
                    "text_content": post.text_content[:200] + "..." if len(post.text_content) > 200 else post.text_content,
                    "posted_at": post.posted_at.isoformat(),
                    "toxicity_score": post.toxicity_score,
                    "stance_scores": post.stance_scores
                }
                for post in posts
            ],
            "alerts": [
                {
                    "id": str(alert.id),
                    "title": alert.title,
                    "severity": alert.severity.value,
                    "is_active": alert.is_active,
                    "created_at": alert.created_at.isoformat()
                }
                for alert in alerts
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting campaign {campaign_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Alert Endpoints
@app.get("/api/v1/alerts")
async def get_alerts(
    active_only: bool = True,
    severity: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db_session)
):
    """Get system alerts"""
    try:
        query = db.query(Alert)
        
        if active_only:
            query = query.filter(Alert.is_active == True)
        
        if severity:
            query = query.filter(Alert.severity == severity)
        
        alerts = query.order_by(Alert.created_at.desc()).offset(skip).limit(limit).all()
        
        return {
            "alerts": [
                {
                    "id": str(alert.id),
                    "campaign_id": str(alert.campaign_id),
                    "title": alert.title,
                    "description": alert.description,
                    "severity": alert.severity.value,
                    "trigger_timestamp": alert.trigger_timestamp.isoformat(),
                    "is_active": alert.is_active,
                    "acknowledged": alert.acknowledged,
                    "resolved": alert.resolved,
                    "created_at": alert.created_at.isoformat()
                }
                for alert in alerts
            ],
            "total": len(alerts)
        }
    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Analysis Endpoints
@app.post("/api/v1/analyze/text")
async def analyze_text(request: Dict[str, Any]):
    """Analyze single text for threats"""
    try:
        text = request.get('text', '')
        language = request.get('language', 'en')
        
        if not text:
            raise HTTPException(status_code=400, detail="Text content required")
        
        # Create mock post for analysis
        mock_post = {
            'text_content': text,
            'language': language,
            'author': {'platform_user_id': 'analysis_user', 'username': 'analysis_user'},
            'posted_at': datetime.now().isoformat(),
            'platform': 'analysis',
            'hashtags': [],
            'mentions': []
        }
        
        # Run campaign scoring on single post
        result = campaign_scorer.score_campaign([mock_post])
        
        return {
            "text": text,
            "language": language,
            "analysis": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing text: {str(e)}")
        raise HTTPException(status_code=500, detail="Analysis failed")

@app.post("/api/v1/analyze/campaign")
async def analyze_campaign(request: Dict[str, Any]):
    """Analyze a set of posts as a campaign"""
    try:
        posts = request.get('posts', [])
        
        if not posts:
            raise HTTPException(status_code=400, detail="Posts required for analysis")
        
        # Validate post structure
        for post in posts:
            if 'text_content' not in post:
                raise HTTPException(status_code=400, detail="Each post must have text_content")
        
        # Run campaign analysis
        result = campaign_scorer.score_campaign(posts)
        
        return {
            "posts_analyzed": len(posts),
            "analysis": result,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing campaign: {str(e)}")
        raise HTTPException(status_code=500, detail="Campaign analysis failed")

# Data Collection Endpoints
@app.post("/api/v1/collection/start")
async def start_collection(background_tasks: BackgroundTasks):
    """Start data collection process"""
    try:
        # This would start the background data collection
        # For now, return success message
        background_tasks.add_task(run_data_collection)
        
        return {
            "status": "started",
            "message": "Data collection started in background",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting collection: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to start collection")

@app.get("/api/v1/collection/status")
async def get_collection_status():
    """Get data collection status"""
    try:
        # Mock status for now
        return {
            "status": "running",
            "posts_collected_today": 1250,
            "platforms_active": ["twitter", "reddit"],
            "last_collection": "2024-08-30T18:30:00Z",
            "next_collection": "2024-08-30T19:30:00Z",
            "errors": 0
        }
        
    except Exception as e:
        logger.error(f"Error getting collection status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get status")

# Statistics Endpoints
@app.get("/api/v1/stats/dashboard")
async def get_dashboard_stats(db: Session = Depends(get_db_session)):
    """Get dashboard statistics"""
    try:
        # Get basic counts
        total_campaigns = db.query(Campaign).count()
        active_alerts = db.query(Alert).filter(Alert.is_active == True).count()
        total_posts = db.query(Post).count()
        
        # Get recent high-score campaigns
        high_score_campaigns = db.query(Campaign).filter(
            Campaign.campaign_score > 70
        ).order_by(Campaign.created_at.desc()).limit(5).all()
        
        return {
            "summary": {
                "total_campaigns": total_campaigns,
                "active_alerts": active_alerts,
                "total_posts": total_posts,
                "high_risk_campaigns": len(high_score_campaigns)
            },
            "recent_high_risk": [
                {
                    "id": str(campaign.id),
                    "name": campaign.name,
                    "score": campaign.campaign_score,
                    "detected_at": campaign.created_at.isoformat()
                }
                for campaign in high_score_campaigns
            ],
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get statistics")

# Utility Functions
async def run_data_collection():
    """Background task for data collection"""
    try:
        logger.info("Starting background data collection")
        # Implementation would go here
        await asyncio.sleep(1)  # Placeholder
        logger.info("Data collection completed")
    except Exception as e:
        logger.error(f"Data collection error: {str(e)}")

# Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "status_code": 500,
            "timestamp": datetime.now().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)