# Smart Surveillance System

A comprehensive smart surveillance system integrated with biometric sensors, 360° night-vision cameras, and AI-enabled emergency response for vehicles and public areas.

## 🚀 Features

### Core Surveillance
- **360° Night Vision Cameras**: High-resolution cameras with advanced night vision capabilities
- **Motion Detection**: Real-time motion detection with configurable sensitivity
- **Live Streaming**: Real-time video streaming from multiple cameras
- **Recording & Playback**: Automated recording with triggered events
- **PTZ Control**: Pan-Tilt-Zoom camera control capabilities

### Biometric Security
- **Face Recognition**: Advanced facial recognition with liveness detection
- **Fingerprint Authentication**: Secure fingerprint-based access control
- **Iris Recognition**: High-security iris scanning (optional)
- **Multi-Modal Authentication**: Combine multiple biometric methods
- **Anti-Spoofing**: Liveness detection to prevent fake biometric attacks

### AI-Powered Analytics
- **Emergency Detection**: Real-time detection of emergency situations
- **Violence Detection**: Automated violence and aggression detection
- **Anomaly Detection**: Unusual behavior pattern recognition
- **Object Detection**: Identification of people, vehicles, and objects
- **Pose Estimation**: Human pose analysis for emergency situations

### Alert & Notification System
- **Real-time Alerts**: Instant notifications for security events
- **Multi-Channel Notifications**: Email, SMS, webhook, and push notifications
- **Alert Management**: Acknowledge, resolve, and track security incidents
- **Escalation Policies**: Automatic escalation based on severity
- **Dashboard Analytics**: Comprehensive reporting and statistics

## 🛠️ Technology Stack

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Cache**: Redis
- **AI/ML**: TensorFlow, PyTorch, OpenCV
- **Biometrics**: face_recognition, MediaPipe
- **Authentication**: JWT tokens, OAuth2
- **Deployment**: Docker, Docker Compose
- **Reverse Proxy**: Nginx
- **Monitoring**: Prometheus, Grafana

## 📦 Installation

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (optional)

### Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone https://github.com/MonuYadav02/smart-surveillance-biometric-security.git
   cd smart-surveillance-biometric-security
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - API Documentation: http://localhost/docs
   - Health Check: http://localhost/health
   - Admin Dashboard: http://localhost/

### Manual Installation

1. **Install system dependencies**
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install -y python3-pip python3-venv postgresql redis-server
   sudo apt-get install -y libopencv-dev python3-opencv ffmpeg
   
   # CentOS/RHEL
   sudo yum install python3-pip python3-venv postgresql-server redis
   sudo yum install opencv-devel opencv-python ffmpeg
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure database**
   ```bash
   # Create database
   sudo -u postgres createdb surveillance_db
   
   # Run migrations (if using Alembic)
   alembic upgrade head
   ```

5. **Start the application**
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# Application
DEBUG=false
HOST=0.0.0.0
PORT=8000
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql://user:password@localhost/surveillance_db

# Notifications
EMAIL_ENABLED=true
SMTP_SERVER=smtp.gmail.com
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-password
ALERT_EMAIL_RECIPIENTS=admin@example.com

# Camera Settings
CAMERA_RESOLUTION_WIDTH=1920
CAMERA_RESOLUTION_HEIGHT=1080
MOTION_DETECTION_SENSITIVITY=0.5

# AI Settings
VIOLENCE_DETECTION_ENABLED=true
ANOMALY_DETECTION_ENABLED=true
EMERGENCY_DETECTION_THRESHOLD=0.7
```

### Camera Configuration

Add cameras via the API:

```bash
curl -X POST "http://localhost:8000/api/v1/cameras/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Main Entrance",
    "location": "Building A - Entrance",
    "ip_address": "192.168.1.100",
    "port": 554,
    "has_night_vision": true,
    "has_360_degree": true,
    "motion_detection_enabled": true
  }'
```

## 🔐 Authentication

### Traditional Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "password"
  }'
```

