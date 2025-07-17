"""
Response models for the medical vector database API.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from .document import Document


class SearchResult(BaseModel):
    """Search result model."""
    document: Document = Field(..., description="Document data")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score")
    matched_entities: List[str] = Field(default_factory=list, description="Matched entities")
    highlighted_text: Optional[str] = Field(None, description="Highlighted text")


class SearchResponse(BaseModel):
    """Search response model."""
    success: bool = Field(..., description="Operation success status")
    query: str = Field(..., description="Search query")
    results: List[SearchResult] = Field(..., description="Search results")
    total_results: int = Field(..., ge=0, description="Total number of results")
    processing_time: float = Field(..., ge=0.0, description="Processing time in seconds")
    message: str = Field(..., description="Response message")


class ProcessingResponse(BaseModel):
    """Document processing response model."""
    success: bool = Field(..., description="Operation success status")
    document_id: str = Field(..., description="Document ID")
    status: str = Field(..., description="Processing status")
    processing_time: float = Field(..., ge=0.0, description="Processing time in seconds")
    entities_found: int = Field(..., ge=0, description="Number of entities found")
    message: str = Field(..., description="Response message")


class DocumentResponse(BaseModel):
    """Document response model."""
    success: bool = Field(..., description="Operation success status")
    document: Optional[Document] = Field(None, description="Document data")
    message: str = Field(..., description="Response message")
    processing_time: Optional[float] = Field(None, ge=0.0, description="Processing time in seconds")


class DocumentListResponse(BaseModel):
    """Document list response model."""
    documents: List[Document] = Field(..., description="List of documents")
    total: int = Field(..., ge=0, description="Total number of documents")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=1000, description="Page size")


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    services: Dict[str, str] = Field(..., description="Service statuses")
    timestamp: str = Field(..., description="Timestamp")


class StatsResponse(BaseModel):
    """Statistics response model."""
    success: bool = Field(..., description="Operation success status")
    statistics: Dict[str, Any] = Field(..., description="System statistics")
    message: str = Field(..., description="Response message")


class ErrorResponse(BaseModel):
    """Error response model."""
    success: bool = Field(False, description="Operation success status")
    error: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Error details")
    timestamp: str = Field(..., description="Error timestamp")


# Bulk Operations Response Models

class BulkOperationResult(BaseModel):
    """Individual result for bulk operations."""
    id: str = Field(..., description="Document ID")
    success: bool = Field(..., description="Operation success status")
    message: str = Field(..., description="Result message")
    processing_time: Optional[float] = Field(None, ge=0.0, description="Processing time")
    error: Optional[str] = Field(None, description="Error message if failed")


class BulkUploadResponse(BaseModel):
    """Bulk upload response model."""
    success: bool = Field(..., description="Overall operation success status")
    total_files: int = Field(..., ge=0, description="Total number of files")
    successful: int = Field(..., ge=0, description="Number of successful uploads")
    failed: int = Field(..., ge=0, description="Number of failed uploads")
    processing_time: float = Field(..., ge=0.0, description="Total processing time")
    results: List[BulkOperationResult] = Field(..., description="Individual results")
    message: str = Field(..., description="Response message")
    batch_id: Optional[str] = Field(None, description="Batch processing ID")


class BulkSearchResult(BaseModel):
    """Bulk search result model."""
    query: str = Field(..., description="Search query")
    results: List[SearchResult] = Field(..., description="Search results")
    total_results: int = Field(..., ge=0, description="Total results for this query")
    processing_time: float = Field(..., ge=0.0, description="Processing time for this query")


class BulkSearchResponse(BaseModel):
    """Bulk search response model."""
    success: bool = Field(..., description="Overall operation success status")
    total_queries: int = Field(..., ge=0, description="Total number of queries")
    successful_queries: int = Field(..., ge=0, description="Number of successful queries")
    failed_queries: int = Field(..., ge=0, description="Number of failed queries")
    total_processing_time: float = Field(..., ge=0.0, description="Total processing time")
    results: List[BulkSearchResult] = Field(..., description="Search results for each query")
    message: str = Field(..., description="Response message")


class BulkDeleteResponse(BaseModel):
    """Bulk delete response model."""
    success: bool = Field(..., description="Overall operation success status")
    total_documents: int = Field(..., ge=0, description="Total number of documents")
    successful: int = Field(..., ge=0, description="Number of successful deletions")
    failed: int = Field(..., ge=0, description="Number of failed deletions")
    processing_time: float = Field(..., ge=0.0, description="Total processing time")
    results: List[BulkOperationResult] = Field(..., description="Individual results")
    message: str = Field(..., description="Response message")


class BulkUpdateRequest(BaseModel):
    """Bulk update request model."""
    document_ids: List[str] = Field(..., min_items=1, max_items=100, description="Document IDs to update")
    metadata_updates: Dict[str, Any] = Field(..., description="Metadata updates to apply")
    status_filter: Optional[str] = Field(None, description="Only update documents with this status")


class BulkUpdateResponse(BaseModel):
    """Bulk update response model."""
    success: bool = Field(..., description="Overall operation success status")
    total_documents: int = Field(..., ge=0, description="Total number of documents")
    successful: int = Field(..., ge=0, description="Number of successful updates")
    failed: int = Field(..., ge=0, description="Number of failed updates")
    processing_time: float = Field(..., ge=0.0, description="Total processing time")
    results: List[BulkOperationResult] = Field(..., description="Individual results")
    message: str = Field(..., description="Response message")


class BulkExportRequest(BaseModel):
    """Bulk export request model."""
    document_ids: Optional[List[str]] = Field(None, description="Specific document IDs to export")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filter criteria")
    format: str = Field("json", description="Export format (json, csv, xml)")
    include_entities: bool = Field(True, description="Include extracted entities")
    include_embeddings: bool = Field(False, description="Include document embeddings")


class BulkExportResponse(BaseModel):
    """Bulk export response model."""
    success: bool = Field(..., description="Operation success status")
    total_documents: int = Field(..., ge=0, description="Total number of documents exported")
    export_format: str = Field(..., description="Export format used")
    file_size: Optional[int] = Field(None, description="Export file size in bytes")
    download_url: Optional[str] = Field(None, description="Download URL for export file")
    processing_time: float = Field(..., ge=0.0, description="Processing time")
    message: str = Field(..., description="Response message")


class BulkStatusResponse(BaseModel):
    """Bulk operation status response model."""
    batch_id: str = Field(..., description="Batch processing ID")
    status: str = Field(..., description="Batch status")
    progress: float = Field(..., ge=0.0, le=100.0, description="Progress percentage")
    total_items: int = Field(..., ge=0, description="Total number of items")
    completed_items: int = Field(..., ge=0, description="Number of completed items")
    failed_items: int = Field(..., ge=0, description="Number of failed items")
    start_time: str = Field(..., description="Batch start time")
    estimated_completion: Optional[str] = Field(None, description="Estimated completion time")
    results: Optional[List[BulkOperationResult]] = Field(None, description="Current results") 