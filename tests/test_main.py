"""
Basic tests for Smart Surveillance System
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert data["message"] == "Smart Surveillance System API"

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data

def test_api_docs():
    """Test API documentation is accessible"""
    response = client.get("/docs")
    assert response.status_code == 200

def test_openapi_schema():
    """Test OpenAPI schema is accessible"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data

def test_login_endpoint():
    """Test login endpoint structure"""
    response = client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "password"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data

def test_invalid_login():
    """Test invalid login"""
    response = client.post("/api/v1/auth/login", json={
        "username": "invalid",
        "password": "invalid"
    })
    assert response.status_code == 401