### Biometric Authentication
```bash
# Face recognition
curl -X POST "http://localhost:8000/api/v1/auth/biometric/login" \
  -H "Content-Type: multipart/form-data" \
  -F "method=face" \
  -F "face_image=@face_image.jpg"

# Multi-modal authentication
curl -X POST "http://localhost:8000/api/v1/auth/biometric/login" \
  -H "Content-Type: multipart/form-data" \
  -F "method=multi_modal" \
  -F "face_image=@face_image.jpg" \
  -F "fingerprint_data=@fingerprint.dat"
```

## 📊 API Usage

### Camera Management
```bash
# List cameras
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/cameras/"

# Stream camera
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/cameras/1/stream"

# Start recording
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/cameras/1/record" \
  -d '{"duration": 300}'
```

### Alert Management
```bash
# Get alerts
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/alerts/?severity=high"

# Acknowledge alert
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/alerts/1/acknowledge"

# Get alert statistics
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/alerts/statistics/overview"
```

### Biometric Registration
```bash
# Register face
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/biometric/register/face" \
  -F "user_id=1" \
  -F "face_image=@face_image.jpg"

# Register fingerprint
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/biometric/register/fingerprint" \
  -F "user_id=1" \
  -F "fingerprint_image=@fingerprint.jpg"
```

## 🚨 Alert Types

The system generates various types of alerts:

- **Motion**: Movement detected in monitored areas
- **Intrusion**: Unauthorized access attempts
- **Violence**: Aggressive behavior detected
- **Emergency**: Emergency situations (falls, distress)
- **Anomaly**: Unusual behavior patterns
- **Biometric**: Authentication failures or security breaches

## 📈 Monitoring & Analytics

### System Health
```bash
# Health check
curl "http://localhost:8000/health"

# System status
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/surveillance/status"

# System metrics
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/surveillance/metrics"
```

### Performance Metrics
- Real-time system resource usage
- Camera performance statistics
- Alert response times
- Biometric authentication success rates
- AI model accuracy metrics

## 🔧 Maintenance

### Database Maintenance
```bash
# Backup database
pg_dump surveillance_db > backup.sql

# Restore database
psql surveillance_db < backup.sql

# Clean old recordings
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/surveillance/cleanup"
```

### Log Management
```bash
# View logs
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/surveillance/logs?level=ERROR"

# Log rotation (configure in logrotate)
/var/log/surveillance/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 surveillance surveillance
}
```

## 🛡️ Security Considerations

### Network Security
- Use HTTPS in production
- Implement proper firewall rules
- VPN access for remote monitoring
- Regular security updates

### Data Privacy
- Encrypt biometric data at rest
- Implement data retention policies
- GDPR compliance for EU deployments
- Regular security audits

### Access Control
- Role-based access control (RBAC)
- Multi-factor authentication
- Session management
- Audit logging

## 🚀 Deployment

### Production Deployment
```bash
# Build production image
docker build -t smart-surveillance:latest .

# Deploy with Docker Compose
docker-compose -f docker-compose.prod.yml up -d

# Scale services
docker-compose up -d --scale app=3
```

### Cloud Deployment
- AWS ECS/EKS
- Google Cloud Run/GKE
- Azure Container Instances/AKS
- Kubernetes manifests available

## 📚 Documentation

- **API Documentation**: Available at `/docs` endpoint
- **Architecture Guide**: `docs/architecture.md`
- **Deployment Guide**: `docs/deployment.md`
- **Security Guide**: `docs/security.md`
- **Troubleshooting**: `docs/troubleshooting.md`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- **Issues**: GitHub Issues
- **Documentation**: `/docs` endpoint
- **Email**: support@example.com

## 🙏 Acknowledgments

- OpenCV for computer vision capabilities
- TensorFlow/PyTorch for AI models
- FastAPI for the web framework
- All contributors and the open-source community

---

**Smart Surveillance System** - Enhancing security through intelligent monitoring and biometric authentication.
