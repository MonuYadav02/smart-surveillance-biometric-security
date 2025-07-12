"""
Alert Management API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from app.core.config import settings
from app.services.alert_service import AlertService
from app.models.alert import Alert
from app.api.v1.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

# Request/Response models
class AlertResponse(BaseModel):
    id: int
    alert_type: str
    severity: str
    status: str
    title: str
    description: Optional[str]
    confidence_score: Optional[float]
    camera_id: Optional[int]
    location: Optional[str]
    coordinates: Optional[Dict[str, Any]]
    detected_objects: Optional[List[Dict[str, Any]]]
    biometric_data: Optional[Dict[str, Any]]
    ai_analysis: Optional[Dict[str, Any]]
    image_path: Optional[str]
    video_path: Optional[str]
    user_id: Optional[int]
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]
    response_time: Optional[float]
    email_sent: bool
    sms_sent: bool
    webhook_sent: bool
    created_at: datetime
    updated_at: datetime

class AlertCreateRequest(BaseModel):
    alert_type: str
    severity: str
    title: str
    description: Optional[str] = None
    camera_id: Optional[int] = None
    location: Optional[str] = None
    coordinates: Optional[Dict[str, Any]] = None
    detected_objects: Optional[List[Dict[str, Any]]] = None
    biometric_data: Optional[Dict[str, Any]] = None
    ai_analysis: Optional[Dict[str, Any]] = None
    image_path: Optional[str] = None
    video_path: Optional[str] = None

class AlertUpdateRequest(BaseModel):
    description: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    location: Optional[str] = None

class AlertAcknowledgeRequest(BaseModel):
    notes: Optional[str] = None

class AlertStatisticsResponse(BaseModel):
    total_alerts: int
    by_severity: Dict[str, int]
    by_type: Dict[str, int]
    by_status: Dict[str, int]
    by_camera: Dict[str, int]
    response_times: List[float]
    average_response_time: float
    unresolved_alerts: int
    date_range: Dict[str, str]

@router.get("/", response_model=List[AlertResponse])
async def list_alerts(
    severity: Optional[str] = Query(None),
    alert_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    camera_id: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    alert_service: AlertService = Depends(lambda: AlertService())
):
    """List alerts with optional filtering"""
    try:
        if status == "active":
            alerts = await alert_service.get_active_alerts(
                severity=severity,
                alert_type=alert_type,
                camera_id=camera_id,
                limit=limit
            )
        else:
            # This would typically fetch from database with filters
            alerts = await alert_service.get_active_alerts(limit=limit)
        
        return [AlertResponse(**alert.__dict__) for alert in alerts]
    
    except Exception as e:
        logger.error(f"List alerts error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list alerts"
        )

@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    current_user: dict = Depends(get_current_user),
    alert_service: AlertService = Depends(lambda: AlertService())
):
    """Get alert by ID"""
    try:
        alert = await alert_service.get_alert_by_id(alert_id)
        
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        return AlertResponse(**alert.__dict__)
    
    except Exception as e:
        logger.error(f"Get alert error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get alert"
        )

@router.post("/", response_model=AlertResponse)
async def create_alert(
    request: AlertCreateRequest,
    current_user: dict = Depends(get_current_user),
    alert_service: AlertService = Depends(lambda: AlertService())
):
    """Create a new alert"""
    try:
        # Check permissions
        if not current_user.get("is_admin") and not current_user.get("is_security_officer"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        alert = await alert_service.create_alert(**request.dict())
        
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Alert creation failed (possibly in cooldown)"
            )
        
        return AlertResponse(**alert.__dict__)
    
    except Exception as e:
        logger.error(f"Create alert error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create alert"
        )

@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: int,
    request: AlertUpdateRequest,
    current_user: dict = Depends(get_current_user),
    alert_service: AlertService = Depends(lambda: AlertService())
):
    """Update alert"""
    try:
        # Check permissions
        if not current_user.get("is_admin") and not current_user.get("is_security_officer"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        success = await alert_service.update_alert(alert_id, **request.dict(exclude_none=True))
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        alert = await alert_service.get_alert_by_id(alert_id)
        return AlertResponse(**alert.__dict__)
    
    except Exception as e:
        logger.error(f"Update alert error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update alert"
        )

@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: int,
    request: AlertAcknowledgeRequest,
    current_user: dict = Depends(get_current_user),
    alert_service: AlertService = Depends(lambda: AlertService())
):
    """Acknowledge an alert"""
    try:
        success = await alert_service.acknowledge_alert(alert_id, current_user["user_id"])
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        return {"message": "Alert acknowledged successfully"}
    
    except Exception as e:
        logger.error(f"Acknowledge alert error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to acknowledge alert"
        )

@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: int,
    request: AlertAcknowledgeRequest,
    current_user: dict = Depends(get_current_user),
    alert_service: AlertService = Depends(lambda: AlertService())
):
    """Resolve an alert"""
    try:
        success = await alert_service.resolve_alert(alert_id, current_user["user_id"])
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        return {"message": "Alert resolved successfully"}
    
    except Exception as e:
        logger.error(f"Resolve alert error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resolve alert"
        )

@router.get("/statistics/overview", response_model=AlertStatisticsResponse)
async def get_alert_statistics(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: dict = Depends(get_current_user),
    alert_service: AlertService = Depends(lambda: AlertService())
):
    """Get alert statistics"""
    try:
        stats = await alert_service.get_alert_statistics(start_date, end_date)
        return AlertStatisticsResponse(**stats)
    
    except Exception as e:
        logger.error(f"Get alert statistics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get alert statistics"
        )

@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: int,
    current_user: dict = Depends(get_current_user),
    alert_service: AlertService = Depends(lambda: AlertService())
):
    """Delete an alert (admin only)"""
    try:
        # Check permissions
        if not current_user.get("is_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # This would typically delete from database
        # For now, just return success
        return {"message": "Alert deleted successfully"}
    
    except Exception as e:
        logger.error(f"Delete alert error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete alert"
        )

@router.post("/test")
async def create_test_alert(
    current_user: dict = Depends(get_current_user),
    alert_service: AlertService = Depends(lambda: AlertService())
):
    """Create a test alert"""
    try:
        # Check permissions
        if not current_user.get("is_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        alert = await alert_service.create_alert(
            alert_type="test",
            severity="low",
            title="Test Alert",
            description="This is a test alert created via API",
            location="Test Location"
        )
        
        if not alert:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Test alert creation failed"
            )
        
        return AlertResponse(**alert.__dict__)
    
    except Exception as e:
        logger.error(f"Create test alert error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create test alert"
        )