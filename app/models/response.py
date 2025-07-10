"""
API response models for the medical vector database.
"""

from typing import List, Optional, Any, Dict
from pydantic import BaseModel
from .document import Document, Entity


class SearchResult(BaseModel):
    """Individual search result."""
    document: Document
    similarity_score: float
    matched_entities: List[Entity] = []
    highlighted_text: Optional[str] = None


class SearchResponse(BaseModel):
    """Response model for search operations."""
    success: bool
    query: str
    results: List[SearchResult]
    total_results: int
    processing_time: float
    message: str


class ProcessingResponse(BaseModel):
    """Response model for document processing."""
    success: bool
    document_id: str
    status: str
    processing_time: float
    entities_found: int
    message: str
    error: Optional[str] = None


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = False
    error: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    services: Dict[str, str]
    timestamp: str


class StatsResponse(BaseModel):
    """Statistics response."""
    total_documents: int
    processed_documents: int
    failed_documents: int
    total_entities: int
    entity_types: Dict[str, int]
    average_processing_time: float 