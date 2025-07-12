"""
Configuration Management for Smart Surveillance System
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, validator
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    PROJECT_NAME: str = "Smart Surveillance System"
    VERSION: str = "1.0.0"
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # API
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/surveillance_db")
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Camera Configuration
    CAMERA_RESOLUTION_WIDTH: int = 1920
    CAMERA_RESOLUTION_HEIGHT: int = 1080
    CAMERA_FPS: int = 30
    NIGHT_VISION_THRESHOLD: float = 0.3
    MOTION_DETECTION_SENSITIVITY: float = 0.5
    
    # Biometric Configuration
    FACE_RECOGNITION_TOLERANCE: float = 0.6
    FINGERPRINT_THRESHOLD: float = 0.8
    IRIS_RECOGNITION_ENABLED: bool = True
    BIOMETRIC_TIMEOUT: int = 30
    
    # AI Configuration
    AI_MODEL_PATH: str = os.getenv("AI_MODEL_PATH", "models/")
    EMERGENCY_DETECTION_THRESHOLD: float = 0.7
    VIOLENCE_DETECTION_ENABLED: bool = True
    ANOMALY_DETECTION_ENABLED: bool = True
    
    # Surveillance Configuration
    RECORDING_ENABLED: bool = True
    RECORDING_DURATION: int = 300  # 5 minutes
    ALERT_COOLDOWN: int = 60  # 1 minute
    
    # Notification Configuration
    EMAIL_ENABLED: bool = os.getenv("EMAIL_ENABLED", "False").lower() == "true"
    SMS_ENABLED: bool = os.getenv("SMS_ENABLED", "False").lower() == "true"
    WEBHOOK_URL: Optional[str] = os.getenv("WEBHOOK_URL")
    
    # Storage Configuration
    STORAGE_PATH: str = os.getenv("STORAGE_PATH", "storage/")
    MAX_STORAGE_SIZE: int = 10 * 1024 * 1024 * 1024  # 10GB
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "surveillance.log")
    
    @validator("ALLOWED_HOSTS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    class Config:
        case_sensitive = True
        env_file = ".env"

# Global settings instance
settings = Settings()