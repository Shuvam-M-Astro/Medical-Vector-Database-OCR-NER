"""
Health check and monitoring utilities.
"""

import os
import psutil
import asyncio
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
from loguru import logger

from ..config import settings


class HealthStatus(Enum):
    """Health status enumeration."""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class HealthCheck:
    """Comprehensive health check system."""
    
    def __init__(self):
        """Initialize health check system."""
        self.health_history = []
        self.last_check = None
        self.unhealthy_count = 0
        self._lock = asyncio.Lock()
    
    async def perform_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        async with self._lock:
            start_time = time.time()
            
            # System resource checks
            system_health = await self._check_system_resources()
            
            # Service availability checks
            service_health = await self._check_services()
            
            # Database health check
            database_health = await self._check_database()
            
            # File system health check
            filesystem_health = await self._check_filesystem()
            
            # Determine overall health
            overall_status = self._determine_overall_health([
                system_health,
                service_health,
                database_health,
                filesystem_health
            ])
            
            health_result = {
                "status": overall_status.value,
                "timestamp": datetime.now().isoformat(),
                "response_time": time.time() - start_time,
                "checks": {
                    "system": system_health,
                    "services": service_health,
                    "database": database_health,
                    "filesystem": filesystem_health
                },
                "summary": {
                    "total_checks": 4,
                    "healthy_checks": sum(1 for check in [system_health, service_health, database_health, filesystem_health] 
                                        if check["status"] == HealthStatus.HEALTHY.value),
                    "unhealthy_checks": sum(1 for check in [system_health, service_health, database_health, filesystem_health] 
                                          if check["status"] == HealthStatus.UNHEALTHY.value)
                }
            }
            
            # Update health history
            self.health_history.append(health_result)
            self.last_check = datetime.now()
            
            # Keep only last 100 health checks
            if len(self.health_history) > 100:
                self.health_history = self.health_history[-100:]
            
            # Update unhealthy count
            if overall_status == HealthStatus.UNHEALTHY:
                self.unhealthy_count += 1
            else:
                self.unhealthy_count = 0
            
            return health_result
    
    async def _check_system_resources(self) -> Dict[str, Any]:
        """Check system resource usage."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # Network I/O
            network = psutil.net_io_counters()
            
            # Determine status
            status = HealthStatus.HEALTHY
            issues = []
            
            if cpu_percent > 80:
                status = HealthStatus.DEGRADED
                issues.append(f"High CPU usage: {cpu_percent:.1f}%")
            
            if memory_percent > settings.MAX_MEMORY_USAGE:
                status = HealthStatus.UNHEALTHY
                issues.append(f"High memory usage: {memory_percent:.1f}%")
            
            if disk_percent > settings.DISK_SPACE_THRESHOLD:
                status = HealthStatus.UNHEALTHY
                issues.append(f"Low disk space: {disk_percent:.1f}% used")
            
            return {
                "status": status.value,
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "disk_percent": disk_percent,
                "network_bytes_sent": network.bytes_sent,
                "network_bytes_recv": network.bytes_recv,
                "issues": issues
            }
            
        except Exception as e:
            logger.error(f"System resource check failed: {str(e)}")
            return {
                "status": HealthStatus.UNHEALTHY.value,
                "error": str(e),
                "issues": ["System resource check failed"]
            }
    
    async def _check_services(self) -> Dict[str, Any]:
        """Check service availability."""
        try:
            # Check if required directories exist
            required_dirs = [
                settings.UPLOAD_DIR,
                settings.PROCESSED_DIR,
                settings.CHROMA_DB_PATH,
                os.path.dirname(settings.LOG_FILE)
            ]
            
            missing_dirs = []
            for directory in required_dirs:
                if not os.path.exists(directory):
                    missing_dirs.append(directory)
            
            # Check if log file is writable
            log_writable = os.access(os.path.dirname(settings.LOG_FILE), os.W_OK)
            
            # Check if temp directory is writable
            temp_writable = os.access(settings.UPLOAD_DIR, os.W_OK)
            
            status = HealthStatus.HEALTHY
            issues = []
            
            if missing_dirs:
                status = HealthStatus.UNHEALTHY
                issues.append(f"Missing directories: {', '.join(missing_dirs)}")
            
            if not log_writable:
                status = HealthStatus.UNHEALTHY
                issues.append("Log directory not writable")
            
            if not temp_writable:
                status = HealthStatus.UNHEALTHY
                issues.append("Upload directory not writable")
            
            return {
                "status": status.value,
                "directories_exist": len(missing_dirs) == 0,
                "log_writable": log_writable,
                "temp_writable": temp_writable,
                "missing_directories": missing_dirs,
                "issues": issues
            }
            
        except Exception as e:
            logger.error(f"Service check failed: {str(e)}")
            return {
                "status": HealthStatus.UNHEALTHY.value,
                "error": str(e),
                "issues": ["Service check failed"]
            }
    
    async def _check_database(self) -> Dict[str, Any]:
        """Check database health."""
        try:
            # Check if ChromaDB directory exists and is accessible
            db_exists = os.path.exists(settings.CHROMA_DB_PATH)
            db_writable = os.access(settings.CHROMA_DB_PATH, os.W_OK) if db_exists else False
            
            # Check database size
            db_size = 0
            if db_exists:
                db_size = sum(
                    os.path.getsize(os.path.join(dirpath, filename))
                    for dirpath, dirnames, filenames in os.walk(settings.CHROMA_DB_PATH)
                    for filename in filenames
                )
            
            status = HealthStatus.HEALTHY
            issues = []
            
            if not db_exists:
                status = HealthStatus.DEGRADED
                issues.append("Database directory does not exist")
            
            if not db_writable:
                status = HealthStatus.UNHEALTHY
                issues.append("Database directory not writable")
            
            return {
                "status": status.value,
                "database_exists": db_exists,
                "database_writable": db_writable,
                "database_size_bytes": db_size,
                "issues": issues
            }
            
        except Exception as e:
            logger.error(f"Database check failed: {str(e)}")
            return {
                "status": HealthStatus.UNHEALTHY.value,
                "error": str(e),
                "issues": ["Database check failed"]
            }
    
    async def _check_filesystem(self) -> Dict[str, Any]:
        """Check filesystem health."""
        try:
            # Check for temporary files that need cleanup
            temp_files = []
            if os.path.exists(settings.UPLOAD_DIR):
                for filename in os.listdir(settings.UPLOAD_DIR):
                    file_path = os.path.join(settings.UPLOAD_DIR, filename)
                    if os.path.isfile(file_path):
                        # Check if file is older than 1 hour
                        file_age = time.time() - os.path.getmtime(file_path)
                        if file_age > 3600:  # 1 hour
                            temp_files.append(filename)
            
            # Check disk space for upload directory
            upload_space = psutil.disk_usage(settings.UPLOAD_DIR)
            upload_space_percent = upload_space.percent
            
            status = HealthStatus.HEALTHY
            issues = []
            
            if len(temp_files) > 10:
                status = HealthStatus.DEGRADED
                issues.append(f"Too many temporary files: {len(temp_files)}")
            
            if upload_space_percent > 95:
                status = HealthStatus.UNHEALTHY
                issues.append(f"Upload directory nearly full: {upload_space_percent:.1f}%")
            
            return {
                "status": status.value,
                "temp_files_count": len(temp_files),
                "upload_space_percent": upload_space_percent,
                "temp_files": temp_files[:10],  # Limit to first 10
                "issues": issues
            }
            
        except Exception as e:
            logger.error(f"Filesystem check failed: {str(e)}")
            return {
                "status": HealthStatus.UNHEALTHY.value,
                "error": str(e),
                "issues": ["Filesystem check failed"]
            }
    
    def _determine_overall_health(self, checks: List[Dict[str, Any]]) -> HealthStatus:
        """Determine overall health status based on individual checks."""
        unhealthy_count = sum(1 for check in checks if check["status"] == HealthStatus.UNHEALTHY.value)
        degraded_count = sum(1 for check in checks if check["status"] == HealthStatus.DEGRADED.value)
        
        if unhealthy_count > 0:
            return HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY
    
    def get_health_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent health check history."""
        return self.health_history[-limit:] if self.health_history else []
    
    def is_healthy(self) -> bool:
        """Check if system is currently healthy."""
        if not self.last_check:
            return True  # Assume healthy if no checks performed
        
        # Consider unhealthy if last check was more than 5 minutes ago and we have unhealthy history
        time_since_check = (datetime.now() - self.last_check).total_seconds()
        if time_since_check > 300 and self.unhealthy_count > 0:  # 5 minutes
            return False
        
        return self.unhealthy_count < settings.UNHEALTHY_THRESHOLD


# Global health check instance
health_checker = HealthCheck() 