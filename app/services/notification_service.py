"""
Notification Service for Alert Delivery
"""

import asyncio
import logging
import smtplib
import json
from typing import Dict, List, Optional
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import httpx
import os

from app.core.config import settings

logger = logging.getLogger(__name__)

class NotificationService:
    """Notification service for sending alerts via multiple channels"""
    
    def __init__(self):
        self.email_config = {
            "smtp_server": os.getenv("SMTP_SERVER", "localhost"),
            "smtp_port": int(os.getenv("SMTP_PORT", "587")),
            "smtp_username": os.getenv("SMTP_USERNAME", ""),
            "smtp_password": os.getenv("SMTP_PASSWORD", ""),
            "sender_email": os.getenv("SENDER_EMAIL", "surveillance@example.com"),
            "sender_name": os.getenv("SENDER_NAME", "Smart Surveillance System")
        }
        
        self.sms_config = {
            "api_key": os.getenv("SMS_API_KEY", ""),
            "api_url": os.getenv("SMS_API_URL", ""),
            "sender_number": os.getenv("SMS_SENDER_NUMBER", "")
        }
        
        self.notification_recipients = {
            "email": os.getenv("ALERT_EMAIL_RECIPIENTS", "").split(","),
            "sms": os.getenv("ALERT_SMS_RECIPIENTS", "").split(","),
            "push": []
        }
        
        self.http_client = None
        
    async def initialize(self):
        """Initialize notification service"""
        logger.info("Initializing Notification Service...")
        
        # Initialize HTTP client for API calls
        self.http_client = httpx.AsyncClient(timeout=30.0)
        
        # Load notification recipients from database
        await self._load_notification_recipients()
        
        logger.info("Notification Service initialized successfully")
    
    async def cleanup(self):
        """Cleanup notification service"""
        logger.info("Cleaning up Notification Service...")
        
        if self.http_client:
            await self.http_client.aclose()
        
        logger.info("Notification Service cleanup complete")
    
    async def _load_notification_recipients(self):
        """Load notification recipients from database"""
        try:
            # In a real implementation, you would load from database
            # This includes email addresses, phone numbers, and push notification tokens
            # for different user roles (admin, security officer, etc.)
            
            logger.info("Loading notification recipients...")
            
            # Filter out empty strings
            self.notification_recipients["email"] = [
                email.strip() for email in self.notification_recipients["email"] 
                if email.strip()
            ]
            
            self.notification_recipients["sms"] = [
                phone.strip() for phone in self.notification_recipients["sms"] 
                if phone.strip()
            ]
            
            logger.info(f"Loaded {len(self.notification_recipients['email'])} email recipients")
            logger.info(f"Loaded {len(self.notification_recipients['sms'])} SMS recipients")
            
        except Exception as e:
            logger.error(f"Error loading notification recipients: {e}")
    
    async def send_email_alert(self, alert_data: Dict) -> bool:
        """Send email alert notification"""
        try:
            if not settings.EMAIL_ENABLED or not self.notification_recipients["email"]:
                return False
            
            # Create email message
            subject = f"[{alert_data['severity'].upper()}] {alert_data['title']}"
            
            # Create HTML email content
            html_body = await self._create_email_html(alert_data)
            
            # Create text email content
            text_body = await self._create_email_text(alert_data)
            
            # Send to all recipients
            for recipient in self.notification_recipients["email"]:
                try:
                    msg = MIMEMultipart("alternative")
                    msg["Subject"] = subject
                    msg["From"] = f"{self.email_config['sender_name']} <{self.email_config['sender_email']}>"
                    msg["To"] = recipient
                    
                    # Add text and HTML parts
                    text_part = MIMEText(text_body, "plain")
                    html_part = MIMEText(html_body, "html")
                    
                    msg.attach(text_part)
                    msg.attach(html_part)
                    
                    # Attach image if available
                    if alert_data.get("image_path") and os.path.exists(alert_data["image_path"]):
                        with open(alert_data["image_path"], "rb") as f:
                            img_data = f.read()
                            img = MIMEImage(img_data)
                            img.add_header("Content-ID", "<alert_image>")
                            msg.attach(img)
                    
                    # Send email
                    await self._send_email(msg)
                    
                except Exception as e:
                    logger.error(f"Error sending email to {recipient}: {e}")
                    continue
            
            logger.info(f"Email alerts sent for alert {alert_data['alert_id']}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
            return False
    
    async def _send_email(self, msg: MIMEMultipart):
        """Send email using SMTP"""
        try:
            server = smtplib.SMTP(self.email_config["smtp_server"], self.email_config["smtp_port"])
            server.starttls()
            
            if self.email_config["smtp_username"]:
                server.login(self.email_config["smtp_username"], self.email_config["smtp_password"])
            
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            logger.error(f"Error sending SMTP email: {e}")
            raise
    
    async def _create_email_html(self, alert_data: Dict) -> str:
        """Create HTML email content"""
        severity_colors = {
            "low": "#28a745",
            "medium": "#ffc107", 
            "high": "#fd7e14",
            "critical": "#dc3545"
        }
        
        color = severity_colors.get(alert_data["severity"], "#6c757d")
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
                .header {{ background-color: {color}; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .alert-info {{ background-color: #f8f9fa; padding: 15px; margin: 10px 0; border-left: 4px solid {color}; }}
                .footer {{ background-color: #f8f9fa; padding: 10px; text-align: center; font-size: 12px; color: #6c757d; }}
                .image {{ text-align: center; margin: 20px 0; }}
                .image img {{ max-width: 100%; height: auto; border: 1px solid #ddd; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🚨 Security Alert</h1>
                <h2>{alert_data['title']}</h2>
            </div>
            
            <div class="content">
                <div class="alert-info">
                    <h3>Alert Details</h3>
                    <p><strong>Severity:</strong> {alert_data['severity'].upper()}</p>
                    <p><strong>Type:</strong> {alert_data['type']}</p>
                    <p><strong>Time:</strong> {alert_data['timestamp']}</p>
                    <p><strong>Location:</strong> {alert_data.get('location', 'Unknown')}</p>
                    {f"<p><strong>Camera:</strong> {alert_data['camera_id']}</p>" if alert_data.get('camera_id') else ""}
                    {f"<p><strong>Confidence:</strong> {alert_data['confidence']:.2f}</p>" if alert_data.get('confidence') else ""}
                </div>
                
                {f"<div class='alert-info'><h3>Description</h3><p>{alert_data['description']}</p></div>" if alert_data.get('description') else ""}
                
                <div class="image">
                    <img src="cid:alert_image" alt="Alert Image" style="max-width: 600px;">
                </div>
            </div>
            
            <div class="footer">
                <p>Smart Surveillance System - Automated Alert</p>
                <p>Please acknowledge this alert in the system dashboard.</p>
            </div>
        </body>
        </html>
        """
        
        return html
    
    async def _create_email_text(self, alert_data: Dict) -> str:
        """Create text email content"""
        text = f"""
🚨 SECURITY ALERT 🚨

{alert_data['title']}

Alert Details:
- Severity: {alert_data['severity'].upper()}
- Type: {alert_data['type']}
- Time: {alert_data['timestamp']}
- Location: {alert_data.get('location', 'Unknown')}
"""
        
        if alert_data.get('camera_id'):
            text += f"- Camera: {alert_data['camera_id']}\n"
        
        if alert_data.get('confidence'):
            text += f"- Confidence: {alert_data['confidence']:.2f}\n"
        
        if alert_data.get('description'):
            text += f"\nDescription:\n{alert_data['description']}\n"
        
        text += """
Please acknowledge this alert in the system dashboard.

---
Smart Surveillance System - Automated Alert
        """
        
        return text
    
    async def send_sms_alert(self, alert_data: Dict) -> bool:
        """Send SMS alert notification"""
        try:
            if not settings.SMS_ENABLED or not self.notification_recipients["sms"]:
                return False
            
            # Create SMS message
            message = f"🚨 ALERT: {alert_data['title']} | {alert_data['severity'].upper()} | {alert_data['timestamp']} | Location: {alert_data.get('location', 'Unknown')}"
            
            # Send to all recipients
            for recipient in self.notification_recipients["sms"]:
                try:
                    await self._send_sms(recipient, message)
                except Exception as e:
                    logger.error(f"Error sending SMS to {recipient}: {e}")
                    continue
            
            logger.info(f"SMS alerts sent for alert {alert_data['alert_id']}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending SMS alert: {e}")
            return False
    
    async def _send_sms(self, phone_number: str, message: str):
        """Send SMS using API"""
        try:
            if not self.sms_config["api_key"] or not self.sms_config["api_url"]:
                logger.warning("SMS API configuration missing")
                return
            
            # SMS API payload (adjust based on your SMS provider)
            payload = {
                "to": phone_number,
                "from": self.sms_config["sender_number"],
                "text": message
            }
            
            headers = {
                "Authorization": f"Bearer {self.sms_config['api_key']}",
                "Content-Type": "application/json"
            }
            
            response = await self.http_client.post(
                self.sms_config["api_url"],
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                logger.info(f"SMS sent successfully to {phone_number}")
            else:
                logger.error(f"SMS API error: {response.status_code} - {response.text}")
            
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            raise
    
    async def send_webhook_alert(self, alert_data: Dict) -> bool:
        """Send webhook alert notification"""
        try:
            if not settings.WEBHOOK_URL:
                return False
            
            # Prepare webhook payload
            payload = {
                "event": "security_alert",
                "alert": alert_data,
                "timestamp": datetime.utcnow().isoformat(),
                "source": "smart_surveillance_system"
            }
            
            headers = {
                "Content-Type": "application/json",
                "User-Agent": "SmartSurveillanceSystem/1.0"
            }
            
            response = await self.http_client.post(
                settings.WEBHOOK_URL,
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                logger.info(f"Webhook sent successfully for alert {alert_data['alert_id']}")
                return True
            else:
                logger.error(f"Webhook error: {response.status_code} - {response.text}")
                return False
            
        except Exception as e:
            logger.error(f"Error sending webhook alert: {e}")
            return False
    
    async def send_push_notification(self, alert_data: Dict) -> bool:
        """Send push notification to mobile apps"""
        try:
            # This would integrate with Firebase Cloud Messaging or Apple Push Notification Service
            # For now, we'll just log the notification
            
            logger.info(f"Push notification would be sent for alert {alert_data['alert_id']}")
            
            # In a real implementation:
            # 1. Load FCM/APNS tokens from database
            # 2. Create notification payload
            # 3. Send to FCM/APNS
            # 4. Handle delivery receipts
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            return False
    
    async def send_test_notification(self, channel: str = "all") -> Dict:
        """Send test notification to verify configuration"""
        try:
            test_alert = {
                "alert_id": 0,
                "type": "test",
                "severity": "low",
                "title": "Test Alert - System Check",
                "description": "This is a test notification to verify the alert system is working correctly.",
                "location": "Test Location",
                "timestamp": datetime.utcnow().isoformat(),
                "camera_id": None,
                "confidence": 1.0,
                "image_path": None,
                "video_path": None
            }
            
            results = {}
            
            if channel in ["all", "email"]:
                results["email"] = await self.send_email_alert(test_alert)
            
            if channel in ["all", "sms"]:
                results["sms"] = await self.send_sms_alert(test_alert)
            
            if channel in ["all", "webhook"]:
                results["webhook"] = await self.send_webhook_alert(test_alert)
            
            if channel in ["all", "push"]:
                results["push"] = await self.send_push_notification(test_alert)
            
            return results
            
        except Exception as e:
            logger.error(f"Error sending test notification: {e}")
            return {"error": str(e)}