"""
Tests for vector database service.
"""

import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime

from app.services.vector_service import VectorService
from app.models.document import Document, DocumentStatus, Entity, EntityType


class TestVectorService:
    """Test cases for vector database service."""
    
    @pytest.fixture
    def vector_service(self):
        """Create vector service instance."""
        # Use temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Override the database path for testing
            import app.config
            original_path = app.config.settings.CHROMA_DB_PATH
            app.config.settings.CHROMA_DB_PATH = os.path.join(temp_dir, "test_chroma_db")
            
            try:
                service = VectorService()
                yield service
            finally:
                # Restore original path
                app.config.settings.CHROMA_DB_PATH = original_path
    
    @pytest.fixture
    def sample_document(self):
        """Create a sample document for testing."""
        return Document(
            id="test-doc-123",
            filename="test_invoice.pdf",
            file_type=".pdf",
            file_size=1024,
            status=DocumentStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            extracted_text="Patient John Smith was prescribed Aspirin 100mg for pain relief.",
            ocr_confidence=0.85,
            entities=[
                Entity(text="John Smith", entity_type=EntityType.PERSON, start=8, end=18, confidence=0.9),
                Entity(text="Aspirin", entity_type=EntityType.MEDICATION, start=30, end=37, confidence=0.95),
                Entity(text="100mg", entity_type=EntityType.QUANTITY, start=38, end=43, confidence=0.8)
            ],
            entity_count=3,
            processing_time=2.5,
            metadata={"source": "test", "department": "cardiology"}
        )
    
    def test_vector_service_initialization(self, vector_service):
        """Test vector service initialization."""
        assert vector_service.client is not None
        assert vector_service.embedding_model is not None
        assert vector_service.collection is not None
    
    def test_add_document(self, vector_service, sample_document):
        """Test adding document to vector database."""
        vector_id = vector_service.add_document(sample_document)
        
        assert isinstance(vector_id, str)
        assert len(vector_id) > 0
        
        # Check that document was added
        count = vector_service.get_document_count()
        assert count > 0
    
    def test_search_documents(self, vector_service, sample_document):
        """Test document search."""
        # Add document first
        vector_service.add_document(sample_document)
        
        # Search for medical terms
        results = vector_service.search_documents("Aspirin medication", n_results=5)
        
        assert isinstance(results, list)
        assert len(results) > 0
        
        # Check result structure
        for document, similarity in results:
            assert isinstance(document, Document)
            assert isinstance(similarity, float)
            assert 0 <= similarity <= 1
    
    def test_search_by_entities(self, vector_service, sample_document):
        """Test search by entities."""
        # Add document first
        vector_service.add_document(sample_document)
        
        # Create search entities
        search_entities = [
            Entity(text="Aspirin", entity_type=EntityType.MEDICATION, start=0, end=7, confidence=0.9),
            Entity(text="John Smith", entity_type=EntityType.PERSON, start=8, end=18, confidence=0.8)
        ]
        
        results = vector_service.search_by_entities(search_entities, n_results=5)
        
        assert isinstance(results, list)
        assert len(results) > 0
    
    def test_update_document(self, vector_service, sample_document):
        """Test document update."""
        # Add document first
        vector_id = vector_service.add_document(sample_document)
        sample_document.vector_id = vector_id
        
        # Update document
        sample_document.extracted_text += " Additional information."
        success = vector_service.update_document(sample_document)
        
        assert success == True
    
    def test_delete_document(self, vector_service, sample_document):
        """Test document deletion."""
        # Add document first
        vector_id = vector_service.add_document(sample_document)
        
        # Delete document
        success = vector_service.delete_document(vector_id)
        
        assert success == True
        
        # Check that document was removed
        count = vector_service.get_document_count()
        assert count == 0
    
    def test_get_document_count(self, vector_service, sample_document):
        """Test document count retrieval."""
        initial_count = vector_service.get_document_count()
        
        # Add document
        vector_service.add_document(sample_document)
        
        new_count = vector_service.get_document_count()
        assert new_count == initial_count + 1
    
    def test_get_collection_stats(self, vector_service):
        """Test collection statistics."""
        stats = vector_service.get_collection_stats()
        
        assert isinstance(stats, dict)
        assert "total_documents" in stats
        assert "embedding_dimension" in stats
        assert "collection_name" in stats
        assert stats["collection_name"] == "medical_documents"
    
    def test_create_document_text(self, vector_service, sample_document):
        """Test document text creation for embedding."""
        doc_text = vector_service._create_document_text(sample_document)
        
        assert isinstance(doc_text, str)
        assert len(doc_text) > 0
        assert "John Smith" in doc_text
        assert "Aspirin" in doc_text
        assert "MEDICATION" in doc_text
    
    def test_create_metadata(self, vector_service, sample_document):
        """Test metadata creation."""
        metadata = vector_service._create_metadata(sample_document)
        
        assert isinstance(metadata, dict)
        assert metadata["document_id"] == sample_document.id
        assert metadata["filename"] == sample_document.filename
        assert metadata["status"] == sample_document.status.value
        assert metadata["entity_count"] == sample_document.entity_count
        assert "entity_types" in metadata
    
    def test_metadata_to_document(self, vector_service):
        """Test metadata to document conversion."""
        metadata = {
            "document_id": "test-123",
            "filename": "test.pdf",
            "file_type": ".pdf",
            "status": "completed",
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00",
            "entity_count": 2,
            "ocr_confidence": 0.85,
            "processing_time": 1.5
        }
        
        document = vector_service._metadata_to_document(metadata)
        
        assert isinstance(document, Document)
        assert document.id == "test-123"
        assert document.filename == "test.pdf"
        assert document.entity_count == 2
        assert document.ocr_confidence == 0.85
    
    def test_multiple_documents(self, vector_service):
        """Test handling multiple documents."""
        # Create multiple test documents
        documents = []
        for i in range(3):
            doc = Document(
                id=f"test-doc-{i}",
                filename=f"invoice_{i}.pdf",
                file_type=".pdf",
                file_size=1024,
                status=DocumentStatus.COMPLETED,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                extracted_text=f"Document {i} with medical information.",
                ocr_confidence=0.8 + i * 0.05,
                entities=[],
                entity_count=0,
                processing_time=1.0 + i * 0.5
            )
            documents.append(doc)
        
        # Add all documents
        vector_ids = []
        for doc in documents:
            vector_id = vector_service.add_document(doc)
            vector_ids.append(vector_id)
        
        # Check count
        count = vector_service.get_document_count()
        assert count == 3
        
        # Search for documents
        results = vector_service.search_documents("medical information", n_results=10)
        assert len(results) >= 3
        
        # Delete all documents
        for vector_id in vector_ids:
            success = vector_service.delete_document(vector_id)
            assert success == True
        
        # Check final count
        final_count = vector_service.get_document_count()
        assert final_count == 0 