"""
Tests for validation utilities.
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.utils.validation import (
    FileValidator, InputValidator, DataQualityValidator, 
    BusinessLogicValidator, ValidationError, rate_limiter
)


class TestFileValidator:
    """Test file validation utilities."""
    
    def test_validate_file_security_valid_file(self):
        """Test validation of a valid file."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b'%PDF-1.4\n%Test PDF content')
            temp_path = f.name
        
        try:
            is_valid, error = FileValidator.validate_file_security(temp_path)
            assert is_valid
            assert error == ""
        finally:
            os.unlink(temp_path)
    
    def test_validate_file_security_nonexistent_file(self):
        """Test validation of non-existent file."""
        is_valid, error = FileValidator.validate_file_security("/nonexistent/file.pdf")
        assert not is_valid
        assert "File does not exist" in error
    
    def test_validate_file_security_large_file(self):
        """Test validation of file that's too large."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            # Create a large file
            f.write(b'0' * (50 * 1024 * 1024 + 1))  # 50MB + 1 byte
            temp_path = f.name
        
        try:
            is_valid, error = FileValidator.validate_file_security(temp_path)
            assert not is_valid
            assert "File too large" in error
        finally:
            os.unlink(temp_path)
    
    def test_validate_file_security_invalid_extension(self):
        """Test validation of file with invalid extension."""
        with tempfile.NamedTemporaryFile(suffix='.exe', delete=False) as f:
            f.write(b'Test content')
            temp_path = f.name
        
        try:
            is_valid, error = FileValidator.validate_file_security(temp_path)
            assert not is_valid
            assert "Unsupported file type" in error
        finally:
            os.unlink(temp_path)
    
    def test_contains_malicious_patterns(self):
        """Test detection of malicious patterns in filenames."""
        malicious_filenames = [
            "test../../../etc/passwd.pdf",
            "test<script>alert('xss')</script>.pdf",
            "testjavascript:alert('xss').pdf",
            "testdata:text/html,<script>alert('xss')</script>.pdf",
            "testvbscript:alert('xss').pdf",
            "testonload=alert('xss').pdf",
            "testonerror=alert('xss').pdf",
            "test<iframe src='xss'></iframe>.pdf",
        ]
        
        for filename in malicious_filenames:
            assert FileValidator._contains_malicious_patterns(filename)
        
        # Test valid filenames
        valid_filenames = [
            "document.pdf",
            "medical_report_2023.pdf",
            "test-image.jpg",
            "scan_001.png",
        ]
        
        for filename in valid_filenames:
            assert not FileValidator._contains_malicious_patterns(filename)
    
    def test_contains_executable_content(self):
        """Test detection of executable content."""
        # Test with executable signature
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00')  # PE header
            temp_path = f.name
        
        try:
            assert FileValidator._contains_executable_content(temp_path)
        finally:
            os.unlink(temp_path)
        
        # Test with normal content
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b'Normal text content')
            temp_path = f.name
        
        try:
            assert not FileValidator._contains_executable_content(temp_path)
        finally:
            os.unlink(temp_path)


class TestInputValidator:
    """Test input validation utilities."""
    
    def test_sanitize_string_valid(self):
        """Test sanitization of valid string."""
        result = InputValidator.sanitize_string("  Test String  ", max_length=100)
        assert result == "Test String"
    
    def test_sanitize_string_with_control_chars(self):
        """Test sanitization of string with control characters."""
        result = InputValidator.sanitize_string("Test\x00String\x08", max_length=100)
        assert result == "TestString"
    
    def test_sanitize_string_too_long(self):
        """Test sanitization of string that's too long."""
        long_string = "a" * 1001
        with pytest.raises(ValidationError, match="String too long"):
            InputValidator.sanitize_string(long_string, max_length=1000)
    
    def test_sanitize_string_invalid_type(self):
        """Test sanitization with invalid input type."""
        with pytest.raises(ValidationError, match="Input must be a string"):
            InputValidator.sanitize_string(123, max_length=100)
    
    def test_validate_search_query_valid(self):
        """Test validation of valid search query."""
        result = InputValidator.validate_search_query("medical diagnosis")
        assert result == "medical diagnosis"
    
    def test_validate_search_query_empty(self):
        """Test validation of empty search query."""
        with pytest.raises(ValidationError, match="Search query cannot be empty"):
            InputValidator.validate_search_query("")
        
        with pytest.raises(ValidationError, match="Search query cannot be empty"):
            InputValidator.validate_search_query("   ")
    
    def test_validate_search_query_dangerous_content(self):
        """Test validation of search query with dangerous content."""
        dangerous_queries = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "vbscript:alert('xss')",
            "onload=alert('xss')",
            "onerror=alert('xss')",
        ]
        
        for query in dangerous_queries:
            with pytest.raises(ValidationError, match="potentially dangerous content"):
                InputValidator.validate_search_query(query)
    
    def test_validate_metadata_valid(self):
        """Test validation of valid metadata."""
        metadata = {
            "patient_id": "12345",
            "department": "cardiology",
            "priority": 1,
            "tags": ["urgent", "review"]
        }
        
        result = InputValidator.validate_metadata(metadata)
        assert result == metadata
    
    def test_validate_metadata_none(self):
        """Test validation of None metadata."""
        result = InputValidator.validate_metadata(None)
        assert result is None
    
    def test_validate_metadata_invalid_type(self):
        """Test validation of invalid metadata type."""
        with pytest.raises(ValidationError, match="Metadata must be a dictionary"):
            InputValidator.validate_metadata("not a dict")
    
    def test_validate_metadata_too_many_keys(self):
        """Test validation of metadata with too many keys."""
        metadata = {f"key_{i}": f"value_{i}" for i in range(51)}
        
        with pytest.raises(ValidationError, match="Too many metadata keys"):
            InputValidator.validate_metadata(metadata)
    
    def test_validate_metadata_invalid_key_type(self):
        """Test validation of metadata with invalid key type."""
        metadata = {123: "value"}
        
        with pytest.raises(ValidationError, match="Metadata keys must be strings"):
            InputValidator.validate_metadata(metadata)
    
    def test_validate_metadata_key_too_long(self):
        """Test validation of metadata with key too long."""
        metadata = {"a" * 101: "value"}
        
        with pytest.raises(ValidationError, match="Metadata key too long"):
            InputValidator.validate_metadata(metadata)
    
    def test_validate_metadata_value_too_long(self):
        """Test validation of metadata with value too long."""
        metadata = {"key": "a" * 1001}
        
        with pytest.raises(ValidationError, match="Metadata string value too long"):
            InputValidator.validate_metadata(metadata)
    
    def test_validate_metadata_unsupported_value_type(self):
        """Test validation of metadata with unsupported value type."""
        metadata = {"key": lambda x: x}
        
        with pytest.raises(ValidationError, match="Unsupported metadata value type"):
            InputValidator.validate_metadata(metadata)


