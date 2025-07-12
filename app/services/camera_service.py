"""
Camera Service for Surveillance System Management
"""

import asyncio
import logging
import cv2
import numpy as np
from typing import List, Dict, Optional, AsyncGenerator
from datetime import datetime
import aiofiles

from app.core.config import settings
from app.models.camera import Camera
from app.models.recording import Recording
from app.services.ai_service import AIService

logger = logging.getLogger(__name__)

class CameraService:
    """Camera service for managing surveillance cameras"""
    
    def __init__(self):
        self.cameras: Dict[int, cv2.VideoCapture] = {}
        self.recording_tasks: Dict[int, asyncio.Task] = {}
        self.ai_service = None
        self.motion_detectors: Dict[int, cv2.BackgroundSubtractorMOG2] = {}
        
    async def initialize(self):
        """Initialize camera service"""
        logger.info("Initializing Camera Service...")
        self.ai_service = AIService()
        await self.ai_service.initialize()
        logger.info("Camera Service initialized successfully")
    
    async def cleanup(self):
        """Cleanup camera service"""
        logger.info("Cleaning up Camera Service...")
        
        # Stop all recording tasks
        for task in self.recording_tasks.values():
            if not task.done():
                task.cancel()
        
        # Release all cameras
        for camera in self.cameras.values():
            if camera.isOpened():
                camera.release()
        
        self.cameras.clear()
        self.recording_tasks.clear()
        self.motion_detectors.clear()
        
        logger.info("Camera Service cleanup complete")
    
    async def add_camera(self, camera_data: Dict) -> Camera:
        """Add a new camera to the system"""
        try:
            # Test camera connection
            cap = cv2.VideoCapture(f"rtsp://{camera_data['ip_address']}:{camera_data['port']}")
            if not cap.isOpened():
                raise Exception(f"Cannot connect to camera at {camera_data['ip_address']}")
            
            # Create camera record
            camera = Camera(**camera_data)
            camera.is_online = True
            camera.last_heartbeat = datetime.utcnow()
            
            # Store camera connection
            self.cameras[camera.id] = cap
            
            # Initialize motion detector
            self.motion_detectors[camera.id] = cv2.createBackgroundSubtractorMOG2(
                detectShadows=True
            )
            
            # Start monitoring task
            if camera.motion_detection_enabled:
                task = asyncio.create_task(self._monitor_camera(camera.id))
                self.recording_tasks[camera.id] = task
            
            logger.info(f"Camera {camera.name} added successfully")
            return camera
            
        except Exception as e:
            logger.error(f"Error adding camera: {e}")
            raise
    
    async def remove_camera(self, camera_id: int):
        """Remove a camera from the system"""
        try:
            # Stop monitoring task
            if camera_id in self.recording_tasks:
                self.recording_tasks[camera_id].cancel()
                del self.recording_tasks[camera_id]
            
            # Release camera
            if camera_id in self.cameras:
                self.cameras[camera_id].release()
                del self.cameras[camera_id]
            
            # Remove motion detector
            if camera_id in self.motion_detectors:
                del self.motion_detectors[camera_id]
            
            logger.info(f"Camera {camera_id} removed successfully")
            
        except Exception as e:
            logger.error(f"Error removing camera {camera_id}: {e}")
            raise
    
    async def _monitor_camera(self, camera_id: int):
        """Monitor camera for motion and events"""
        logger.info(f"Starting monitoring for camera {camera_id}")
        
        try:
            cap = self.cameras[camera_id]
            motion_detector = self.motion_detectors[camera_id]
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    logger.warning(f"Cannot read frame from camera {camera_id}")
                    await asyncio.sleep(1)
                    continue
                
                # Motion detection
                if await self._detect_motion(frame, motion_detector):
                    logger.info(f"Motion detected on camera {camera_id}")
                    await self._handle_motion_event(camera_id, frame)
                
                # Night vision adjustment
                if await self._is_night_vision_needed(frame):
                    frame = await self._apply_night_vision(frame)
                
                # AI analysis
                if self.ai_service:
                    analysis = await self.ai_service.analyze_frame(frame)
                    if analysis.get("emergency_detected"):
                        await self._handle_emergency_event(camera_id, frame, analysis)
                
                await asyncio.sleep(1 / settings.CAMERA_FPS)
                
        except asyncio.CancelledError:
            logger.info(f"Monitoring cancelled for camera {camera_id}")
        except Exception as e:
            logger.error(f"Error monitoring camera {camera_id}: {e}")
    
    async def _detect_motion(self, frame: np.ndarray, motion_detector: cv2.BackgroundSubtractorMOG2) -> bool:
        """Detect motion in frame"""
        try:
            # Apply background subtraction
            fg_mask = motion_detector.apply(frame)
            
            # Calculate motion percentage
            motion_pixels = cv2.countNonZero(fg_mask)
            total_pixels = fg_mask.shape[0] * fg_mask.shape[1]
            motion_percentage = motion_pixels / total_pixels
            
            return motion_percentage > settings.MOTION_DETECTION_SENSITIVITY
            
        except Exception as e:
            logger.error(f"Error detecting motion: {e}")
            return False
    
    async def _is_night_vision_needed(self, frame: np.ndarray) -> bool:
        """Check if night vision is needed"""
        try:
            # Calculate average brightness
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            brightness = np.mean(gray) / 255.0
            
            return brightness < settings.NIGHT_VISION_THRESHOLD
            
        except Exception as e:
            logger.error(f"Error checking brightness: {e}")
            return False
    
    async def _apply_night_vision(self, frame: np.ndarray) -> np.ndarray:
        """Apply night vision enhancement"""
        try:
            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            
            # Convert back to BGR
            enhanced_bgr = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
            
            return enhanced_bgr
            
        except Exception as e:
            logger.error(f"Error applying night vision: {e}")
            return frame
    
    async def _handle_motion_event(self, camera_id: int, frame: np.ndarray):
        """Handle motion detection event"""
        try:
            # Save frame
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"motion_{camera_id}_{timestamp}.jpg"
            filepath = f"{settings.STORAGE_PATH}/motion/{filename}"
            
            cv2.imwrite(filepath, frame)
            
            # Create alert
            from app.services.alert_service import AlertService
            alert_service = AlertService()
            await alert_service.create_alert(
                alert_type="motion",
                severity="medium",
                title=f"Motion detected on camera {camera_id}",
                camera_id=camera_id,
                image_path=filepath
            )
            
        except Exception as e:
            logger.error(f"Error handling motion event: {e}")
    
    async def _handle_emergency_event(self, camera_id: int, frame: np.ndarray, analysis: Dict):
        """Handle emergency detection event"""
        try:
            # Save frame
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"emergency_{camera_id}_{timestamp}.jpg"
            filepath = f"{settings.STORAGE_PATH}/emergency/{filename}"
            
            cv2.imwrite(filepath, frame)
            
            # Create critical alert
            from app.services.alert_service import AlertService
            alert_service = AlertService()
            await alert_service.create_alert(
                alert_type="emergency",
                severity="critical",
                title=f"Emergency detected on camera {camera_id}",
                description=f"AI Analysis: {analysis.get('description', 'Unknown emergency')}",
                camera_id=camera_id,
                image_path=filepath,
                ai_analysis=analysis
            )
            
        except Exception as e:
            logger.error(f"Error handling emergency event: {e}")
    
    async def start_recording(self, camera_id: int, duration: int = None) -> Recording:
        """Start recording from camera"""
        try:
            if camera_id not in self.cameras:
                raise Exception(f"Camera {camera_id} not found")
            
            cap = self.cameras[camera_id]
            duration = duration or settings.RECORDING_DURATION
            
            # Create recording file
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{camera_id}_{timestamp}.mp4"
            filepath = f"{settings.STORAGE_PATH}/recordings/{filename}"
            
            # Setup video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(
                filepath,
                fourcc,
                settings.CAMERA_FPS,
                (settings.CAMERA_RESOLUTION_WIDTH, settings.CAMERA_RESOLUTION_HEIGHT)
            )
            
            start_time = datetime.utcnow()
            frames_written = 0
            
            # Record for specified duration
            while frames_written < (duration * settings.CAMERA_FPS):
                ret, frame = cap.read()
                if ret:
                    out.write(frame)
                    frames_written += 1
                await asyncio.sleep(1 / settings.CAMERA_FPS)
            
            out.release()
            end_time = datetime.utcnow()
            
            # Create recording record
            recording = Recording(
                filename=filename,
                file_path=filepath,
                file_size=0,  # Will be calculated
                camera_id=camera_id,
                duration=duration,
                start_time=start_time,
                end_time=end_time,
                resolution=f"{settings.CAMERA_RESOLUTION_WIDTH}x{settings.CAMERA_RESOLUTION_HEIGHT}",
                fps=settings.CAMERA_FPS,
                triggered_by="manual"
            )
            
            logger.info(f"Recording completed for camera {camera_id}")
            return recording
            
        except Exception as e:
            logger.error(f"Error starting recording: {e}")
            raise
    
    async def get_camera_stream(self, camera_id: int) -> AsyncGenerator[bytes, None]:
        """Get live stream from camera"""
        try:
            if camera_id not in self.cameras:
                raise Exception(f"Camera {camera_id} not found")
            
            cap = self.cameras[camera_id]
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Encode frame as JPEG
                _, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
                await asyncio.sleep(1 / settings.CAMERA_FPS)
                
        except Exception as e:
            logger.error(f"Error streaming camera {camera_id}: {e}")
    
    async def get_camera_status(self, camera_id: int) -> Dict:
        """Get camera status"""
        try:
            if camera_id not in self.cameras:
                return {"status": "offline", "error": "Camera not found"}
            
            cap = self.cameras[camera_id]
            is_online = cap.isOpened()
            
            return {
                "status": "online" if is_online else "offline",
                "fps": cap.get(cv2.CAP_PROP_FPS),
                "width": cap.get(cv2.CAP_PROP_FRAME_WIDTH),
                "height": cap.get(cv2.CAP_PROP_FRAME_HEIGHT),
                "last_check": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting camera status: {e}")
            return {"status": "error", "error": str(e)}