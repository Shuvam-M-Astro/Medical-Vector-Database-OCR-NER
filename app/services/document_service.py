"""
Main document processing service that orchestrates OCR, NER, and vector database operations.
"""

import os
import time
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
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
        
        logger.info("Document service initialized")
    
    def process_document(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> Document:
        """
        Process a document through the complete pipeline.
        
        Args:
            file_path: Path to the document file
            metadata: Optional metadata for the document
            
        Returns:
            Processed document
        """
        start_time = time.time()
        
        try:
            # Validate file
            if not self.ocr_service.validate_file(file_path):
                raise ValueError(f"Unsupported file format: {file_path}")
            
            # Create document record
            document = self._create_document_record(file_path, metadata)
            document.status = DocumentStatus.PROCESSING
            self.documents[document.id] = document
            
            logger.info(f"Starting processing for document: {document.id}")
            
            # Step 1: OCR Processing
            extracted_text, ocr_confidence = self._perform_ocr(file_path)
            document.extracted_text = extracted_text
            document.ocr_confidence = ocr_confidence
            
            logger.info(f"OCR completed for {document.id}: {len(extracted_text)} characters, {ocr_confidence:.2f} confidence")
            
            # Step 2: NER Processing
            entities = self.ner_service.extract_entities(extracted_text)
            document.entities = entities
            document.entity_count = len(entities)
            
            logger.info(f"NER completed for {document.id}: {len(entities)} entities found")
            
            # Step 3: Vector Database Storage
            vector_id = self.vector_service.add_document(document)
            document.vector_id = vector_id
            
            # Update document status
            document.status = DocumentStatus.COMPLETED
            document.updated_at = datetime.now()
            document.processing_time = time.time() - start_time
            
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
    
    def process_documents_batch(self, file_paths: List[str]) -> List[Document]:
        """
        Process multiple documents in batch.
        
        Args:
            file_paths: List of file paths to process
            
        Returns:
            List of processed documents
        """
        results = []
        
        for file_path in file_paths:
            try:
                document = self.process_document(file_path)
                results.append(document)
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {str(e)}")
                # Create failed document record
                failed_doc = self._create_document_record(file_path)
                failed_doc.status = DocumentStatus.FAILED
                failed_doc.error_message = str(e)
                failed_doc.updated_at = datetime.now()
                self.documents[failed_doc.id] = failed_doc
                results.append(failed_doc)
        
        return results
    
    def search_documents(self, query: str, n_results: int = 10) -> List[tuple]:
        """
        Search documents by text query.
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of (document, similarity_score) tuples
        """
        return self.vector_service.search_documents(query, n_results)
    
    def search_by_entities(self, entities: List[str], n_results: int = 10) -> List[tuple]:
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
        
        return self.vector_service.search_by_entities(entity_objects, n_results)
    
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
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document.
        
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
                self.vector_service.delete_document(document.vector_id)
            
            # Remove from memory
            del self.documents[document_id]
            
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
            "vector_db_stats": self.vector_service.get_collection_stats()
        }
    
    def _create_document_record(self, file_path: str, metadata: Optional[Dict[str, Any]] = None) -> Document:
        """
        Create a new document record.
        
        Args:
            file_path: Path to the document file
            metadata: Optional metadata
            
        Returns:
            New document record
        """
        file_path_obj = Path(file_path)
        
        document = Document(
            id=str(uuid.uuid4()),
            filename=file_path_obj.name,
            file_type=file_path_obj.suffix.lower(),
            file_size=file_path_obj.stat().st_size,
            status=DocumentStatus.PENDING,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata=metadata or {}
        )
        
        return document
    
    def _perform_ocr(self, file_path: str) -> tuple:
        """
        Perform OCR on the document.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Tuple of (extracted_text, confidence)
        """
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.pdf':
            # For PDFs, combine text from all pages
            page_results = self.ocr_service.extract_text_from_pdf(file_path)
            combined_text = " ".join([text for text, _ in page_results])
            avg_confidence = sum(conf for _, conf in page_results) / len(page_results) if page_results else 0
            return combined_text, avg_confidence
        else:
            # For images
            return self.ocr_service.extract_text_from_image(file_path) 