"""
Document data models for the medical vector database.
"""

from datetime import datetime
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from enum import Enum


class DocumentStatus(str, Enum):
    """Document processing status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class EntityType(str, Enum):
    """Medical entity types."""
    MEDICATION = "MEDICATION"
    PROCEDURE = "PROCEDURE"
    DIAGNOSIS = "DIAGNOSIS"
    BODY_PART = "BODY_PART"
    ORGANIZATION = "ORGANIZATION"
    PERSON = "PERSON"
    DATE = "DATE"
    MONEY = "MONEY"
    LOCATION = "LOCATION"
    QUANTITY = "QUANTITY"


class Entity(BaseModel):
    """Named entity extracted from document."""
    text: str
    entity_type: EntityType
    start: int
    end: int
    confidence: float = Field(ge=0.0, le=1.0)


class DocumentCreate(BaseModel):
    """Model for creating a new document."""
    filename: str
    file_type: str
    file_size: int
    metadata: Optional[Dict[str, Any]] = None


class Document(BaseModel):
    """Document model with all processing results."""
    id: str
    filename: str
    file_type: str
    file_size: int
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime
    
    # OCR Results
    extracted_text: Optional[str] = None
    ocr_confidence: Optional[float] = None
    
    # NER Results
    entities: List[Entity] = []
    entity_count: int = 0
    
    # Vector Database
    vector_id: Optional[str] = None
    embedding: Optional[List[float]] = None
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = None
    processing_time: Optional[float] = None
    error_message: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DocumentResponse(BaseModel):
    """Response model for document operations."""
    success: bool
    document: Optional[Document] = None
    message: str
    processing_time: Optional[float] = None


class DocumentListResponse(BaseModel):
    """Response model for document listing."""
    documents: List[Document]
    total: int
    page: int
    page_size: int 