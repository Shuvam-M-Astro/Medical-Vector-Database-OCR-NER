"""
API layer for the medical vector database application.
"""

from .routes import router
from .middleware import setup_middleware

__all__ = ["router", "setup_middleware"] 