class TestDataQualityValidator:
    """Test data quality validation utilities."""
    
    def test_validate_ocr_result_high_confidence(self):
        """Test validation of OCR result with high confidence."""
        is_valid, warnings = DataQualityValidator.validate_ocr_result(
            "This is a medical document with clear text.", 0.95
        )
        assert is_valid
        assert warnings == ""
    
    def test_validate_ocr_result_low_confidence(self):
        """Test validation of OCR result with low confidence."""
        is_valid, warnings = DataQualityValidator.validate_ocr_result(
            "This is a medical document with clear text.", 0.3
        )
        assert not is_valid
        assert "Low OCR confidence" in warnings
    
    def test_validate_ocr_result_short_text(self):
        """Test validation of OCR result with very short text."""
        is_valid, warnings = DataQualityValidator.validate_ocr_result("Hi", 0.8)
        assert not is_valid
        assert "Extracted text is very short" in warnings
    
    def test_validate_ocr_result_common_errors(self):
        """Test validation of OCR result with common errors."""
        is_valid, warnings = DataQualityValidator.validate_ocr_result(
            "This text has 000 multiple zeros and 111 multiple ones", 0.8
        )
        assert not is_valid
        assert "Text contains common OCR errors" in warnings
    
    def test_validate_ocr_result_gibberish(self):
        """Test validation of OCR result that appears to be gibberish."""
        is_valid, warnings = DataQualityValidator.validate_ocr_result(
            "1234567890123456789012345678901234567890", 0.8
        )
        assert not is_valid
        assert "Text appears to be gibberish" in warnings
    
    def test_validate_ner_result_valid(self):
        """Test validation of valid NER result."""
        entities = [
            {"text": "aspirin", "confidence": 0.9},
            {"text": "heart attack", "confidence": 0.8},
            {"text": "Dr. Smith", "confidence": 0.7}
        ]
        
        is_valid, warnings = DataQualityValidator.validate_ner_result(entities)
        assert is_valid
        assert warnings == ""
    
    def test_validate_ner_result_no_entities(self):
        """Test validation of NER result with no entities."""
        is_valid, warnings = DataQualityValidator.validate_ner_result([])
        assert not is_valid
        assert "No entities extracted" in warnings
    
    def test_validate_ner_result_too_many_entities(self):
        """Test validation of NER result with too many entities."""
        entities = [{"text": f"entity_{i}", "confidence": 0.8} for i in range(1001)]
        
        is_valid, warnings = DataQualityValidator.validate_ner_result(entities)
        assert not is_valid
        assert "Very high number of entities extracted" in warnings
    
    def test_validate_ner_result_low_confidence_entities(self):
        """Test validation of NER result with many low-confidence entities."""
        entities = [
            {"text": "entity1", "confidence": 0.3},
            {"text": "entity2", "confidence": 0.4},
            {"text": "entity3", "confidence": 0.2},
            {"text": "entity4", "confidence": 0.1}
        ]
        
        is_valid, warnings = DataQualityValidator.validate_ner_result(entities)
        assert not is_valid
        assert "High proportion of low-confidence entities" in warnings
    
    def test_validate_ner_result_duplicate_entities(self):
        """Test validation of NER result with duplicate entities."""
        entities = [
            {"text": "aspirin", "confidence": 0.9},
            {"text": "aspirin", "confidence": 0.8},
            {"text": "heart attack", "confidence": 0.7}
        ]
        
        is_valid, warnings = DataQualityValidator.validate_ner_result(entities)
        assert not is_valid
        assert "Duplicate entities detected" in warnings


