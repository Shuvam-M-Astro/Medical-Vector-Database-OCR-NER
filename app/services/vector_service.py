"""
Vector database service using ChromaDB for medical document storage and search.
"""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional, Tuple
import uuid
import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from loguru import logger
import time

from ..config import settings
from ..models.document import Document, DocumentStatus


class VectorService:
    """Vector database service for medical documents."""
    
    def __init__(self):
        """Initialize vector service."""
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_DB_PATH,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Initialize embedding model with caching
        self.embedding_model = self._get_embedding_model()
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="medical_documents",
            metadata={"description": "Medical documents with OCR and NER"}
        )
        
        # Performance optimizations
        self._executor = ThreadPoolExecutor(max_workers=settings.MAX_WORKERS)
        self._embedding_cache = {}
        self._cache_ttl = 3600  # 1 hour cache TTL
        
        logger.info("Vector service initialized")
    
    @lru_cache(maxsize=1)
    def _get_embedding_model(self) -> SentenceTransformer:
        """Get embedding model with caching."""
        logger.info("Loading embedding model...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Embedding model loaded successfully")
        return model
    
    def add_document(self, document: Document) -> str:
        """
        Add a document to the vector database.
        
        Args:
            document: Document to add
            
        Returns:
            Vector ID of the added document
        """
        try:
            # Create document text for embedding
            doc_text = self._create_document_text(document)
            
            # Generate embedding with caching
            embedding = self._get_embedding_cached(doc_text)
            
            # Create metadata
            metadata = self._create_metadata(document)
            
            # Add to collection
            vector_id = str(uuid.uuid4())
            self.collection.add(
                documents=[doc_text],
                embeddings=[embedding],
                metadatas=[metadata],
                ids=[vector_id]
            )
            
            logger.info(f"Added document {document.id} to vector database")
            return vector_id
            
        except Exception as e:
            logger.error(f"Failed to add document to vector database: {str(e)}")
            raise
    
    async def add_document_async(self, document: Document) -> str:
        """
        Add a document to the vector database asynchronously.
        
        Args:
            document: Document to add
            
        Returns:
            Vector ID of the added document
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor, 
            self.add_document, 
            document
        )
    
    def search_documents(self, query: str, n_results: int = 10) -> List[Tuple[Document, float]]:
        """
        Search documents by text query.
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of (document, similarity_score) tuples
        """
        try:
            # Generate query embedding with caching
            query_embedding = self._get_embedding_cached(query)
            
            # Search collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=['metadatas', 'distances']
            )
            
            # Convert results to documents
            documents = []
            for i, doc_id in enumerate(results['ids'][0]):
                metadata = results['metadatas'][0][i]
                distance = results['distances'][0][i]
                similarity = 1 - distance  # Convert distance to similarity
                
                # Create document object from metadata
                document = self._metadata_to_document(metadata)
                documents.append((document, similarity))
            
            logger.info(f"Found {len(documents)} documents for query: {query}")
            return documents
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return []
    
    async def search_documents_async(self, query: str, n_results: int = 10) -> List[Tuple[Document, float]]:
        """
        Search documents by text query asynchronously.
        
        Args:
            query: Search query
            n_results: Number of results to return
            
        Returns:
            List of (document, similarity_score) tuples
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor, 
            self.search_documents, 
            query, 
            n_results
        )
    
    def search_by_entities(self, entities: List[Document.Entity], n_results: int = 10) -> List[Tuple[Document, float]]:
        """
        Search documents by medical entities.
        
        Args:
            entities: List of medical entities
            n_results: Number of results to return
            
        Returns:
            List of (document, similarity_score) tuples
        """
        # Create query from entity texts
        entity_texts = [entity.text for entity in entities]
        query = " ".join(entity_texts)
        
        return self.search_documents(query, n_results)
    
    async def search_by_entities_async(self, entities: List[Document.Entity], n_results: int = 10) -> List[Tuple[Document, float]]:
        """
        Search documents by medical entities asynchronously.
        
        Args:
            entities: List of medical entities
            n_results: Number of results to return
            
        Returns:
            List of (document, similarity_score) tuples
        """
        # Create query from entity texts
        entity_texts = [entity.text for entity in entities]
        query = " ".join(entity_texts)
        
        return await self.search_documents_async(query, n_results)
    
    def update_document(self, document: Document) -> bool:
        """
        Update a document in the vector database.
        
        Args:
            document: Updated document
            
        Returns:
            True if successful
        """
        try:
            # Remove old document
            if document.vector_id:
                self.collection.delete(ids=[document.vector_id])
            
            # Add updated document
            vector_id = self.add_document(document)
            document.vector_id = vector_id
            
            logger.info(f"Updated document {document.id} in vector database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update document: {str(e)}")
            return False
    
    async def update_document_async(self, document: Document) -> bool:
        """
        Update a document in the vector database asynchronously.
        
        Args:
            document: Updated document
            
        Returns:
            True if successful
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor, 
            self.update_document, 
            document
        )
    
    def delete_document(self, vector_id: str) -> bool:
        """
        Delete a document from the vector database.
        
        Args:
            vector_id: Vector ID of document to delete
            
        Returns:
            True if successful
        """
        try:
            self.collection.delete(ids=[vector_id])
            logger.info(f"Deleted document {vector_id} from vector database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document: {str(e)}")
            return False
    
    async def delete_document_async(self, vector_id: str) -> bool:
        """
        Delete a document from the vector database asynchronously.
        
        Args:
            vector_id: Vector ID of document to delete
            
        Returns:
            True if successful
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor, 
            self.delete_document, 
            vector_id
        )
    
    def get_document_count(self) -> int:
        """Get total number of documents in the database."""
        return self.collection.count()
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        count = self.collection.count()
        return {
            "total_documents": count,
            "embedding_dimension": settings.VECTOR_DIMENSION,
            "collection_name": "medical_documents",
            "embedding_cache_size": len(self._embedding_cache)
        }
    
    def _get_embedding_cached(self, text: str) -> List[float]:
        """
        Get embedding with caching.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        # Check cache first
        cache_key = hash(text)
        if cache_key in self._embedding_cache:
            cached_result = self._embedding_cache[cache_key]
            if time.time() - cached_result.get('timestamp', 0) < self._cache_ttl:
                return cached_result['embedding']
        
        # Generate embedding
        embedding = self.embedding_model.encode(text).tolist()
        
        # Cache the result
        self._embedding_cache[cache_key] = {
            'embedding': embedding,
            'timestamp': time.time()
        }
        
        return embedding
    
    def _create_document_text(self, document: Document) -> str:
        """
        Create text representation of document for embedding.
        
        Args:
            document: Document to process
            
        Returns:
            Text representation
        """
        text_parts = []
        
        # Add extracted text
        if document.extracted_text:
            text_parts.append(document.extracted_text)
        
        # Add entity information
        if document.entities:
            entity_texts = []
            for entity in document.entities:
                entity_texts.append(f"{entity.text} ({entity.entity_type.value})")
            text_parts.append(" ".join(entity_texts))
        
        # Add metadata
        if document.metadata:
            for key, value in document.metadata.items():
                text_parts.append(f"{key}: {value}")
        
        return " ".join(text_parts)
    
    def _create_metadata(self, document: Document) -> Dict[str, Any]:
        """
        Create metadata for vector database.
        
        Args:
            document: Document to process
            
        Returns:
            Metadata dictionary
        """
        metadata = {
            "document_id": document.id,
            "filename": document.filename,
            "file_type": document.file_type,
            "status": document.status.value,
            "created_at": document.created_at.isoformat(),
            "updated_at": document.updated_at.isoformat(),
            "entity_count": document.entity_count,
            "ocr_confidence": document.ocr_confidence or 0.0,
            "processing_time": document.processing_time or 0.0
        }
        
        # Add entity information
        if document.entities:
            entity_types = {}
            for entity in document.entities:
                entity_type = entity.entity_type.value
                entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
            metadata["entity_types"] = entity_types
        
        # Add custom metadata
        if document.metadata:
            metadata.update(document.metadata)
        
        return metadata
    
    def _metadata_to_document(self, metadata: Dict[str, Any]) -> Document:
        """
        Convert metadata back to document object.
        
        Args:
            metadata: Document metadata
            
        Returns:
            Document object
        """
        from datetime import datetime
        
        return Document(
            id=metadata.get("document_id", ""),
            filename=metadata.get("filename", ""),
            file_type=metadata.get("file_type", ""),
            status=DocumentStatus(metadata.get("status", "pending")),
            created_at=datetime.fromisoformat(metadata.get("created_at", datetime.now().isoformat())),
            updated_at=datetime.fromisoformat(metadata.get("updated_at", datetime.now().isoformat())),
            entity_count=metadata.get("entity_count", 0),
            ocr_confidence=metadata.get("ocr_confidence", 0.0),
            processing_time=metadata.get("processing_time", 0.0),
            metadata=metadata
        ) 