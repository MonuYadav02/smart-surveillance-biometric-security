"""
Camera Management API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import logging

from app.core.config import settings
from app.services.camera_service import CameraService
from app.models.camera import Camera
from app.api.v1.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

# Request/Response models
class CameraCreateRequest(BaseModel):
    name: str
    location: str
    description: Optional[str] = None
    ip_address: str
    port: int = 8080
    username: Optional[str] = None
    password: Optional[str] = None
    has_night_vision: bool = True
    has_360_degree: bool = False
    has_ptz: bool = False
    has_audio: bool = False
    resolution_width: int = 1920
    resolution_height: int = 1080
    fps: int = 30
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    altitude: Optional[float] = None
    orientation: Optional[float] = None
    motion_detection_enabled: bool = True
    face_recognition_enabled: bool = True
    alert_on_motion: bool = True

class CameraUpdateRequest(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    motion_detection_enabled: Optional[bool] = None
    face_recognition_enabled: Optional[bool] = None
    alert_on_motion: Optional[bool] = None

class CameraResponse(BaseModel):
    id: int
    name: str
    location: str
    description: Optional[str]
    ip_address: str
    port: int
    has_night_vision: bool
    has_360_degree: bool
    has_ptz: bool
    has_audio: bool
    resolution_width: int
    resolution_height: int
    fps: int
    latitude: Optional[float]
    longitude: Optional[float]
    altitude: Optional[float]
    orientation: Optional[float]
    is_active: bool
    is_recording: bool
    is_online: bool
    last_heartbeat: Optional[datetime]
    motion_detection_enabled: bool
    face_recognition_enabled: bool
    alert_on_motion: bool
    created_at: datetime
    updated_at: datetime

class RecordingRequest(BaseModel):
    duration: Optional[int] = None  # seconds

@router.post("/", response_model=CameraResponse)
async def create_camera(
    request: CameraCreateRequest,
    current_user: dict = Depends(get_current_user),
    camera_service: CameraService = Depends(lambda: CameraService())
):
    """Create a new camera"""
    try:
        # Check permissions
        if not current_user.get("is_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        camera_data = request.dict()
        camera = await camera_service.add_camera(camera_data)
        
        return CameraResponse(**camera.__dict__)
    
    except Exception as e:
        logger.error(f"Create camera error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create camera"
        )

@router.get("/", response_model=List[CameraResponse])
async def list_cameras(
    current_user: dict = Depends(get_current_user)
):
    """List all cameras"""
    try:
        # This would typically fetch from database
        # For simulation, return empty list
        return []
    
    except Exception as e:
        logger.error(f"List cameras error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list cameras"
        )

@router.get("/{camera_id}", response_model=CameraResponse)
async def get_camera(
    camera_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get camera by ID"""
    try:
        # This would typically fetch from database
        # For simulation, return mock data
        return CameraResponse(
            id=camera_id,
            name=f"Camera {camera_id}",
            location="Test Location",
            description="Test Camera",
            ip_address="192.168.1.100",
            port=8080,
            has_night_vision=True,
            has_360_degree=False,
            has_ptz=False,
            has_audio=False,
            resolution_width=1920,
            resolution_height=1080,
            fps=30,
            latitude=None,
            longitude=None,
            altitude=None,
            orientation=None,
            is_active=True,
            is_recording=False,
            is_online=True,
            last_heartbeat=datetime.utcnow(),
            motion_detection_enabled=True,
            face_recognition_enabled=True,
            alert_on_motion=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    except Exception as e:
        logger.error(f"Get camera error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get camera"
        )

@router.put("/{camera_id}", response_model=CameraResponse)
async def update_camera(
    camera_id: int,
    request: CameraUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update camera settings"""
    try:
        # Check permissions
        if not current_user.get("is_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # This would typically update database
        # For simulation, return updated data
        return CameraResponse(
            id=camera_id,
            name=request.name or f"Camera {camera_id}",
            location=request.location or "Updated Location",
            description=request.description,
            ip_address="192.168.1.100",
            port=8080,
            has_night_vision=True,
            has_360_degree=False,
            has_ptz=False,
            has_audio=False,
            resolution_width=1920,
            resolution_height=1080,
            fps=30,
            latitude=None,
            longitude=None,
            altitude=None,
            orientation=None,
            is_active=request.is_active if request.is_active is not None else True,
            is_recording=False,
            is_online=True,
            last_heartbeat=datetime.utcnow(),
            motion_detection_enabled=request.motion_detection_enabled if request.motion_detection_enabled is not None else True,
            face_recognition_enabled=request.face_recognition_enabled if request.face_recognition_enabled is not None else True,
            alert_on_motion=request.alert_on_motion if request.alert_on_motion is not None else True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    except Exception as e:
        logger.error(f"Update camera error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update camera"
        )

@router.delete("/{camera_id}")
async def delete_camera(
    camera_id: int,
    current_user: dict = Depends(get_current_user),
    camera_service: CameraService = Depends(lambda: CameraService())
):
    """Delete camera"""
    try:
        # Check permissions
        if not current_user.get("is_admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        await camera_service.remove_camera(camera_id)
        return {"message": "Camera deleted successfully"}
    
    except Exception as e:
        logger.error(f"Delete camera error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete camera"
        )

@router.get("/{camera_id}/stream")
async def stream_camera(
    camera_id: int,
    current_user: dict = Depends(get_current_user),
    camera_service: CameraService = Depends(lambda: CameraService())
):
    """Stream live video from camera"""
    try:
        return StreamingResponse(
            camera_service.get_camera_stream(camera_id),
            media_type="multipart/x-mixed-replace; boundary=frame"
        )
    
    except Exception as e:
        logger.error(f"Stream camera error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stream camera"
        )

@router.get("/{camera_id}/status")
async def get_camera_status(
    camera_id: int,
    current_user: dict = Depends(get_current_user),
    camera_service: CameraService = Depends(lambda: CameraService())
):
    """Get camera status"""
    try:
        status_info = await camera_service.get_camera_status(camera_id)
        return status_info
    
    except Exception as e:
        logger.error(f"Get camera status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get camera status"
        )

@router.post("/{camera_id}/record")
async def start_recording(
    camera_id: int,
    request: RecordingRequest,
    current_user: dict = Depends(get_current_user),
    camera_service: CameraService = Depends(lambda: CameraService())
):
    """Start recording from camera"""
    try:
        recording = await camera_service.start_recording(camera_id, request.duration)
        return {
            "message": "Recording started",
            "recording_id": recording.id,
            "duration": recording.duration,
            "file_path": recording.file_path
        }
    
    except Exception as e:
        logger.error(f"Start recording error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start recording"
        )

@router.post("/{camera_id}/ptz")
async def control_ptz(
    camera_id: int,
    action: str,  # up, down, left, right, zoom_in, zoom_out, preset_1, etc.
    current_user: dict = Depends(get_current_user)
):
    """Control PTZ camera movements"""
    try:
        # This would typically send PTZ commands to the camera
        # For simulation, just return success
        return {"message": f"PTZ action '{action}' executed successfully"}
    
    except Exception as e:
        logger.error(f"PTZ control error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to control PTZ"
        )