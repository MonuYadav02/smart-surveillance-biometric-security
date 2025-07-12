"""
Biometric Management API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import cv2
import numpy as np
import logging

from app.core.config import settings
from app.services.biometric_service import BiometricService
from app.api.v1.auth import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

# Request/Response models
class BiometricRegistrationResponse(BaseModel):
    success: bool
    message: str
    template_id: Optional[str] = None
    quality_score: Optional[float] = None
    error: Optional[str] = None

class BiometricAuthenticationResponse(BaseModel):
    success: bool
    user_id: Optional[int] = None
    confidence: float
    method: str
    error: Optional[str] = None
    detailed_results: Optional[List[Dict[str, Any]]] = None

class LivenessCheckResponse(BaseModel):
    is_live: bool
    confidence: float
    quality_score: float
    error: Optional[str] = None

class BiometricTestRequest(BaseModel):
    user_id: int
    method: str  # face, fingerprint, iris, multi_modal

@router.post("/register/face", response_model=BiometricRegistrationResponse)
async def register_face(
    user_id: int,
    face_image: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    biometric_service: BiometricService = Depends(lambda: BiometricService())
):
    """Register face biometric for a user"""
    try:
        # Check permissions
        if not current_user.get("is_admin") and current_user["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Validate file type
        if not face_image.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Please upload an image."
            )
        
        # Read and process image
        image_data = await face_image.read()
        image_array = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
        
        if image_array is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image format"
            )
        
        # Perform liveness check
        liveness_result = await biometric_service.detect_liveness(image_array)
        if not liveness_result["is_live"]:
            return BiometricRegistrationResponse(
                success=False,
                message="Liveness check failed",
                error="Please provide a live image"
            )
        
        # Register face
        result = await biometric_service.register_face(user_id, image_array)
        
        return BiometricRegistrationResponse(
            success=result["success"],
            message="Face registered successfully" if result["success"] else "Face registration failed",
            template_id=str(user_id) if result["success"] else None,
            quality_score=liveness_result["quality_score"],
            error=result.get("error")
        )
    
    except Exception as e:
        logger.error(f"Register face error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Face registration failed"
        )

@router.post("/register/fingerprint", response_model=BiometricRegistrationResponse)
async def register_fingerprint(
    user_id: int,
    fingerprint_image: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    biometric_service: BiometricService = Depends(lambda: BiometricService())
):
    """Register fingerprint biometric for a user"""
    try:
        # Check permissions
        if not current_user.get("is_admin") and current_user["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Read fingerprint data
        fingerprint_data = await fingerprint_image.read()
        
        # Register fingerprint
        result = await biometric_service.register_fingerprint(user_id, fingerprint_data)
        
        return BiometricRegistrationResponse(
            success=result["success"],
            message="Fingerprint registered successfully" if result["success"] else "Fingerprint registration failed",
            template_id=str(user_id) if result["success"] else None,
            quality_score=result.get("quality", 0.0),
            error=result.get("error")
        )
    
    except Exception as e:
        logger.error(f"Register fingerprint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fingerprint registration failed"
        )

@router.post("/register/iris", response_model=BiometricRegistrationResponse)
async def register_iris(
    user_id: int,
    iris_image: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    biometric_service: BiometricService = Depends(lambda: BiometricService())
):
    """Register iris biometric for a user"""
    try:
        # Check permissions
        if not current_user.get("is_admin") and current_user["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        # Validate file type
        if not iris_image.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Please upload an image."
            )
        
        # Read and process image
        image_data = await iris_image.read()
        image_array = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
        
        if image_array is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image format"
            )
        
        # Register iris
        result = await biometric_service.register_iris(user_id, image_array)
        
        return BiometricRegistrationResponse(
            success=result["success"],
            message="Iris registered successfully" if result["success"] else "Iris registration failed",
            template_id=str(user_id) if result["success"] else None,
            quality_score=result.get("quality", 0.0),
            error=result.get("error")
        )
    
    except Exception as e:
        logger.error(f"Register iris error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Iris registration failed"
        )

@router.post("/authenticate/face", response_model=BiometricAuthenticationResponse)
async def authenticate_face(
    face_image: UploadFile = File(...),
    user_id: Optional[int] = None,
    biometric_service: BiometricService = Depends(lambda: BiometricService())
):
    """Authenticate user by face recognition"""
    try:
        # Validate file type
        if not face_image.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Please upload an image."
            )
        
        # Read and process image
        image_data = await face_image.read()
        image_array = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
        
        if image_array is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image format"
            )
        
        # Perform liveness check
        liveness_result = await biometric_service.detect_liveness(image_array)
        if not liveness_result["is_live"]:
            return BiometricAuthenticationResponse(
                success=False,
                confidence=0.0,
                method="face",
                error="Liveness check failed"
            )
        
        # Authenticate face
        result = await biometric_service.authenticate_face(image_array, user_id)
        
        return BiometricAuthenticationResponse(
            success=result["success"],
            user_id=result.get("user_id"),
            confidence=result.get("confidence", 0.0),
            method="face",
            error=result.get("error")
        )
    
    except Exception as e:
        logger.error(f"Authenticate face error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Face authentication failed"
        )

@router.post("/authenticate/fingerprint", response_model=BiometricAuthenticationResponse)
async def authenticate_fingerprint(
    fingerprint_image: UploadFile = File(...),
    user_id: Optional[int] = None,
    biometric_service: BiometricService = Depends(lambda: BiometricService())
):
    """Authenticate user by fingerprint"""
    try:
        # Read fingerprint data
        fingerprint_data = await fingerprint_image.read()
        
        # Authenticate fingerprint
        result = await biometric_service.authenticate_fingerprint(fingerprint_data, user_id)
        
        return BiometricAuthenticationResponse(
            success=result["success"],
            user_id=result.get("user_id"),
            confidence=result.get("confidence", 0.0),
            method="fingerprint",
            error=result.get("error")
        )
    
    except Exception as e:
        logger.error(f"Authenticate fingerprint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fingerprint authentication failed"
        )

@router.post("/authenticate/iris", response_model=BiometricAuthenticationResponse)
async def authenticate_iris(
    iris_image: UploadFile = File(...),
    user_id: Optional[int] = None,
    biometric_service: BiometricService = Depends(lambda: BiometricService())
):
    """Authenticate user by iris recognition"""
    try:
        # Validate file type
        if not iris_image.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Please upload an image."
            )
        
        # Read and process image
        image_data = await iris_image.read()
        image_array = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
        
        if image_array is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image format"
            )
        
        # Authenticate iris
        result = await biometric_service.authenticate_iris(image_array, user_id)
        
        return BiometricAuthenticationResponse(
            success=result["success"],
            user_id=result.get("user_id"),
            confidence=result.get("confidence", 0.0),
            method="iris",
            error=result.get("error")
        )
    
    except Exception as e:
        logger.error(f"Authenticate iris error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Iris authentication failed"
        )

@router.post("/authenticate/multi-modal", response_model=BiometricAuthenticationResponse)
async def authenticate_multi_modal(
    face_image: Optional[UploadFile] = File(None),
    fingerprint_image: Optional[UploadFile] = File(None),
    iris_image: Optional[UploadFile] = File(None),
    user_id: Optional[int] = None,
    biometric_service: BiometricService = Depends(lambda: BiometricService())
):
    """Multi-modal biometric authentication"""
    try:
        # Process uploaded files
        face_array = None
        fingerprint_bytes = None
        iris_array = None
        
        if face_image:
            face_data = await face_image.read()
            face_array = cv2.imdecode(np.frombuffer(face_data, np.uint8), cv2.IMREAD_COLOR)
        
        if fingerprint_image:
            fingerprint_bytes = await fingerprint_image.read()
        
        if iris_image:
            iris_data = await iris_image.read()
            iris_array = cv2.imdecode(np.frombuffer(iris_data, np.uint8), cv2.IMREAD_COLOR)
        
        # Perform multi-modal authentication
        result = await biometric_service.multi_modal_authentication(
            face_image=face_array,
            fingerprint_data=fingerprint_bytes,
            iris_image=iris_array,
            user_id=user_id
        )
        
        return BiometricAuthenticationResponse(
            success=result["success"],
            user_id=result.get("user_id"),
            confidence=result.get("confidence", 0.0),
            method="multi_modal",
            error=result.get("error"),
            detailed_results=result.get("detailed_results")
        )
    
    except Exception as e:
        logger.error(f"Multi-modal authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Multi-modal authentication failed"
        )

@router.post("/liveness-check", response_model=LivenessCheckResponse)
async def check_liveness(
    image: UploadFile = File(...),
    biometric_service: BiometricService = Depends(lambda: BiometricService())
):
    """Check if biometric sample is from a live person"""
    try:
        # Validate file type
        if not image.content_type.startswith("image/"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Please upload an image."
            )
        
        # Read and process image
        image_data = await image.read()
        image_array = cv2.imdecode(np.frombuffer(image_data, np.uint8), cv2.IMREAD_COLOR)
        
        if image_array is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image format"
            )
        
        # Perform liveness check
        result = await biometric_service.detect_liveness(image_array)
        
        return LivenessCheckResponse(
            is_live=result["is_live"],
            confidence=result["confidence"],
            quality_score=result["quality_score"],
            error=result.get("error")
        )
    
    except Exception as e:
        logger.error(f"Liveness check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Liveness check failed"
        )

@router.get("/status")
async def get_biometric_status(
    current_user: dict = Depends(get_current_user),
    biometric_service: BiometricService = Depends(lambda: BiometricService())
):
    """Get biometric system status"""
    try:
        return {
            "status": "operational",
            "face_recognition_enabled": True,
            "fingerprint_enabled": True,
            "iris_recognition_enabled": settings.IRIS_RECOGNITION_ENABLED,
            "liveness_detection_enabled": True,
            "multi_modal_enabled": True,
            "registered_users": len(biometric_service.face_encodings_cache),
            "last_check": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        logger.error(f"Get biometric status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get biometric status"
        )