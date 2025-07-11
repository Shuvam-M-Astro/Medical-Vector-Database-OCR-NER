"""
Document data models for the medical vector database.
"""

from datetime import datetime
from typing import List, Dict, Optional, Any, Union
from pydantic import BaseModel, Field, validator, root_validator
from enum import Enum
import re


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
    text: str = Field(..., min_length=1, max_length=500, description="Entity text")
    entity_type: EntityType = Field(..., description="Type of medical entity")
    start: int = Field(..., ge=0, description="Start position in text")
    end: int = Field(..., ge=0, description="End position in text")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    
    @validator('text')
    def validate_text(cls, v):
        """Validate entity text."""
        if not v or not v.strip():
            raise ValueError("Entity text cannot be empty")
        
        # Remove control characters
        cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', v)
        if cleaned != v:
            raise ValueError("Entity text contains invalid control characters")
        
        return v.strip()
    
    @validator('end')
    def validate_end_position(cls, v, values):
        """Validate end position is greater than start position."""
        if 'start' in values and v <= values['start']:
            raise ValueError("End position must be greater than start position")
        return v
    
    @validator('confidence')
    def validate_confidence(cls, v):
        """Validate confidence score."""
        if not isinstance(v, (int, float)):
            raise ValueError("Confidence must be a number")
        return float(v)


class DocumentCreate(BaseModel):
    """Model for creating a new document."""
    filename: str = Field(..., min_length=1, max_length=255, description="Document filename")
    file_type: str = Field(..., min_length=1, max_length=10, description="File type/extension")
    file_size: int = Field(..., gt=0, le=50*1024*1024, description="File size in bytes")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")
    
    @validator('filename')
    def validate_filename(cls, v):
        """Validate filename."""
        if not v or not v.strip():
            raise ValueError("Filename cannot be empty")
        
        # Check for malicious patterns
        malicious_patterns = [
            r'\.\./',  # Directory traversal
            r'\.\.\\',  # Windows directory traversal
            r'<script',  # XSS
            r'javascript:',  # XSS
            r'data:',  # Data URI
        ]
        
        for pattern in malicious_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError("Filename contains potentially malicious patterns")
        
        return v.strip()
    
    @validator('file_type')
    def validate_file_type(cls, v):
        """Validate file type."""
        allowed_types = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.bmp']
        if v.lower() not in allowed_types:
            raise ValueError(f"Unsupported file type: {v}. Allowed: {', '.join(allowed_types)}")
        return v.lower()
    
    @validator('metadata')
    def validate_metadata(cls, v):
        """Validate metadata."""
        if v is None:
            return v
        
        if not isinstance(v, dict):
            raise ValueError("Metadata must be a dictionary")
        
        # Limit metadata size
        if len(v) > 50:
            raise ValueError("Too many metadata keys (max: 50)")
        
        validated_metadata = {}
        for key, value in v.items():
            if not isinstance(key, str):
                raise ValueError("Metadata keys must be strings")
            
            if len(key) > 100:
                raise ValueError("Metadata key too long (max: 100 characters)")
            
            # Validate value types
            if isinstance(value, (str, int, float, bool)):
                if isinstance(value, str) and len(value) > 1000:
                    raise ValueError("Metadata string value too long (max: 1000 characters)")
                validated_metadata[key] = value
            else:
                raise ValueError(f"Unsupported metadata value type: {type(value)}")
        
        return validated_metadata


class Document(BaseModel):
    """Document model with all processing results."""
    id: str = Field(..., min_length=1, max_length=100, description="Document ID")
    filename: str = Field(..., min_length=1, max_length=255, description="Document filename")
    file_type: str = Field(..., min_length=1, max_length=10, description="File type")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    status: DocumentStatus = Field(..., description="Processing status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    # OCR Results
    extracted_text: Optional[str] = Field(None, max_length=1000000, description="Extracted text from OCR")
    ocr_confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="OCR confidence score")
    
    # NER Results
    entities: List[Entity] = Field(default_factory=list, description="Extracted entities")
    entity_count: int = Field(0, ge=0, description="Number of entities")
    
    # Vector Database
    vector_id: Optional[str] = Field(None, max_length=100, description="Vector database ID")
    embedding: Optional[List[float]] = Field(None, description="Document embedding vector")
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = Field(None, description="Document metadata")
    processing_time: Optional[float] = Field(None, ge=0.0, le=3600.0, description="Processing time in seconds")
    error_message: Optional[str] = Field(None, max_length=1000, description="Error message if processing failed")
    
    @validator('id')
    def validate_id(cls, v):
        """Validate document ID."""
        if not v or not v.strip():
            raise ValueError("Document ID cannot be empty")
        
        # Check for valid characters
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Document ID contains invalid characters")
        
        return v.strip()
    
    @validator('extracted_text')
    def validate_extracted_text(cls, v):
        """Validate extracted text."""
        if v is None:
            return v
        
        # Remove null bytes and control characters
        cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', v)
        if cleaned != v:
            raise ValueError("Extracted text contains invalid control characters")
        
        return cleaned
    
    @validator('embedding')
    def validate_embedding(cls, v):
        """Validate embedding vector."""
        if v is None:
            return v
        
        if not isinstance(v, list):
            raise ValueError("Embedding must be a list")
        
        if len(v) == 0:
            raise ValueError("Embedding cannot be empty")
        
        if len(v) > 10000:  # Reasonable limit for embedding dimensions
            raise ValueError("Embedding vector too large")
        
        # Validate all elements are numbers
        for i, val in enumerate(v):
            if not isinstance(val, (int, float)):
                raise ValueError(f"Embedding element {i} must be a number")
        
        return v
    
    @root_validator
    def validate_consistency(cls, values):
        """Validate document consistency."""
        # Check entity count consistency
        entities = values.get('entities', [])
        entity_count = values.get('entity_count', 0)
        
        if len(entities) != entity_count:
            raise ValueError(f"Entity count mismatch: recorded {entity_count}, actual {len(entities)}")
        
        # Check status consistency
        status = values.get('status')
        extracted_text = values.get('extracted_text')
        error_message = values.get('error_message')
        
        if status == DocumentStatus.COMPLETED:
            if not extracted_text:
                raise ValueError("Completed document must have extracted text")
        elif status == DocumentStatus.FAILED:
            if not error_message:
                raise ValueError("Failed document must have error message")
        
        # Check timestamps
        created_at = values.get('created_at')
        updated_at = values.get('updated_at')
        
        if created_at and updated_at and updated_at < created_at:
            raise ValueError("Updated timestamp cannot be before created timestamp")
        
        return values
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        # Allow extra fields for backward compatibility
        extra = "allow"


class DocumentResponse(BaseModel):
    """Response model for document operations."""
    success: bool = Field(..., description="Operation success status")
    document: Optional[Document] = Field(None, description="Document data")
    message: str = Field(..., min_length=1, max_length=1000, description="Response message")
    processing_time: Optional[float] = Field(None, ge=0.0, description="Processing time in seconds")
    
    @validator('message')
    def validate_message(cls, v):
        """Validate response message."""
        if not v or not v.strip():
            raise ValueError("Response message cannot be empty")
        return v.strip()


class DocumentListResponse(BaseModel):
    """Response model for document listing."""
    documents: List[Document] = Field(..., description="List of documents")
    total: int = Field(..., ge=0, description="Total number of documents")
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, le=1000, description="Page size")
    
    @validator('total')
    def validate_total_consistency(cls, v, values):
        """Validate total count consistency."""
        documents = values.get('documents', [])
        if v < len(documents):
            raise ValueError("Total count cannot be less than number of documents")
        return v 