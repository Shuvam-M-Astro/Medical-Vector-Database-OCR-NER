"""
Retry utilities with exponential backoff and circuit breaker patterns.
"""

import asyncio
import time
import random
from typing import Callable, Any, Optional, Type, Union, List
from functools import wraps
from enum import Enum
from loguru import logger

from ..config import settings


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Circuit breaker pattern implementation."""
    
    def __init__(
        self,
        failure_threshold: int = settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
        recovery_timeout: int = settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT,
        expected_exception: bool = settings.CIRCUIT_BREAKER_EXPECTED_EXCEPTION
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self._lock = asyncio.Lock()
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        async with self._lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    logger.info("Circuit breaker transitioning to HALF_OPEN")
                else:
                    raise Exception("Circuit breaker is OPEN")
            
            try:
                result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
                self._on_success()
                return result
            except Exception as e:
                self._on_failure()
                raise
    
    def _on_success(self):
        """Handle successful execution."""
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            logger.info("Circuit breaker reset to CLOSED")
    
    def _on_failure(self):
        """Handle failed execution."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if not self.last_failure_time:
            return False
        return time.time() - self.last_failure_time >= self.recovery_timeout


class RetryHandler:
    """Retry handler with exponential backoff."""
    
    def __init__(
        self,
        max_attempts: int = settings.MAX_RETRY_ATTEMPTS,
        base_delay: float = settings.RETRY_BASE_DELAY,
        max_delay: float = settings.RETRY_MAX_DELAY,
        exponential_base: float = settings.RETRY_EXPONENTIAL_BASE,
        retryable_exceptions: Optional[List[Type[Exception]]] = None
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retryable_exceptions = retryable_exceptions or [Exception]
    
    async def execute(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with retry logic."""
        last_exception = None
        
        for attempt in range(self.max_attempts):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
                    
            except tuple(self.retryable_exceptions) as e:
                last_exception = e
                
                if attempt == self.max_attempts - 1:
                    logger.error(f"Final retry attempt failed: {str(e)}")
                    raise
                
                delay = self._calculate_delay(attempt)
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay:.2f}s")
                
                await asyncio.sleep(delay)
        
        raise last_exception
    
    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter."""
        delay = min(
            self.base_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        # Add jitter to prevent thundering herd
        jitter = random.uniform(0, delay * 0.1)
        return delay + jitter


def with_retry(
    max_attempts: int = settings.MAX_RETRY_ATTEMPTS,
    base_delay: float = settings.RETRY_BASE_DELAY,
    max_delay: float = settings.RETRY_MAX_DELAY,
    retryable_exceptions: Optional[List[Type[Exception]]] = None
):
    """Decorator for retry functionality."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            handler = RetryHandler(
                max_attempts=max_attempts,
                base_delay=base_delay,
                max_delay=max_delay,
                retryable_exceptions=retryable_exceptions
            )
            return await handler.execute(func, *args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            handler = RetryHandler(
                max_attempts=max_attempts,
                base_delay=base_delay,
                max_delay=max_delay,
                retryable_exceptions=retryable_exceptions
            )
            return asyncio.run(handler.execute(func, *args, **kwargs))
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def with_circuit_breaker(
    failure_threshold: int = settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
    recovery_timeout: int = settings.CIRCUIT_BREAKER_RECOVERY_TIMEOUT
):
    """Decorator for circuit breaker functionality."""
    def decorator(func: Callable) -> Callable:
        circuit_breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout
        )
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await circuit_breaker.call(func, *args, **kwargs)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return asyncio.run(circuit_breaker.call(func, *args, **kwargs))
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Global circuit breakers for different services
ocr_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
ner_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=30)
vector_circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60) 