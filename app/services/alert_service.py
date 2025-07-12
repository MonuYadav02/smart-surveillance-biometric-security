"""
Alert Service for Security Notifications and Alert Management
"""

import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

from app.core.config import settings
from app.models.alert import Alert
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

class AlertService:
    """Alert service for managing security alerts and notifications"""
    
    def __init__(self):
        self.notification_service = NotificationService()
        self.alert_cooldowns: Dict[str, datetime] = {}
        self.active_alerts: Dict[int, Alert] = {}
        
    async def initialize(self):
        """Initialize alert service"""
        logger.info("Initializing Alert Service...")
        await self.notification_service.initialize()
        logger.info("Alert Service initialized successfully")
    
    async def cleanup(self):
        """Cleanup alert service"""
        logger.info("Cleaning up Alert Service...")
        await self.notification_service.cleanup()
        self.alert_cooldowns.clear()
        self.active_alerts.clear()
        logger.info("Alert Service cleanup complete")
    
    async def create_alert(self, alert_type: str, severity: str, title: str, 
                          description: str = None, camera_id: int = None,
                          location: str = None, coordinates: Dict = None,
                          detected_objects: List = None, biometric_data: Dict = None,
                          ai_analysis: Dict = None, image_path: str = None,
                          video_path: str = None) -> Alert:
        """Create a new security alert"""
        try:
            # Check cooldown to prevent spam
            cooldown_key = f"{alert_type}_{camera_id}_{location}"
            if await self._is_in_cooldown(cooldown_key):
                logger.info(f"Alert {cooldown_key} is in cooldown, skipping")
                return None
            
            # Create alert
            alert = Alert(
                alert_type=alert_type,
                severity=severity,
                title=title,
                description=description,
                camera_id=camera_id,
                location=location,
                coordinates=coordinates,
                detected_objects=detected_objects,
                biometric_data=biometric_data,
                ai_analysis=ai_analysis,
                image_path=image_path,
                video_path=video_path
            )
            
            # Set confidence score based on AI analysis
            if ai_analysis and "confidence_scores" in ai_analysis:
                scores = ai_analysis["confidence_scores"]
                alert.confidence_score = max(scores.values()) if scores else 0.0
            
            # Store alert (in real implementation, save to database)
            alert.id = len(self.active_alerts) + 1
            self.active_alerts[alert.id] = alert
            
            # Set cooldown
            self.alert_cooldowns[cooldown_key] = datetime.utcnow()
            
            # Send notifications
            await self._send_notifications(alert)
            
            logger.info(f"Alert created: {alert.title} (ID: {alert.id})")
            return alert
            
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            raise
    
    async def _is_in_cooldown(self, cooldown_key: str) -> bool:
        """Check if alert type is in cooldown period"""
        try:
            if cooldown_key not in self.alert_cooldowns:
                return False
            
            last_alert_time = self.alert_cooldowns[cooldown_key]
            cooldown_duration = timedelta(seconds=settings.ALERT_COOLDOWN)
            
            return datetime.utcnow() - last_alert_time < cooldown_duration
            
        except Exception as e:
            logger.error(f"Error checking cooldown: {e}")
            return False
    
    async def _send_notifications(self, alert: Alert):
        """Send notifications for the alert"""
        try:
            # Prepare notification data
            notification_data = {
                "alert_id": alert.id,
                "type": alert.alert_type,
                "severity": alert.severity,
                "title": alert.title,
                "description": alert.description,
                "location": alert.location,
                "timestamp": alert.created_at.isoformat(),
                "camera_id": alert.camera_id,
                "confidence": alert.confidence_score,
                "image_path": alert.image_path,
                "video_path": alert.video_path
            }
            
            # Send email notification
            if settings.EMAIL_ENABLED:
                email_sent = await self.notification_service.send_email_alert(notification_data)
                alert.email_sent = email_sent
            
            # Send SMS notification
            if settings.SMS_ENABLED:
                sms_sent = await self.notification_service.send_sms_alert(notification_data)
                alert.sms_sent = sms_sent
            
            # Send webhook notification
            if settings.WEBHOOK_URL:
                webhook_sent = await self.notification_service.send_webhook_alert(notification_data)
                alert.webhook_sent = webhook_sent
            
            # Send push notification (for mobile app)
            await self.notification_service.send_push_notification(notification_data)
            
            logger.info(f"Notifications sent for alert {alert.id}")
            
        except Exception as e:
            logger.error(f"Error sending notifications for alert {alert.id}: {e}")
    
    async def acknowledge_alert(self, alert_id: int, user_id: int) -> bool:
        """Acknowledge an alert"""
        try:
            if alert_id not in self.active_alerts:
                return False
            
            alert = self.active_alerts[alert_id]
            
            if alert.status == "acknowledged":
                logger.info(f"Alert {alert_id} already acknowledged")
                return True
            
            # Update alert
            alert.status = "acknowledged"
            alert.user_id = user_id
            alert.acknowledged_at = datetime.utcnow()
            alert.response_time = (alert.acknowledged_at - alert.created_at).total_seconds()
            
            logger.info(f"Alert {alert_id} acknowledged by user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error acknowledging alert {alert_id}: {e}")
            return False
    
    async def resolve_alert(self, alert_id: int, user_id: int) -> bool:
        """Resolve an alert"""
        try:
            if alert_id not in self.active_alerts:
                return False
            
            alert = self.active_alerts[alert_id]
            
            if alert.status == "resolved":
                logger.info(f"Alert {alert_id} already resolved")
                return True
            
            # Update alert
            alert.status = "resolved"
            alert.user_id = user_id
            alert.resolved_at = datetime.utcnow()
            
            if alert.acknowledged_at:
                alert.response_time = (alert.resolved_at - alert.acknowledged_at).total_seconds()
            else:
                alert.response_time = (alert.resolved_at - alert.created_at).total_seconds()
            
            logger.info(f"Alert {alert_id} resolved by user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error resolving alert {alert_id}: {e}")
            return False
    
    async def get_active_alerts(self, severity: str = None, alert_type: str = None,
                               camera_id: int = None, limit: int = 50) -> List[Alert]:
        """Get active alerts with optional filtering"""
        try:
            alerts = list(self.active_alerts.values())
            
            # Filter by status
            alerts = [a for a in alerts if a.status == "active"]
            
            # Apply filters
            if severity:
                alerts = [a for a in alerts if a.severity == severity]
            
            if alert_type:
                alerts = [a for a in alerts if a.alert_type == alert_type]
            
            if camera_id:
                alerts = [a for a in alerts if a.camera_id == camera_id]
            
            # Sort by creation time (newest first)
            alerts.sort(key=lambda x: x.created_at, reverse=True)
            
            return alerts[:limit]
            
        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return []
    
    async def get_alert_statistics(self, start_date: datetime = None, 
                                  end_date: datetime = None) -> Dict:
        """Get alert statistics"""
        try:
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            
            if not end_date:
                end_date = datetime.utcnow()
            
            # Filter alerts by date range
            alerts = [a for a in self.active_alerts.values() 
                     if start_date <= a.created_at <= end_date]
            
            # Calculate statistics
            stats = {
                "total_alerts": len(alerts),
                "by_severity": {},
                "by_type": {},
                "by_status": {},
                "by_camera": {},
                "response_times": [],
                "average_response_time": 0,
                "unresolved_alerts": 0,
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat()
                }
            }
            
            # Count by severity
            for alert in alerts:
                severity = alert.severity
                stats["by_severity"][severity] = stats["by_severity"].get(severity, 0) + 1
            
            # Count by type
            for alert in alerts:
                alert_type = alert.alert_type
                stats["by_type"][alert_type] = stats["by_type"].get(alert_type, 0) + 1
            
            # Count by status
            for alert in alerts:
                status = alert.status
                stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            
            # Count by camera
            for alert in alerts:
                if alert.camera_id:
                    camera_id = str(alert.camera_id)
                    stats["by_camera"][camera_id] = stats["by_camera"].get(camera_id, 0) + 1
            
            # Calculate response times
            response_times = [a.response_time for a in alerts if a.response_time]
            stats["response_times"] = response_times
            
            if response_times:
                stats["average_response_time"] = sum(response_times) / len(response_times)
            
            # Count unresolved alerts
            stats["unresolved_alerts"] = len([a for a in alerts if a.status == "active"])
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting alert statistics: {e}")
            return {}
    
    async def cleanup_old_alerts(self, retention_days: int = 30):
        """Clean up old resolved alerts"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            alerts_to_remove = []
            for alert_id, alert in self.active_alerts.items():
                if (alert.status == "resolved" and 
                    alert.resolved_at and 
                    alert.resolved_at < cutoff_date):
                    alerts_to_remove.append(alert_id)
            
            for alert_id in alerts_to_remove:
                del self.active_alerts[alert_id]
            
            logger.info(f"Cleaned up {len(alerts_to_remove)} old alerts")
            
        except Exception as e:
            logger.error(f"Error cleaning up old alerts: {e}")
    
    async def get_alert_by_id(self, alert_id: int) -> Optional[Alert]:
        """Get alert by ID"""
        return self.active_alerts.get(alert_id)
    
    async def update_alert(self, alert_id: int, **kwargs) -> bool:
        """Update alert properties"""
        try:
            if alert_id not in self.active_alerts:
                return False
            
            alert = self.active_alerts[alert_id]
            
            # Update allowed fields
            allowed_fields = ["description", "severity", "status", "location", 
                            "coordinates", "detected_objects", "biometric_data", 
                            "ai_analysis", "image_path", "video_path"]
            
            for field, value in kwargs.items():
                if field in allowed_fields:
                    setattr(alert, field, value)
            
            alert.updated_at = datetime.utcnow()
            
            logger.info(f"Alert {alert_id} updated")
            return True
            
        except Exception as e:
            logger.error(f"Error updating alert {alert_id}: {e}")
            return False