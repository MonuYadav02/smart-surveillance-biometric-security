"""
Biometric Service for Authentication and Identification
"""

import asyncio
import logging
import cv2
import numpy as np
import face_recognition
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json

from app.core.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)

class BiometricService:
    """Biometric service for authentication and identification"""
    
    def __init__(self):
        self.face_encodings_cache: Dict[int, np.ndarray] = {}
        self.fingerprint_templates_cache: Dict[int, str] = {}
        self.iris_templates_cache: Dict[int, str] = {}
        
    async def initialize(self):
        """Initialize biometric service"""
        logger.info("Initializing Biometric Service...")
        await self._load_biometric_templates()
        logger.info("Biometric Service initialized successfully")
    
    async def cleanup(self):
        """Cleanup biometric service"""
        logger.info("Cleaning up Biometric Service...")
        self.face_encodings_cache.clear()
        self.fingerprint_templates_cache.clear()
        self.iris_templates_cache.clear()
        logger.info("Biometric Service cleanup complete")
    
    async def _load_biometric_templates(self):
        """Load biometric templates from database"""
        try:
            # This would typically load from database
            # For now, we'll simulate loading
            logger.info("Loading biometric templates...")
            
            # In a real implementation, you would:
            # 1. Query database for all users with biometric data
            # 2. Load face encodings, fingerprint templates, iris templates
            # 3. Cache them for fast lookup
            
            logger.info("Biometric templates loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading biometric templates: {e}")
            raise
    
    async def register_face(self, user_id: int, image: np.ndarray) -> Dict:
        """Register face for a user"""
        try:
            # Detect faces in image
            face_locations = face_recognition.face_locations(image)
            
            if not face_locations:
                return {"success": False, "error": "No face detected in image"}
            
            if len(face_locations) > 1:
                return {"success": False, "error": "Multiple faces detected. Please provide image with single face"}
            
            # Extract face encoding
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            if not face_encodings:
                return {"success": False, "error": "Could not extract face features"}
            
            face_encoding = face_encodings[0]
            
            # Store in cache
            self.face_encodings_cache[user_id] = face_encoding
            
            # Convert to JSON serializable format for database storage
            face_encoding_list = face_encoding.tolist()
            
            logger.info(f"Face registered successfully for user {user_id}")
            
            return {
                "success": True,
                "face_encoding": face_encoding_list,
                "confidence": 1.0
            }
            
        except Exception as e:
            logger.error(f"Error registering face for user {user_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def authenticate_face(self, image: np.ndarray, user_id: Optional[int] = None) -> Dict:
        """Authenticate user by face recognition"""
        try:
            # Detect faces in image
            face_locations = face_recognition.face_locations(image)
            
            if not face_locations:
                return {"success": False, "error": "No face detected in image"}
            
            # Extract face encodings
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            if not face_encodings:
                return {"success": False, "error": "Could not extract face features"}
            
            unknown_face_encoding = face_encodings[0]
            
            # If user_id is provided, verify against specific user
            if user_id and user_id in self.face_encodings_cache:
                known_face_encoding = self.face_encodings_cache[user_id]
                
                # Compare faces
                distance = face_recognition.face_distance([known_face_encoding], unknown_face_encoding)[0]
                is_match = distance <= settings.FACE_RECOGNITION_TOLERANCE
                confidence = 1 - distance
                
                return {
                    "success": is_match,
                    "user_id": user_id if is_match else None,
                    "confidence": confidence,
                    "distance": distance
                }
            
            # Otherwise, search through all registered faces
            best_match = None
            best_confidence = 0
            
            for stored_user_id, stored_encoding in self.face_encodings_cache.items():
                distance = face_recognition.face_distance([stored_encoding], unknown_face_encoding)[0]
                confidence = 1 - distance
                
                if distance <= settings.FACE_RECOGNITION_TOLERANCE and confidence > best_confidence:
                    best_match = stored_user_id
                    best_confidence = confidence
            
            if best_match:
                return {
                    "success": True,
                    "user_id": best_match,
                    "confidence": best_confidence,
                    "method": "face_recognition"
                }
            else:
                return {
                    "success": False,
                    "error": "Face not recognized",
                    "confidence": 0
                }
                
        except Exception as e:
            logger.error(f"Error authenticating face: {e}")
            return {"success": False, "error": str(e)}
    
    async def register_fingerprint(self, user_id: int, fingerprint_data: bytes) -> Dict:
        """Register fingerprint for a user"""
        try:
            # In a real implementation, you would:
            # 1. Process fingerprint image
            # 2. Extract minutiae points
            # 3. Create fingerprint template
            # 4. Store template
            
            # For simulation, we'll create a simple hash
            import hashlib
            fingerprint_hash = hashlib.sha256(fingerprint_data).hexdigest()
            
            # Store in cache
            self.fingerprint_templates_cache[user_id] = fingerprint_hash
            
            logger.info(f"Fingerprint registered successfully for user {user_id}")
            
            return {
                "success": True,
                "template": fingerprint_hash,
                "quality": 0.95
            }
            
        except Exception as e:
            logger.error(f"Error registering fingerprint for user {user_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def authenticate_fingerprint(self, fingerprint_data: bytes, user_id: Optional[int] = None) -> Dict:
        """Authenticate user by fingerprint"""
        try:
            # Create hash for comparison
            import hashlib
            fingerprint_hash = hashlib.sha256(fingerprint_data).hexdigest()
            
            # If user_id is provided, verify against specific user
            if user_id and user_id in self.fingerprint_templates_cache:
                stored_hash = self.fingerprint_templates_cache[user_id]
                is_match = fingerprint_hash == stored_hash
                
                return {
                    "success": is_match,
                    "user_id": user_id if is_match else None,
                    "confidence": 1.0 if is_match else 0.0,
                    "method": "fingerprint"
                }
            
            # Otherwise, search through all registered fingerprints
            for stored_user_id, stored_hash in self.fingerprint_templates_cache.items():
                if fingerprint_hash == stored_hash:
                    return {
                        "success": True,
                        "user_id": stored_user_id,
                        "confidence": 1.0,
                        "method": "fingerprint"
                    }
            
            return {
                "success": False,
                "error": "Fingerprint not recognized",
                "confidence": 0.0
            }
            
        except Exception as e:
            logger.error(f"Error authenticating fingerprint: {e}")
            return {"success": False, "error": str(e)}
    
    async def register_iris(self, user_id: int, iris_image: np.ndarray) -> Dict:
        """Register iris for a user"""
        try:
            # In a real implementation, you would:
            # 1. Detect iris in image
            # 2. Extract iris patterns
            # 3. Create iris template
            # 4. Store template
            
            # For simulation, we'll create a simple hash from image
            import hashlib
            iris_hash = hashlib.sha256(iris_image.tobytes()).hexdigest()
            
            # Store in cache
            self.iris_templates_cache[user_id] = iris_hash
            
            logger.info(f"Iris registered successfully for user {user_id}")
            
            return {
                "success": True,
                "template": iris_hash,
                "quality": 0.98
            }
            
        except Exception as e:
            logger.error(f"Error registering iris for user {user_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def authenticate_iris(self, iris_image: np.ndarray, user_id: Optional[int] = None) -> Dict:
        """Authenticate user by iris recognition"""
        try:
            # Create hash for comparison
            import hashlib
            iris_hash = hashlib.sha256(iris_image.tobytes()).hexdigest()
            
            # If user_id is provided, verify against specific user
            if user_id and user_id in self.iris_templates_cache:
                stored_hash = self.iris_templates_cache[user_id]
                is_match = iris_hash == stored_hash
                
                return {
                    "success": is_match,
                    "user_id": user_id if is_match else None,
                    "confidence": 1.0 if is_match else 0.0,
                    "method": "iris"
                }
            
            # Otherwise, search through all registered iris templates
            for stored_user_id, stored_hash in self.iris_templates_cache.items():
                if iris_hash == stored_hash:
                    return {
                        "success": True,
                        "user_id": stored_user_id,
                        "confidence": 1.0,
                        "method": "iris"
                    }
            
            return {
                "success": False,
                "error": "Iris not recognized",
                "confidence": 0.0
            }
            
        except Exception as e:
            logger.error(f"Error authenticating iris: {e}")
            return {"success": False, "error": str(e)}
    
    async def multi_modal_authentication(self, face_image: Optional[np.ndarray] = None, 
                                       fingerprint_data: Optional[bytes] = None,
                                       iris_image: Optional[np.ndarray] = None,
                                       user_id: Optional[int] = None) -> Dict:
        """Multi-modal biometric authentication"""
        try:
            results = []
            total_confidence = 0
            authenticated_user_id = None
            
            # Face authentication
            if face_image is not None:
                face_result = await self.authenticate_face(face_image, user_id)
                results.append(face_result)
                if face_result["success"]:
                    total_confidence += face_result["confidence"]
                    authenticated_user_id = face_result["user_id"]
            
            # Fingerprint authentication
            if fingerprint_data is not None:
                fingerprint_result = await self.authenticate_fingerprint(fingerprint_data, user_id)
                results.append(fingerprint_result)
                if fingerprint_result["success"]:
                    total_confidence += fingerprint_result["confidence"]
                    if authenticated_user_id is None:
                        authenticated_user_id = fingerprint_result["user_id"]
                    elif authenticated_user_id != fingerprint_result["user_id"]:
                        return {
                            "success": False,
                            "error": "Biometric data mismatch between modalities"
                        }
            
            # Iris authentication
            if iris_image is not None and settings.IRIS_RECOGNITION_ENABLED:
                iris_result = await self.authenticate_iris(iris_image, user_id)
                results.append(iris_result)
                if iris_result["success"]:
                    total_confidence += iris_result["confidence"]
                    if authenticated_user_id is None:
                        authenticated_user_id = iris_result["user_id"]
                    elif authenticated_user_id != iris_result["user_id"]:
                        return {
                            "success": False,
                            "error": "Biometric data mismatch between modalities"
                        }
            
            # Calculate final result
            successful_authentications = sum(1 for r in results if r["success"])
            average_confidence = total_confidence / len(results) if results else 0
            
            is_authenticated = (successful_authentications > 0 and 
                              average_confidence >= 0.7 and 
                              authenticated_user_id is not None)
            
            return {
                "success": is_authenticated,
                "user_id": authenticated_user_id,
                "confidence": average_confidence,
                "successful_modalities": successful_authentications,
                "total_modalities": len(results),
                "detailed_results": results
            }
            
        except Exception as e:
            logger.error(f"Error in multi-modal authentication: {e}")
            return {"success": False, "error": str(e)}
    
    async def detect_liveness(self, image: np.ndarray) -> Dict:
        """Detect if the biometric sample is from a live person"""
        try:
            # Simple liveness detection based on image properties
            # In a real implementation, you would use more sophisticated methods
            
            # Check image quality
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            variance = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Check for basic liveness indicators
            is_live = variance > 100  # Threshold for blur detection
            
            return {
                "is_live": is_live,
                "confidence": min(variance / 1000, 1.0),
                "quality_score": variance
            }
            
        except Exception as e:
            logger.error(f"Error detecting liveness: {e}")
            return {"is_live": False, "confidence": 0.0, "error": str(e)}