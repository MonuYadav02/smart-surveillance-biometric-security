"""
Authentication API endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
import cv2
import numpy as np
from datetime import datetime, timedelta
import logging

from app.core.config import settings
from app.services.biometric_service import BiometricService
from app.models.user import User
from app.models.access_log import AccessLog

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)

# Request/Response models
class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class BiometricLoginRequest(BaseModel):
    user_id: Optional[int] = None
    method: str  # face, fingerprint, iris, multi_modal

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    is_active: bool
    is_admin: bool
    is_security_officer: bool
    last_login: Optional[datetime]

# Dependency to get current user
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # This would typically validate JWT token and return user
    # For now, we'll simulate
    return {"user_id": 1, "username": "admin", "is_admin": True}

@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Traditional username/password login"""
    try:
        # This would typically:
        # 1. Validate credentials against database
        # 2. Generate JWT token
        # 3. Log access attempt
        
        # For simulation
        if request.username == "admin" and request.password == "password":
            return TokenResponse(
                access_token="simulated_jwt_token",
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
    
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.post("/biometric/login", response_model=TokenResponse)
async def biometric_login(
    request: BiometricLoginRequest,
    face_image: Optional[UploadFile] = File(None),
    fingerprint_data: Optional[UploadFile] = File(None),
    iris_image: Optional[UploadFile] = File(None),
    biometric_service: BiometricService = Depends(lambda: BiometricService())
):
    """Biometric authentication login"""
    try:
        # Process uploaded files
        face_array = None
        fingerprint_bytes = None
        iris_array = None
        
        if face_image:
            face_data = await face_image.read()
            face_array = cv2.imdecode(np.frombuffer(face_data, np.uint8), cv2.IMREAD_COLOR)
        
        if fingerprint_data:
            fingerprint_bytes = await fingerprint_data.read()
        
        if iris_image:
            iris_data = await iris_image.read()
            iris_array = cv2.imdecode(np.frombuffer(iris_data, np.uint8), cv2.IMREAD_COLOR)
        
        # Perform biometric authentication
        if request.method == "multi_modal":
            auth_result = await biometric_service.multi_modal_authentication(
                face_image=face_array,
                fingerprint_data=fingerprint_bytes,
                iris_image=iris_array,
                user_id=request.user_id
            )
        elif request.method == "face":
            auth_result = await biometric_service.authenticate_face(face_array, request.user_id)
        elif request.method == "fingerprint":
            auth_result = await biometric_service.authenticate_fingerprint(fingerprint_bytes, request.user_id)
        elif request.method == "iris":
            auth_result = await biometric_service.authenticate_iris(iris_array, request.user_id)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid authentication method"
            )
        
        if auth_result["success"]:
            # Generate token and log access
            return TokenResponse(
                access_token=f"biometric_token_{auth_result['user_id']}",
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=auth_result.get("error", "Biometric authentication failed")
            )
    
    except Exception as e:
        logger.error(f"Biometric login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Biometric authentication failed"
        )

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """Logout user"""
    try:
        # This would typically:
        # 1. Invalidate JWT token
        # 2. Log logout event
        
        return {"message": "Logged out successfully"}
    
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    try:
        # This would typically fetch user from database
        # For simulation
        return UserResponse(
            id=current_user["user_id"],
            username=current_user["username"],
            email="admin@example.com",
            full_name="System Administrator",
            is_active=True,
            is_admin=current_user.get("is_admin", False),
            is_security_officer=True,
            last_login=datetime.utcnow()
        )
    
    except Exception as e:
        logger.error(f"Get user info error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )

@router.post("/biometric/register")
async def register_biometric(
    method: str,
    user_id: int,
    face_image: Optional[UploadFile] = File(None),
    fingerprint_data: Optional[UploadFile] = File(None),
    iris_image: Optional[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user),
    biometric_service: BiometricService = Depends(lambda: BiometricService())
):
    """Register biometric data for a user"""
    try:
        # Check permissions
        if not current_user.get("is_admin") and current_user["user_id"] != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        result = {}
        
        if method == "face" and face_image:
            face_data = await face_image.read()
            face_array = cv2.imdecode(np.frombuffer(face_data, np.uint8), cv2.IMREAD_COLOR)
            result = await biometric_service.register_face(user_id, face_array)
        
        elif method == "fingerprint" and fingerprint_data:
            fingerprint_bytes = await fingerprint_data.read()
            result = await biometric_service.register_fingerprint(user_id, fingerprint_bytes)
        
        elif method == "iris" and iris_image:
            iris_data = await iris_image.read()
            iris_array = cv2.imdecode(np.frombuffer(iris_data, np.uint8), cv2.IMREAD_COLOR)
            result = await biometric_service.register_iris(user_id, iris_array)
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid method or missing biometric data"
            )
        
        if result["success"]:
            return {"message": f"Biometric {method} registered successfully", "result": result}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Biometric registration failed")
            )
    
    except Exception as e:
        logger.error(f"Biometric registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Biometric registration failed"
        )