"""
FastAPI routes for the medical vector database API.
"""

import os
import shutil
import time
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query, Request
from fastapi.responses import JSONResponse
from loguru import logger

from ..config import settings
from ..models.document import Document, DocumentResponse, DocumentListResponse, DocumentCreate
from ..models.response import SearchResponse, ProcessingResponse, ErrorResponse, HealthResponse, StatsResponse, SearchResult
from ..services.document_service import DocumentService
from ..utils.validation import (
    FileValidator, InputValidator, DataQualityValidator, 
    BusinessLogicValidator, rate_limiter, ValidationError
)

router = APIRouter(prefix="/api/v1", tags=["medical-documents"])

# Global document service instance
document_service = DocumentService()


def get_client_id(request: Request) -> str:
    """Extract client ID from request."""
    # Use IP address as client ID (in production, use proper authentication)
    client_ip = request.client.host if request.client else "unknown"
    return client_ip


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        services={
            "ocr": "available",
            "ner": "available",
            "vector_db": "available"
        },
        timestamp=datetime.now().isoformat()
    )


@router.post("/upload", response_model=ProcessingResponse)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    metadata: Optional[str] = Query(None, description="JSON metadata string")
):
    """
    Upload and process a medical document.
    
    Args:
        file: Document file to upload
        metadata: Optional JSON metadata string
        
    Returns:
        Processing response with document details
    """
    start_time = time.time()
    
    try:
        # Rate limiting
        client_id = get_client_id(request)
        is_allowed, rate_limit_error = rate_limiter.check_rate_limit(client_id)
        if not is_allowed:
            raise HTTPException(status_code=429, detail=rate_limit_error)
        
        # Validate file upload
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Validate filename
        try:
            InputValidator.sanitize_string(file.filename, max_length=255)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Invalid filename: {str(e)}")
        
        # Check file size
        if file.size and file.size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413, 
                detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE} bytes"
            )
        
        # Check file extension
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type. Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        
        # Save file temporarily
        temp_path = os.path.join(settings.UPLOAD_DIR, file.filename)
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Security validation
        is_valid, security_error = FileValidator.validate_file_security(temp_path)
        if not is_valid:
            # Clean up temp file
            try:
                os.remove(temp_path)
            except:
                pass
            raise HTTPException(status_code=400, detail=f"File validation failed: {security_error}")
        
        # Parse and validate metadata
        parsed_metadata = None
        if metadata:
            try:
                import json
                raw_metadata = json.loads(metadata)
                parsed_metadata = InputValidator.validate_metadata(raw_metadata)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON metadata")
            except ValidationError as e:
                raise HTTPException(status_code=400, detail=f"Invalid metadata: {str(e)}")
        
        # Process document
        document = document_service.process_document(temp_path, parsed_metadata)
        
        # Validate processing results
        is_valid, quality_warnings = DataQualityValidator.validate_ocr_result(
            document.extracted_text or "", 
            document.ocr_confidence or 0.0
        )
        
        if document.entities:
            ner_valid, ner_warnings = DataQualityValidator.validate_ner_result(
                [entity.dict() for entity in document.entities]
            )
            if not ner_valid:
                quality_warnings += f"; {ner_warnings}"
        
        processing_time = time.time() - start_time
        
        return ProcessingResponse(
            success=True,
            document_id=document.id,
            status=document.status.value,
            processing_time=processing_time,
            entities_found=document.entity_count,
            message=f"Document processed successfully. Found {document.entity_count} entities." + 
                   (f" Warnings: {quality_warnings}" if quality_warnings else "")
        )
        
    except HTTPException:
        raise
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/search", response_model=SearchResponse)
async def search_documents(
    request: Request,
    query: str = Query(..., description="Search query"),
    n_results: int = Query(10, ge=1, le=100, description="Number of results to return")
):
    """
    Search documents by text query.
    
    Args:
        query: Search query
        n_results: Number of results to return
        
    Returns:
        Search results
    """
    try:
        # Rate limiting
        client_id = get_client_id(request)
        is_allowed, rate_limit_error = rate_limiter.check_rate_limit(client_id)
        if not is_allowed:
            raise HTTPException(status_code=429, detail=rate_limit_error)
        
        # Validate search parameters
        try:
            validated_query = InputValidator.validate_search_query(query)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Invalid search query: {str(e)}")
        
        # Business logic validation
        is_valid, errors = BusinessLogicValidator.validate_search_parameters(
            validated_query, n_results, max_results=100
        )
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid search parameters: {'; '.join(errors)}")
        
        start_time = time.time()
        
        # Perform search
        results = document_service.search_documents(validated_query, n_results)
        
        # Convert to response format
        search_results = []
        for document, similarity in results:
            search_result = SearchResult(
                document=document,
                similarity_score=similarity,
                matched_entities=[],  # Could be enhanced to show matched entities
                highlighted_text=None  # Could be enhanced to show highlighted text
            )
            search_results.append(search_result)
        
        processing_time = time.time() - start_time
        
        return SearchResponse(
            success=True,
            query=validated_query,
            results=search_results,
            total_results=len(search_results),
            processing_time=processing_time,
            message=f"Found {len(search_results)} documents"
        )
        
    except HTTPException:
        raise
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    request: Request,
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of documents to return"),
    offset: int = Query(0, ge=0, description="Number of documents to skip")
):
    """
    List all documents.
    
    Args:
        limit: Maximum number of documents to return
        offset: Number of documents to skip
        
    Returns:
        List of documents
    """
    try:
        # Rate limiting
        client_id = get_client_id(request)
        is_allowed, rate_limit_error = rate_limiter.check_rate_limit(client_id)
        if not is_allowed:
            raise HTTPException(status_code=429, detail=rate_limit_error)
        
        # Validate pagination parameters
        if offset < 0:
            raise HTTPException(status_code=400, detail="Offset cannot be negative")
        
        if limit > 1000:
            raise HTTPException(status_code=400, detail="Limit too high (max: 1000)")
        
        documents = document_service.get_all_documents(limit + offset)
        documents = documents[offset:offset + limit]
        
        return DocumentListResponse(
            documents=documents,
            total=len(documents),
            page=offset // limit + 1,
            page_size=limit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list documents: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    request: Request,
    document_id: str
):
    """
    Get a specific document by ID.
    
    Args:
        document_id: Document ID
        
    Returns:
        Document details
    """
    try:
        # Rate limiting
        client_id = get_client_id(request)
        is_allowed, rate_limit_error = rate_limiter.check_rate_limit(client_id)
        if not is_allowed:
            raise HTTPException(status_code=429, detail=rate_limit_error)
        
        # Validate document ID
        try:
            InputValidator.sanitize_string(document_id, max_length=100)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Invalid document ID: {str(e)}")
        
        document = document_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return DocumentResponse(
            success=True,
            document=document,
            message="Document retrieved successfully"
        )
        
    except HTTPException:
        raise
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/documents/{document_id}")
async def delete_document(
    request: Request,
    document_id: str
):
    """
    Delete a document.
    
    Args:
        document_id: Document ID to delete
        
    Returns:
        Success response
    """
    try:
        # Rate limiting
        client_id = get_client_id(request)
        is_allowed, rate_limit_error = rate_limiter.check_rate_limit(client_id)
        if not is_allowed:
            raise HTTPException(status_code=429, detail=rate_limit_error)
        
        # Validate document ID
        try:
            InputValidator.sanitize_string(document_id, max_length=100)
        except ValidationError as e:
            raise HTTPException(status_code=400, detail=f"Invalid document ID: {str(e)}")
        
        success = document_service.delete_document(document_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"success": True, "message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to delete document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/stats", response_model=StatsResponse)
async def get_statistics(request: Request):
    """
    Get processing statistics.
    
    Returns:
        Statistics about the system
    """
    try:
        # Rate limiting
        client_id = get_client_id(request)
        is_allowed, rate_limit_error = rate_limiter.check_rate_limit(client_id)
        if not is_allowed:
            raise HTTPException(status_code=429, detail=rate_limit_error)
        
        stats = document_service.get_statistics()
        
        return StatsResponse(
            total_documents=stats["total_documents"],
            processed_documents=stats["completed_documents"],
            failed_documents=stats["failed_documents"],
            total_entities=stats["total_entities"],
            entity_types=stats["entity_types"],
            average_processing_time=stats["average_processing_time"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/batch-upload")
async def batch_upload_documents(
    request: Request,
    files: List[UploadFile] = File(...)
):
    """
    Upload and process multiple documents in batch.
    
    Args:
        files: List of document files to upload
        
    Returns:
        Batch processing results
    """
    try:
        # Rate limiting
        client_id = get_client_id(request)
        is_allowed, rate_limit_error = rate_limiter.check_rate_limit(client_id)
        if not is_allowed:
            raise HTTPException(status_code=429, detail=rate_limit_error)
        
        # Validate batch size
        if len(files) > 10:
            raise HTTPException(status_code=400, detail="Too many files (max: 10)")
        
        if len(files) == 0:
            raise HTTPException(status_code=400, detail="No files provided")
        
        results = []
        
        for file in files:
            try:
                # Validate individual file
                if not file.filename:
                    results.append({
                        "filename": "unknown",
                        "success": False,
                        "error": "No filename provided"
                    })
                    continue
                
                # Validate filename
                try:
                    InputValidator.sanitize_string(file.filename, max_length=255)
                except ValidationError as e:
                    results.append({
                        "filename": file.filename,
                        "success": False,
                        "error": f"Invalid filename: {str(e)}"
                    })
                    continue
                
                # Check file size
                if file.size and file.size > settings.MAX_FILE_SIZE:
                    results.append({
                        "filename": file.filename,
                        "success": False,
                        "error": f"File too large: {file.size} bytes"
                    })
                    continue
                
                # Save and process file
                temp_path = os.path.join(settings.UPLOAD_DIR, file.filename)
                with open(temp_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                # Security validation
                is_valid, security_error = FileValidator.validate_file_security(temp_path)
                if not is_valid:
                    try:
                        os.remove(temp_path)
                    except:
                        pass
                    results.append({
                        "filename": file.filename,
                        "success": False,
                        "error": f"File validation failed: {security_error}"
                    })
                    continue
                
                # Process document
                document = document_service.process_document(temp_path)
                
                results.append({
                    "filename": file.filename,
                    "success": True,
                    "document_id": document.id,
                    "entities_found": document.entity_count,
                    "processing_time": document.processing_time
                })
                
            except Exception as e:
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "success": True,
            "total_files": len(files),
            "processed_files": len([r for r in results if r["success"]]),
            "failed_files": len([r for r in results if not r["success"]]),
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error") 