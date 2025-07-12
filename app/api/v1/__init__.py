"""
API v1 Package - Version 1 REST API endpoints
"""

from fastapi import APIRouter

from .auth import router as auth_router
from .cameras import router as cameras_router
from .alerts import router as alerts_router
from .biometric import router as biometric_router
from .surveillance import router as surveillance_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router.include_router(cameras_router, prefix="/cameras", tags=["cameras"])
api_router.include_router(alerts_router, prefix="/alerts", tags=["alerts"])
api_router.include_router(biometric_router, prefix="/biometric", tags=["biometric"])
api_router.include_router(surveillance_router, prefix="/surveillance", tags=["surveillance"])