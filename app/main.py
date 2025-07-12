"""
Smart Surveillance System - Main Application
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1 import api_router
from app.core.database import create_tables
from app.services.camera_service import CameraService
from app.services.biometric_service import BiometricService
from app.services.ai_service import AIService

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Global services
camera_service = CameraService()
biometric_service = BiometricService()
ai_service = AIService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    logger.info("Starting Smart Surveillance System...")
    
    # Initialize database
    await create_tables()
    
    # Initialize services
    await camera_service.initialize()
    await biometric_service.initialize()
    await ai_service.initialize()
    
    logger.info("Smart Surveillance System started successfully!")
    
    yield
    
    # Cleanup
    logger.info("Shutting down Smart Surveillance System...")
    await camera_service.cleanup()
    await biometric_service.cleanup()
    await ai_service.cleanup()
    logger.info("Smart Surveillance System shut down complete.")

# Create FastAPI app
app = FastAPI(
    title="Smart Surveillance System",
    description="A comprehensive surveillance system with biometric security and AI-enabled emergency response",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API routes
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "Smart Surveillance System is running",
        "version": "1.0.0"
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Smart Surveillance System API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )