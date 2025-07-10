"""
FastAPI routes for the medical vector database API.
"""

import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from loguru import logger

from ..config import settings
from ..models.document import Document, DocumentResponse, DocumentListResponse
from ..models.response import SearchResponse, ProcessingResponse, ErrorResponse, HealthResponse, StatsResponse
from ..services.document_service import DocumentService

router = APIRouter(prefix="/api/v1", tags=["medical-documents"])

# Global document service instance
document_service = DocumentService()


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
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
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
        
        # Parse metadata
        parsed_metadata = None
        if metadata:
            try:
                import json
                parsed_metadata = json.loads(metadata)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON metadata")
        
        # Process document
        document = document_service.process_document(temp_path, parsed_metadata)
        
        return ProcessingResponse(
            success=True,
            document_id=document.id,
            status=document.status.value,
            processing_time=document.processing_time or 0.0,
            entities_found=document.entity_count,
            message=f"Document processed successfully. Found {document.entity_count} entities."
        )
        
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=SearchResponse)
async def search_documents(
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
        start_time = time.time()
        
        # Perform search
        results = document_service.search_documents(query, n_results)
        
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
            query=query,
            results=search_results,
            total_results=len(search_results),
            processing_time=processing_time,
            message=f"Found {len(search_results)} documents"
        )
        
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
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
        documents = document_service.get_all_documents(limit + offset)
        documents = documents[offset:offset + limit]
        
        return DocumentListResponse(
            documents=documents,
            total=len(documents),
            page=offset // limit + 1,
            page_size=limit
        )
        
    except Exception as e:
        logger.error(f"Failed to list documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str):
    """
    Get a specific document by ID.
    
    Args:
        document_id: Document ID
        
    Returns:
        Document details
    """
    try:
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
    except Exception as e:
        logger.error(f"Failed to get document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document.
    
    Args:
        document_id: Document ID to delete
        
    Returns:
        Success response
    """
    try:
        success = document_service.delete_document(document_id)
        if not success:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return {"success": True, "message": "Document deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document {document_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=StatsResponse)
async def get_statistics():
    """
    Get processing statistics.
    
    Returns:
        Statistics about the system
    """
    try:
        stats = document_service.get_statistics()
        
        return StatsResponse(
            total_documents=stats["total_documents"],
            processed_documents=stats["completed_documents"],
            failed_documents=stats["failed_documents"],
            total_entities=stats["total_entities"],
            entity_types=stats["entity_types"],
            average_processing_time=stats["average_processing_time"]
        )
        
    except Exception as e:
        logger.error(f"Failed to get statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-upload")
async def batch_upload_documents(files: List[UploadFile] = File(...)):
    """
    Upload and process multiple documents in batch.
    
    Args:
        files: List of files to upload
        
    Returns:
        Batch processing results
    """
    try:
        results = []
        
        for file in files:
            try:
                # Validate file
                if not file.filename:
                    continue
                
                # Check file size
                if file.size and file.size > settings.MAX_FILE_SIZE:
                    results.append({
                        "filename": file.filename,
                        "success": False,
                        "error": "File too large"
                    })
                    continue
                
                # Check file extension
                file_ext = os.path.splitext(file.filename)[1].lower()
                if file_ext not in settings.ALLOWED_EXTENSIONS:
                    results.append({
                        "filename": file.filename,
                        "success": False,
                        "error": "Unsupported file type"
                    })
                    continue
                
                # Save file temporarily
                temp_path = os.path.join(settings.UPLOAD_DIR, file.filename)
                with open(temp_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                # Process document
                document = document_service.process_document(temp_path)
                
                results.append({
                    "filename": file.filename,
                    "success": True,
                    "document_id": document.id,
                    "entities_found": document.entity_count
                })
                
            except Exception as e:
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "success": True,
            "results": results,
            "total_files": len(files),
            "successful": len([r for r in results if r["success"]]),
            "failed": len([r for r in results if not r["success"]])
        }
        
    except Exception as e:
        logger.error(f"Batch upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Import necessary modules
import time
from datetime import datetime
from ..models.response import SearchResult 