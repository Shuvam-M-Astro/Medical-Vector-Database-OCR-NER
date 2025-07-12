"""
API middleware for logging, validation, and error handling.
"""

import time
import json
import re
import os
from typing import Dict, Any
from fastapi import Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from ..utils.validation import InputValidator, ValidationError


def setup_middleware(app):
    """Setup middleware for the FastAPI application."""
    
    # Environment-aware CORS configuration
    is_development = os.getenv("ENVIRONMENT", "development").lower() == "development"
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if is_development else ["http://localhost:3000", "https://yourdomain.com"],
        allow_credentials=True,
        allow_methods=["*"] if is_development else ["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"] if is_development else ["Content-Type", "Authorization"],
    )
    
    # Trusted host middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"] if is_development else ["localhost", "127.0.0.1", "yourdomain.com"]
    )
    
    # Request validation middleware
    @app.middleware("http")
    async def validate_request(request: Request, call_next):
        """Validate and sanitize incoming requests."""
        start_time = time.time()
        
        # Log request
        client_ip = request.client.host if request.client else "unknown"
        logger.info(f"Request: {request.method} {request.url} from {client_ip}")
        
        # Validate request headers
        try:
            validate_request_headers(request)
        except ValidationError as e:
            logger.warning(f"Invalid request headers from {client_ip}: {str(e)}")
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid request headers", "details": str(e)}
            )
        
        # Validate request body for POST/PUT requests
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                await validate_request_body(request)
            except ValidationError as e:
                logger.warning(f"Invalid request body from {client_ip}: {str(e)}")
                return JSONResponse(
                    status_code=400,
                    content={"error": "Invalid request body", "details": str(e)}
                )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Add security headers
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["X-Frame-Options"] = "DENY"
            response.headers["X-XSS-Protection"] = "1; mode=block"
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
            response.headers["Content-Security-Policy"] = "default-src 'self'"
            
            # Log response
            process_time = time.time() - start_time
            logger.info(f"Response: {response.status_code} - {process_time:.3f}s")
            
            return response
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unhandled exception: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"error": "Internal server error", "details": "An unexpected error occurred"}
            )
    
    # Error handling middleware
    @app.middleware("http")
    async def error_handling(request: Request, call_next):
        """Handle errors and provide consistent error responses."""
        try:
            response = await call_next(request)
            return response
        except HTTPException as e:
            # Log HTTP exceptions
            client_ip = request.client.host if request.client else "unknown"
            logger.warning(f"HTTP {e.status_code} for {request.method} {request.url} from {client_ip}: {e.detail}")
            
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": "Request failed",
                    "status_code": e.status_code,
                    "details": str(e.detail)
                }
            )
        except ValidationError as e:
            # Log validation errors
            client_ip = request.client.host if request.client else "unknown"
            logger.warning(f"Validation error for {request.method} {request.url} from {client_ip}: {str(e)}")
            
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Validation failed",
                    "details": str(e)
                }
            )
        except Exception as e:
            # Log unexpected errors
            client_ip = request.client.host if request.client else "unknown"
            logger.error(f"Unexpected error for {request.method} {request.url} from {client_ip}: {str(e)}")
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "details": "An unexpected error occurred"
                }
            )


def validate_request_headers(request: Request):
    """Validate request headers for security and consistency."""
    headers = request.headers
    
    # Check for required headers
    required_headers = ["user-agent"]
    for header in required_headers:
        if header not in headers:
            raise ValidationError(f"Missing required header: {header}")
    
    # Validate content-type for POST/PUT requests
    if request.method in ["POST", "PUT", "PATCH"]:
        content_type = headers.get("content-type", "")
        if not content_type:
            raise ValidationError("Missing content-type header")
        
        # Validate content-type format
        if not re.match(r'^[a-zA-Z0-9\-_]+/[a-zA-Z0-9\-_]+(\s*;\s*[a-zA-Z0-9\-_=]+)*$', content_type):
            raise ValidationError("Invalid content-type format")
    
    # Check for suspicious headers
    suspicious_headers = [
        "x-forwarded-for",
        "x-real-ip",
        "x-forwarded-proto",
        "x-forwarded-host"
    ]
    
    for header in suspicious_headers:
        if header in headers:
            value = headers[header]
            # Basic validation for IP addresses
            if header in ["x-forwarded-for", "x-real-ip"]:
                if not re.match(r'^[\d\.]+$', value):
                    raise ValidationError(f"Invalid {header} value")
    
    # Validate user-agent
    user_agent = headers.get("user-agent", "")
    if len(user_agent) > 500:
        raise ValidationError("User-Agent header too long")
    
    # Check for suspicious user-agent patterns
    suspicious_ua_patterns = [
        r'<script',
        r'javascript:',
        r'data:',
        r'vbscript:',
    ]
    
    for pattern in suspicious_ua_patterns:
        if re.search(pattern, user_agent, re.IGNORECASE):
            raise ValidationError("Suspicious User-Agent header")


