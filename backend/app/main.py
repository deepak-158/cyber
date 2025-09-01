"""
FastAPI Backend Main Application
Provides REST API endpoints for the Cyber Threat Detection system
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import asyncio

# ✅ Use absolute imports
from backend.app.core.config import settings
from backend.app.database.database import get_db_session, check_database_health
from backend.app.models import Post, Author, Campaign, Alert, CampaignPost  # 🔥 fixed import
from backend.app.services.data_ingestion import DataIngestionPipeline
from backend.app.detection.campaign_scoring import create_campaign_scorer

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


# Utility Functions
async def run_data_collection():
    """Background task for data collection"""
    try:
        logger.info("Starting background data collection")
        await asyncio.sleep(1)  # Placeholder
        logger.info("Data collection completed")
    except Exception as e:
        logger.error(f"Data collection error: {str(e)}")


# Exception Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "timestamp": datetime.now().isoformat()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
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
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
