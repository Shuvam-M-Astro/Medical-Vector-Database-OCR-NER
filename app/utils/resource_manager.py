"""
Resource management and cleanup utilities.
"""

import os
import shutil
import time
import asyncio
import psutil
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
from loguru import logger

from ..config import settings


class ResourceManager:
    """Resource management and cleanup system."""
    
    def __init__(self):
        """Initialize resource manager."""
        self.cleanup_tasks = []
        self.last_cleanup = None
        self._lock = asyncio.Lock()
    
    async def start_cleanup_scheduler(self):
        """Start the cleanup scheduler."""
        while True:
            try:
                await self.perform_cleanup()
                await asyncio.sleep(settings.TEMP_FILE_CLEANUP_INTERVAL)
            except Exception as e:
                logger.error(f"Cleanup scheduler error: {str(e)}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def perform_cleanup(self):
        """Perform comprehensive cleanup."""
        async with self._lock:
            logger.info("Starting resource cleanup")
            
            # Clean up temporary files
            temp_files_cleaned = await self._cleanup_temp_files()
            
            # Clean up old log files
            log_files_cleaned = await self._cleanup_log_files()
            
            # Clean up cache
            cache_cleaned = await self._cleanup_cache()
            
            # Memory cleanup
            memory_freed = await self._cleanup_memory()
            
            logger.info(f"Cleanup completed: {temp_files_cleaned} temp files, "
                       f"{log_files_cleaned} log files, {cache_cleaned} cache entries, "
                       f"{memory_freed}MB memory freed")
    
    async def _cleanup_temp_files(self) -> int:
        """Clean up temporary files older than 1 hour."""
        try:
            cleaned_count = 0
            current_time = time.time()
            
            # Clean upload directory
            if os.path.exists(settings.UPLOAD_DIR):
                for filename in os.listdir(settings.UPLOAD_DIR):
                    file_path = os.path.join(settings.UPLOAD_DIR, filename)
                    if os.path.isfile(file_path):
                        file_age = current_time - os.path.getmtime(file_path)
                        if file_age > 3600:  # 1 hour
                            try:
                                os.remove(file_path)
                                cleaned_count += 1
                                logger.debug(f"Cleaned temp file: {filename}")
                            except Exception as e:
                                logger.warning(f"Failed to remove temp file {filename}: {str(e)}")
            
            # Clean processed directory (keep only last 1000 files)
            if os.path.exists(settings.PROCESSED_DIR):
                files = []
                for filename in os.listdir(settings.PROCESSED_DIR):
                    file_path = os.path.join(settings.PROCESSED_DIR, filename)
                    if os.path.isfile(file_path):
                        files.append((file_path, os.path.getmtime(file_path)))
                
                # Sort by modification time (oldest first)
                files.sort(key=lambda x: x[1])
                
                # Remove oldest files if more than 1000
                if len(files) > 1000:
                    files_to_remove = files[:-1000]
                    for file_path, _ in files_to_remove:
                        try:
                            os.remove(file_path)
                            cleaned_count += 1
                            logger.debug(f"Cleaned old processed file: {os.path.basename(file_path)}")
                        except Exception as e:
                            logger.warning(f"Failed to remove old file {file_path}: {str(e)}")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Temp file cleanup failed: {str(e)}")
            return 0
    
    async def _cleanup_log_files(self) -> int:
        """Clean up old log files."""
        try:
            cleaned_count = 0
            log_dir = os.path.dirname(settings.LOG_FILE)
            
            if not os.path.exists(log_dir):
                return 0
            
            current_time = time.time()
            for filename in os.listdir(log_dir):
                if filename.endswith('.log') and filename != 'app.log':
                    file_path = os.path.join(log_dir, filename)
                    if os.path.isfile(file_path):
                        file_age = current_time - os.path.getmtime(file_path)
                        if file_age > 7 * 24 * 3600:  # 7 days
                            try:
                                os.remove(file_path)
                                cleaned_count += 1
                                logger.debug(f"Cleaned old log file: {filename}")
                            except Exception as e:
                                logger.warning(f"Failed to remove log file {filename}: {str(e)}")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Log file cleanup failed: {str(e)}")
            return 0
    
    async def _cleanup_cache(self) -> int:
        """Clean up expired cache entries."""
        try:
            # This would be implemented based on your caching strategy
            # For now, return 0 as we don't have a centralized cache
            return 0
            
        except Exception as e:
            logger.error(f"Cache cleanup failed: {str(e)}")
            return 0
    
    async def _cleanup_memory(self) -> float:
        """Perform memory cleanup."""
        try:
            # Force garbage collection
            import gc
            gc.collect()
            
            # Get memory info before and after
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            
            # Force garbage collection again
            gc.collect()
            
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_freed = memory_before - memory_after
            
            if memory_freed > 10:  # Only log if significant memory was freed
                logger.info(f"Memory cleanup freed {memory_freed:.1f}MB")
            
            return memory_freed
            
        except Exception as e:
            logger.error(f"Memory cleanup failed: {str(e)}")
            return 0.0
    
    async def check_disk_space(self) -> Dict[str, Any]:
        """Check available disk space."""
        try:
            disk_usage = psutil.disk_usage('/')
            upload_usage = psutil.disk_usage(settings.UPLOAD_DIR)
            
            return {
                "root_free_gb": disk_usage.free / 1024 / 1024 / 1024,
                "root_used_percent": disk_usage.percent,
                "upload_free_gb": upload_usage.free / 1024 / 1024 / 1024,
                "upload_used_percent": upload_usage.percent,
                "critical": disk_usage.percent > settings.DISK_SPACE_THRESHOLD
            }
            
        except Exception as e:
            logger.error(f"Disk space check failed: {str(e)}")
            return {
                "error": str(e),
                "critical": True
            }
    
    async def check_memory_usage(self) -> Dict[str, Any]:
        """Check memory usage."""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            
            return {
                "memory_mb": memory_info.rss / 1024 / 1024,
                "memory_percent": memory_percent,
                "virtual_memory_mb": memory_info.vms / 1024 / 1024,
                "critical": memory_percent > settings.MAX_MEMORY_USAGE
            }
            
        except Exception as e:
            logger.error(f"Memory usage check failed: {str(e)}")
            return {
                "error": str(e),
                "critical": True
            }
    
    async def emergency_cleanup(self):
        """Perform emergency cleanup when resources are critically low."""
        logger.warning("Performing emergency cleanup")
        
        try:
            # Force garbage collection
            import gc
            gc.collect()
            
            # Remove all temporary files regardless of age
            temp_files_removed = 0
            if os.path.exists(settings.UPLOAD_DIR):
                for filename in os.listdir(settings.UPLOAD_DIR):
                    file_path = os.path.join(settings.UPLOAD_DIR, filename)
                    if os.path.isfile(file_path):
                        try:
                            os.remove(file_path)
                            temp_files_removed += 1
                        except Exception as e:
                            logger.warning(f"Failed to remove file {filename}: {str(e)}")
            
            # Clear any caches
            # This would be implemented based on your caching strategy
            
            logger.info(f"Emergency cleanup completed: {temp_files_removed} files removed")
            
        except Exception as e:
            logger.error(f"Emergency cleanup failed: {str(e)}")


# Global resource manager instance
resource_manager = ResourceManager() 