async def validate_request_body(request: Request):
    """Validate request body for security and consistency."""
    content_type = request.headers.get("content-type", "")
    
    # Skip validation for multipart/form-data (file uploads)
    if "multipart/form-data" in content_type:
        return
    
    # Validate JSON requests
    if "application/json" in content_type:
        try:
            body = await request.body()
            if body:
                # Check body size
                if len(body) > 10 * 1024 * 1024:  # 10MB limit
                    raise ValidationError("Request body too large")
                
                # Parse and validate JSON
                try:
                    json_data = json.loads(body.decode('utf-8'))
                    validate_json_structure(json_data)
                except json.JSONDecodeError:
                    raise ValidationError("Invalid JSON format")
                except ValidationError:
                    raise
        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"Error reading request body: {str(e)}")


def validate_json_structure(data: Any, max_depth: int = 10, current_depth: int = 0):
    """Validate JSON structure for security and consistency."""
    if current_depth > max_depth:
        raise ValidationError("JSON structure too deep")
    
    if isinstance(data, dict):
        # Check dictionary size
        if len(data) > 100:
            raise ValidationError("JSON object too large")
        
        for key, value in data.items():
            # Validate key
            if not isinstance(key, str):
                raise ValidationError("JSON keys must be strings")
            
            if len(key) > 100:
                raise ValidationError("JSON key too long")
            
            # Check for suspicious keys
            suspicious_keys = [
                "__proto__",
                "constructor",
                "prototype",
                "eval",
                "Function",
                "setTimeout",
                "setInterval"
            ]
            
            if key.lower() in [k.lower() for k in suspicious_keys]:
                raise ValidationError(f"Suspicious JSON key: {key}")
            
            # Recursively validate value
            validate_json_structure(value, max_depth, current_depth + 1)
    
    elif isinstance(data, list):
        # Check list size
        if len(data) > 1000:
            raise ValidationError("JSON array too large")
        
        for item in data:
            validate_json_structure(item, max_depth, current_depth + 1)
    
    elif isinstance(data, str):
        # Validate string length
        if len(data) > 10000:
            raise ValidationError("JSON string too long")
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'<script',
            r'javascript:',
            r'data:',
            r'vbscript:',
            r'onload=',
            r'onerror=',
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, data, re.IGNORECASE):
                raise ValidationError("JSON contains suspicious content")
    
    elif isinstance(data, (int, float, bool)):
        # Validate numeric values
        if isinstance(data, (int, float)):
            if abs(data) > 1e15:  # Reasonable limit for numeric values
                raise ValidationError("Numeric value too large")
    
    elif data is None:
        # Allow null values
        pass
    
    else:
        raise ValidationError(f"Unsupported JSON type: {type(data)}")


def sanitize_response_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize response data to prevent information leakage."""
    if not isinstance(data, dict):
        return data
    
    sanitized = {}
    sensitive_keys = [
        "password", "token", "secret", "key", "api_key",
        "private", "internal", "debug", "error_details"
    ]
    
    for key, value in data.items():
        # Check if key contains sensitive information
        is_sensitive = any(sensitive in key.lower() for sensitive in sensitive_keys)
        
        if is_sensitive:
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_response_data(value)
        elif isinstance(value, list):
            sanitized[key] = [sanitize_response_data(item) if isinstance(item, dict) else item for item in value]
        else:
            sanitized[key] = value
    
    return sanitized 