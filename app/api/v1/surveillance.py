"""
Surveillance System API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.core.config import settings
from app.services.ai_service import AIService
from app.services.alert_service import AlertService
from app.services.notification_service import NotificationService
from app.api.v1.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

# Request/Response models
class SystemStatusResponse(BaseModel):
    status: str
    uptime: str
    version: str
    active_cameras: int
    active_alerts: int
    system_health: Dict[str, Any]
    last_check: str

class VideoAnalysisRequest(BaseModel):
    video_path: str

class VideoAnalysisResponse(BaseModel):
    analysis_id: str
    status: str
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class NotificationTestRequest(BaseModel):
    channel: str = "all"  # email, sms, webhook, push, all

class SystemConfigResponse(BaseModel):
    camera_settings: Dict[str, Any]
    biometric_settings: Dict[str, Any]
    ai_settings: Dict[str, Any]
    alert_settings: Dict[str, Any]
    notification_settings: Dict[str, Any]

@router.get("/status", response_model=SystemStatusResponse)
async def get_system_status(
    current_user: dict = Depends(get_current_user),
    ai_service: AIService = Depends(lambda: AIService()),
    alert_service: AlertService = Depends(lambda: AlertService())
):
    """Get overall system status"""
    try:
        # Get system health information
        system_health = {
            "ai_service": "operational" if ai_service.initialized else "offline",
            "database": "operational",
            "storage": "operational",
            "network": "operational"
        }
        
        # Get active alerts count
        active_alerts = await alert_service.get_active_alerts(limit=1000)
        
        return SystemStatusResponse(
            status="operational",
            uptime="1 day, 2 hours, 30 minutes",  # This would be calculated from startup time
            version=settings.VERSION,
            active_cameras=0,  # This would be from camera service
            active_alerts=len(active_alerts),
            system_health=system_health,
            last_check=datetime.utcnow().isoformat()
        )
    
    except Exception as e:
        logger.error(f"Get system status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get system status"
        )

@router.post("/analyze-video", response_model=VideoAnalysisResponse)
async def analyze_video(
    video_file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    ai_service: AIService = Depends(lambda: AIService())
):
    """Analyze uploaded video for events"""
    try:
        # Check permissions
        if not current_user.get("is_admin") and not current_user.get("is_security_officer"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Validate file type
        if not video_file.content_type.startswith("video/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Please upload a video file."
            )
        
        # Save uploaded file
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
            content = await video_file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            # Analyze video
            analysis_result = await ai_service.analyze_video(tmp_path)
            
            # Generate analysis ID
            analysis_id = f"analysis_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            return VideoAnalysisResponse(
                analysis_id=analysis_id,
                status="completed",
                results=analysis_result
            )
        
        finally:
            # Clean up temporary file
            os.unlink(tmp_path)
    
    except Exception as e:
        logger.error(f"Video analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Video analysis failed"
        )

@router.post("/test-notifications")
async def test_notifications(
    request: NotificationTestRequest,
    current_user: dict = Depends(get_current_user),
    notification_service: NotificationService = Depends(lambda: NotificationService())
):
    """Test notification system"""
    try:
        # Check permissions
        if not current_user.get("is_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Send test notifications
        results = await notification_service.send_test_notification(request.channel)
        
        return {
            "message": "Test notifications sent",
            "results": results,
            "channel": request.channel
        }
    
    except Exception as e:
        logger.error(f"Test notifications error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test notifications"
        )

@router.get("/config", response_model=SystemConfigResponse)
async def get_system_config(
    current_user: dict = Depends(get_current_user)
):
    """Get system configuration"""
    try:
        # Check permissions
        if not current_user.get("is_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return SystemConfigResponse(
            camera_settings={
                "resolution_width": settings.CAMERA_RESOLUTION_WIDTH,
                "resolution_height": settings.CAMERA_RESOLUTION_HEIGHT,
                "fps": settings.CAMERA_FPS,
                "night_vision_threshold": settings.NIGHT_VISION_THRESHOLD,
                "motion_detection_sensitivity": settings.MOTION_DETECTION_SENSITIVITY
            },
            biometric_settings={
                "face_recognition_tolerance": settings.FACE_RECOGNITION_TOLERANCE,
                "fingerprint_threshold": settings.FINGERPRINT_THRESHOLD,
                "iris_recognition_enabled": settings.IRIS_RECOGNITION_ENABLED,
                "biometric_timeout": settings.BIOMETRIC_TIMEOUT
            },
            ai_settings={
                "model_path": settings.AI_MODEL_PATH,
                "emergency_detection_threshold": settings.EMERGENCY_DETECTION_THRESHOLD,
                "violence_detection_enabled": settings.VIOLENCE_DETECTION_ENABLED,
                "anomaly_detection_enabled": settings.ANOMALY_DETECTION_ENABLED
            },
            alert_settings={
                "recording_enabled": settings.RECORDING_ENABLED,
                "recording_duration": settings.RECORDING_DURATION,
                "alert_cooldown": settings.ALERT_COOLDOWN
            },
            notification_settings={
                "email_enabled": settings.EMAIL_ENABLED,
                "sms_enabled": settings.SMS_ENABLED,
                "webhook_url": settings.WEBHOOK_URL is not None
            }
        )
    
    except Exception as e:
        logger.error(f"Get system config error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get system configuration"
        )

@router.get("/health")
async def health_check():
    """Detailed health check endpoint"""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": settings.VERSION,
            "services": {
                "database": "operational",
                "redis": "operational",
                "ai_service": "operational",
                "camera_service": "operational",
                "biometric_service": "operational",
                "alert_service": "operational",
                "notification_service": "operational"
            },
            "system_resources": {
                "cpu_usage": "25%",
                "memory_usage": "60%",
                "disk_usage": "40%",
                "network_status": "connected"
            }
        }
        
        return health_status
    
    except Exception as e:
        logger.error(f"Health check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed"
        )

@router.get("/logs")
async def get_system_logs(
    limit: int = 100,
    level: str = "INFO",
    current_user: dict = Depends(get_current_user)
):
    """Get system logs"""
    try:
        # Check permissions
        if not current_user.get("is_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # This would typically read from log files
        # For simulation, return mock logs
        logs = [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "INFO",
                "message": "System startup completed",
                "module": "main"
            },
            {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "INFO",
                "message": "Camera monitoring started",
                "module": "camera_service"
            },
            {
                "timestamp": datetime.utcnow().isoformat(),
                "level": "INFO",
                "message": "AI services initialized",
                "module": "ai_service"
            }
        ]
        
        return {
            "logs": logs[:limit],
            "total": len(logs),
            "level": level
        }
    
    except Exception as e:
        logger.error(f"Get system logs error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get system logs"
        )

@router.post("/maintenance")
async def maintenance_mode(
    enable: bool,
    current_user: dict = Depends(get_current_user)
):
    """Enable/disable maintenance mode"""
    try:
        # Check permissions
        if not current_user.get("is_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # This would typically set a global maintenance flag
        # For simulation, just return success
        return {
            "message": f"Maintenance mode {'enabled' if enable else 'disabled'}",
            "maintenance_mode": enable,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Maintenance mode error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update maintenance mode"
        )

@router.get("/metrics")
async def get_system_metrics(
    current_user: dict = Depends(get_current_user)
):
    """Get system performance metrics"""
    try:
        # Check permissions
        if not current_user.get("is_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # This would typically collect real metrics
        # For simulation, return mock metrics
        metrics = {
            "system": {
                "cpu_usage_percent": 25.5,
                "memory_usage_percent": 60.2,
                "disk_usage_percent": 40.8,
                "network_rx_bytes": 1024000,
                "network_tx_bytes": 512000
            },
            "application": {
                "active_connections": 15,
                "requests_per_minute": 120,
                "average_response_time": 150,
                "error_rate_percent": 0.1
            },
            "surveillance": {
                "frames_processed": 50000,
                "alerts_generated": 25,
                "storage_used_gb": 150.5,
                "uptime_hours": 26.5
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return metrics
    
    except Exception as e:
        logger.error(f"Get system metrics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get system metrics"
        )