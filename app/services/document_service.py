"""
Main document processing service that orchestrates OCR, NER, and vector database operations.
"""

import os
import time
import uuid
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
from loguru import logger

from ..config import settings
from ..models.document import Document, DocumentStatus, DocumentCreate
from .ocr_service import OCRService
from .ner_service import NERService
from .vector_service import VectorService


class DocumentService:
    """Main service for processing medical documents."""
    
    def __init__(self):
        """Initialize document service."""
        self.ocr_service = OCRService()
        self.ner_service = NERService()
        self.vector_service = VectorService()
        
        # In-memory document storage (in production, use a proper database)
        self.documents: Dict[str, Document] = {}
        
        # Performance optimizations
        self._executor = ThreadPoolExecutor(max_workers=settings.MAX_WORKERS)
        self._cache = {}
        self._cache_ttl = 3600  # 1 hour cache TTL
        
        logger.info("Document service initialized")
    
    async def process_document(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> Document:
        """
        Process a document through the complete pipeline asynchronously.
        
        Args:
            file_path: Path to the document file
            metadata: Optional metadata for the document
            
        Returns:
            Processed document
        """
        start_time = time.time()
        
        try:
            # Check cache first
            cache_key = f"{file_path}_{hash(str(metadata))}"
            if cache_key in self._cache:
                cached_doc = self._cache[cache_key]
                if time.time() - cached_doc.get('timestamp', 0) < self._cache_ttl:
                    logger.info(f"Returning cached result for {file_path}")
                    return cached_doc['document']
            
            # Validate file
            if not self.ocr_service.validate_file(file_path):
                raise ValueError(f"Unsupported file format: {file_path}")
            
            # Create document record
            document = self._create_document_record(file_path, metadata)
            document.status = DocumentStatus.PROCESSING
            self.documents[document.id] = document
            
            logger.info(f"Starting processing for document: {document.id}")
            
            # Step 1: OCR Processing (async)
            extracted_text, ocr_confidence = await self._perform_ocr_async(file_path)
            document.extracted_text = extracted_text
            document.ocr_confidence = ocr_confidence
            
            logger.info(f"OCR completed for {document.id}: {len(extracted_text)} characters, {ocr_confidence:.2f} confidence")
            
            # Step 2: NER Processing (async)
            entities = await self._perform_ner_async(extracted_text)
            document.entities = entities
            document.entity_count = len(entities)
            
            logger.info(f"NER completed for {document.id}: {len(entities)} entities found")
            
            # Step 3: Vector Database Storage (async)
            vector_id = await self._add_to_vector_db_async(document)
            document.vector_id = vector_id
            
            # Update document status
            document.status = DocumentStatus.COMPLETED
            document.updated_at = datetime.now()
            document.processing_time = time.time() - start_time
            
            # Cache the result
            self._cache[cache_key] = {
                'document': document,
                'timestamp': time.time()
            }
            
            logger.info(f"Document {document.id} processed successfully in {document.processing_time:.2f}s")
            
            return document
            
        except Exception as e:
            # Update document with error
            if 'document' in locals():
                document.status = DocumentStatus.FAILED
                document.error_message = str(e)
                document.updated_at = datetime.now()
                document.processing_time = time.time() - start_time
            
            logger.error(f"Document processing failed: {str(e)}")
            raise
    
    async def process_documents_batch(self, file_paths: List[str]) -> List[Document]:
        """
        Process multiple documents in batch asynchronously.
        
        Args:
            file_paths: List of file paths to process
            
        Returns:
            List of processed documents
        """
        # Create tasks for concurrent processing
        tasks = [self.process_document(file_path) for file_path in file_paths]
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to process {file_paths[i]}: {str(result)}")
                # Create failed document record
                failed_doc = self._create_document_record(file_paths[i])
                failed_doc.status = DocumentStatus.FAILED
                failed_doc.error_message = str(result)
                failed_doc.updated_at = datetime.now()
                self.documents[failed_doc.id] = failed_doc
                processed_results.append(failed_doc)
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def search_documents(self, query: str, n_results: int = 10) -> List[tuple]:
        """
        Search documents by text query with caching.
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of (document, similarity_score) tuples
        """
        # Check cache for search results
        cache_key = f"search_{hash(query)}_{n_results}"
        if cache_key in self._cache:
            cached_result = self._cache[cache_key]
            if time.time() - cached_result.get('timestamp', 0) < self._cache_ttl:
                logger.info(f"Returning cached search results for query: {query}")
                return cached_result['results']
        
        # Perform search
        results = await self.vector_service.search_documents_async(query, n_results)
        
        # Cache the results
        self._cache[cache_key] = {
            'results': results,
            'timestamp': time.time()
        }
        
        return results
    
    async def search_by_entities(self, entities: List[str], n_results: int = 10) -> List[tuple]:
        """
        Search documents by medical entities.
        
        Args:
            entities: List of entity texts
            n_results: Number of results to return
            
        Returns:
            List of (document, similarity_score) tuples
        """
        from ..models.document import Entity, EntityType
        
        # Convert entity texts to Entity objects
        entity_objects = []
        for entity_text in entities:
            entity = Entity(
                text=entity_text,
                entity_type=EntityType.MEDICATION,  # Default type
                start=0,
                end=len(entity_text),
                confidence=1.0
            )
            entity_objects.append(entity)
        
        return await self.vector_service.search_by_entities_async(entity_objects, n_results)
    
    def get_document(self, document_id: str) -> Optional[Document]:
        """
        Get a document by ID.
        
        Args:
            document_id: Document ID
            
        Returns:
            Document or None if not found
        """
        return self.documents.get(document_id)
    
    def get_all_documents(self, limit: int = 100) -> List[Document]:
        """
        Get all documents.
        
        Args:
            limit: Maximum number of documents to return
            
        Returns:
            List of documents
        """
        return list(self.documents.values())[:limit]
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document asynchronously.
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            True if successful
        """
        document = self.documents.get(document_id)
        if not document:
            return False
        
        try:
            # Remove from vector database
            if document.vector_id:
                await self.vector_service.delete_document_async(document.vector_id)
            
            # Remove from memory
            del self.documents[document_id]
            
            # Clear cache entries for this document
            self._clear_document_cache(document_id)
            
            logger.info(f"Deleted document {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {str(e)}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get processing statistics.
        
        Args:
            Dictionary with statistics
        """
        total_docs = len(self.documents)
        completed_docs = len([d for d in self.documents.values() if d.status == DocumentStatus.COMPLETED])
        failed_docs = len([d for d in self.documents.values() if d.status == DocumentStatus.FAILED])
        
        total_entities = sum(d.entity_count for d in self.documents.values())
        
        # Entity type statistics
        entity_types = {}
        for doc in self.documents.values():
            for entity in doc.entities:
                entity_type = entity.entity_type.value
                entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
        
        avg_processing_time = 0
        if completed_docs > 0:
            processing_times = [d.processing_time for d in self.documents.values() if d.processing_time]
            avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        return {
            "total_documents": total_docs,
            "completed_documents": completed_docs,
            "failed_documents": failed_docs,
            "total_entities": total_entities,
            "entity_types": entity_types,
            "average_processing_time": avg_processing_time,
            "cache_size": len(self._cache),
            "vector_db_stats": self.vector_service.get_collection_stats()
        }
    
    def _create_document_record(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> Document:
        """Create a new document record."""
        document_id = str(uuid.uuid4())
        filename = os.path.basename(file_path)
        file_type = os.path.splitext(filename)[1].lower()
        
        return Document(
            id=document_id,
            filename=filename,
            file_path=file_path,
            file_type=file_type,
            metadata=metadata or {},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    async def _perform_ocr_async(self, file_path: str) -> tuple:
        """Perform OCR processing asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor, 
            self.ocr_service.extract_text, 
            file_path
        )
    
    async def _perform_ner_async(self, text: str) -> List:
        """Perform NER processing asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor, 
            self.ner_service.extract_entities, 
            text
        )
    
    async def _add_to_vector_db_async(self, document: Document) -> str:
        """Add document to vector database asynchronously."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor, 
            self.vector_service.add_document, 
            document
        )
    
    def _clear_document_cache(self, document_id: str):
        """Clear cache entries for a specific document."""
        keys_to_remove = [k for k in self._cache.keys() if document_id in str(k)]
        for key in keys_to_remove:
            del self._cache[key]
    
    def _perform_ocr(self, file_path: str) -> tuple:
        """Synchronous OCR processing (kept for backward compatibility)."""
        return self.ocr_service.extract_text(file_path) 