class TestBusinessLogicValidator:
    """Test business logic validation utilities."""
    
    def test_validate_document_processing_valid(self):
        """Test validation of valid document processing."""
        document = {
            "id": "doc123",
            "filename": "test.pdf",
            "status": "completed",
            "extracted_text": "Medical document content",
            "entities": [{"text": "aspirin", "entity_type": "MEDICATION"}],
            "entity_count": 1,
            "processing_time": 5.5
        }
        
        is_valid, errors = BusinessLogicValidator.validate_document_processing(document)
        assert is_valid
        assert errors == []
    
    def test_validate_document_processing_missing_required_fields(self):
        """Test validation of document processing with missing required fields."""
        document = {
            "filename": "test.pdf"
            # Missing id and status
        }
        
        is_valid, errors = BusinessLogicValidator.validate_document_processing(document)
        assert not is_valid
        assert "Missing required field: id" in errors
        assert "Missing required field: status" in errors
    
    def test_validate_document_processing_inconsistent_status(self):
        """Test validation of document processing with inconsistent status."""
        # Completed document without extracted text
        document = {
            "id": "doc123",
            "filename": "test.pdf",
            "status": "completed",
            "entities": []
        }
        
        is_valid, errors = BusinessLogicValidator.validate_document_processing(document)
        assert not is_valid
        assert "Completed document missing extracted text" in errors
        
        # Failed document without error message
        document["status"] = "failed"
        document["extracted_text"] = "Some text"
        
        is_valid, errors = BusinessLogicValidator.validate_document_processing(document)
        assert not is_valid
        assert "Failed document missing error message" in errors
    
    def test_validate_document_processing_invalid_processing_time(self):
        """Test validation of document processing with invalid processing time."""
        document = {
            "id": "doc123",
            "filename": "test.pdf",
            "status": "completed",
            "extracted_text": "Medical document content",
            "processing_time": -1.0
        }
        
        is_valid, errors = BusinessLogicValidator.validate_document_processing(document)
        assert not is_valid
        assert "Invalid processing time: negative value" in errors
        
        document["processing_time"] = 4000.0  # Over 1 hour
        
        is_valid, errors = BusinessLogicValidator.validate_document_processing(document)
        assert not is_valid
        assert "Processing time too long" in errors
    
    def test_validate_document_processing_entity_count_mismatch(self):
        """Test validation of document processing with entity count mismatch."""
        document = {
            "id": "doc123",
            "filename": "test.pdf",
            "status": "completed",
            "extracted_text": "Medical document content",
            "entities": [{"text": "aspirin"}, {"text": "heart attack"}],
            "entity_count": 1  # Should be 2
        }
        
        is_valid, errors = BusinessLogicValidator.validate_document_processing(document)
        assert not is_valid
        assert "Entity count mismatch" in errors
    
    def test_validate_search_parameters_valid(self):
        """Test validation of valid search parameters."""
        is_valid, errors = BusinessLogicValidator.validate_search_parameters(
            "medical diagnosis", 10, max_results=100
        )
        assert is_valid
        assert errors == []
    
    def test_validate_search_parameters_empty_query(self):
        """Test validation of search parameters with empty query."""
        is_valid, errors = BusinessLogicValidator.validate_search_parameters(
            "", 10, max_results=100
        )
        assert not is_valid
        assert "Search query cannot be empty" in errors
    
    def test_validate_search_parameters_invalid_results_count(self):
        """Test validation of search parameters with invalid results count."""
        is_valid, errors = BusinessLogicValidator.validate_search_parameters(
            "medical diagnosis", 0, max_results=100
        )
        assert not is_valid
        assert "Number of results must be at least 1" in errors
        
        is_valid, errors = BusinessLogicValidator.validate_search_parameters(
            "medical diagnosis", 150, max_results=100
        )
        assert not is_valid
        assert "Number of results too high" in errors


class TestRateLimitValidator:
    """Test rate limiting validation utilities."""
    
    def test_rate_limit_check_allowed(self):
        """Test rate limit check for allowed request."""
        client_id = "test_client"
        
        # First request should be allowed
        is_allowed, error = rate_limiter.check_rate_limit(client_id)
        assert is_allowed
        assert error == ""
    
    def test_rate_limit_check_exceeded(self):
        """Test rate limit check for exceeded limit."""
        client_id = "test_client_2"
        
        # Make many requests to exceed limit
        for _ in range(65):  # Exceed 60 per minute
            rate_limiter.check_rate_limit(client_id)
        
        # Next request should be blocked
        is_allowed, error = rate_limiter.check_rate_limit(client_id)
        assert not is_allowed
        assert "Rate limit exceeded" in error
    
    def test_rate_limit_cleanup(self):
        """Test rate limit cleanup of old entries."""
        client_id = "test_client_3"
        
        # Make a request
        rate_limiter.check_rate_limit(client_id)
        
        # Verify cleanup doesn't affect current requests
        is_allowed, error = rate_limiter.check_rate_limit(client_id)
        assert is_allowed
        assert error == ""


if __name__ == "__main__":
    pytest.main([__file__]) 