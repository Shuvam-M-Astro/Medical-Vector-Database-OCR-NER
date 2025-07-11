"""
Comprehensive validation utilities for the medical vector database.
"""

import os
import re
import magic
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import json
from loguru import logger

from ..config import settings


class ValidationError(Exception):
    """Custom validation error."""
    pass


class FileValidator:
    """File validation utilities."""
    
    @staticmethod
    def validate_file_security(file_path: str) -> Tuple[bool, str]:
        """
        Perform security validation on uploaded files.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return False, "File does not exist"
            
            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > settings.MAX_FILE_SIZE:
                return False, f"File too large: {file_size} bytes (max: {settings.MAX_FILE_SIZE})"
            
            # Check file extension
            file_ext = Path(file_path).suffix.lower()
            if file_ext not in settings.ALLOWED_EXTENSIONS:
                return False, f"Unsupported file type: {file_ext}"
            
            # Check MIME type using python-magic
            try:
                mime_type = magic.from_file(file_path, mime=True)
                allowed_mimes = {
                    '.pdf': 'application/pdf',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                    '.tiff': 'image/tiff',
                    '.bmp': 'image/bmp'
                }
                
                if file_ext in allowed_mimes and mime_type != allowed_mimes[file_ext]:
                    return False, f"MIME type mismatch: expected {allowed_mimes[file_ext]}, got {mime_type}"
                    
            except ImportError:
                logger.warning("python-magic not available, skipping MIME type validation")
            
            # Check for malicious patterns in filename
            filename = Path(file_path).name
            if FileValidator._contains_malicious_patterns(filename):
                return False, "Filename contains potentially malicious patterns"
            
            # Check file content for executable patterns
            if FileValidator._contains_executable_content(file_path):
                return False, "File contains executable content"
            
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    @staticmethod
    def _contains_malicious_patterns(filename: str) -> bool:
        """Check for malicious patterns in filename."""
        malicious_patterns = [
            r'\.\./',  # Directory traversal
            r'\.\.\\',  # Windows directory traversal
            r'<script',  # XSS
            r'javascript:',  # XSS
            r'data:',  # Data URI
            r'vbscript:',  # VBScript
            r'onload=',  # Event handlers
            r'onerror=',  # Event handlers
            r'<iframe',  # Iframe injection
        ]
        
        for pattern in malicious_patterns:
            if re.search(pattern, filename, re.IGNORECASE):
                return True
        
        return False
    
    @staticmethod
    def _contains_executable_content(file_path: str) -> bool:
        """Check if file contains executable content."""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(1024)
                
            # Check for common executable signatures
            executable_signatures = [
                b'MZ',  # Windows PE
                b'\x7fELF',  # Linux ELF
                b'\xfe\xed\xfa\xce',  # Mach-O
                b'\xce\xfa\xed\xfe',  # Mach-O (reverse)
            ]
            
            for sig in executable_signatures:
                if header.startswith(sig):
                    return True
                    
        except Exception:
            pass
        
        return False


class InputValidator:
    """Input validation utilities."""
    
    @staticmethod
    def sanitize_string(input_str: str, max_length: int = 1000) -> str:
        """
        Sanitize string input.
        
        Args:
            input_str: Input string
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string
        """
        if not isinstance(input_str, str):
            raise ValidationError("Input must be a string")
        
        # Remove null bytes and control characters
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', input_str)
        
        # Trim whitespace
        sanitized = sanitized.strip()
        
        # Check length
        if len(sanitized) > max_length:
            raise ValidationError(f"String too long: {len(sanitized)} characters (max: {max_length})")
        
        return sanitized
    
    @staticmethod
    def validate_search_query(query: str) -> str:
        """
        Validate search query.
        
        Args:
            query: Search query
            
        Returns:
            Validated query
        """
        if not query or not query.strip():
            raise ValidationError("Search query cannot be empty")
        
        sanitized = InputValidator.sanitize_string(query, max_length=500)
        
        # Check for potentially dangerous patterns
        dangerous_patterns = [
            r'<script',
            r'javascript:',
            r'data:',
            r'vbscript:',
            r'onload=',
            r'onerror=',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, sanitized, re.IGNORECASE):
                raise ValidationError("Search query contains potentially dangerous content")
        
        return sanitized
    
    @staticmethod
    def validate_metadata(metadata: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Validate metadata dictionary.
        
        Args:
            metadata: Metadata dictionary
            
        Returns:
            Validated metadata
        """
        if metadata is None:
            return None
        
        if not isinstance(metadata, dict):
            raise ValidationError("Metadata must be a dictionary")
        
        validated_metadata = {}
        
        for key, value in metadata.items():
            # Validate key
            if not isinstance(key, str):
                raise ValidationError("Metadata keys must be strings")
            
            if len(key) > 100:
                raise ValidationError("Metadata key too long")
            
            # Validate value
            if isinstance(value, (str, int, float, bool)):
                if isinstance(value, str):
                    validated_metadata[key] = InputValidator.sanitize_string(value, max_length=1000)
                else:
                    validated_metadata[key] = value
            elif isinstance(value, list):
                validated_metadata[key] = InputValidator._validate_list(value)
            elif isinstance(value, dict):
                validated_metadata[key] = InputValidator.validate_metadata(value)
            else:
                raise ValidationError(f"Unsupported metadata value type: {type(value)}")
        
        return validated_metadata
    
    @staticmethod
    def _validate_list(value_list: List[Any]) -> List[Any]:
        """Validate list values."""
        if len(value_list) > 100:
            raise ValidationError("List too long")
        
        validated_list = []
        for item in value_list:
            if isinstance(item, (str, int, float, bool)):
                if isinstance(item, str):
                    validated_list.append(InputValidator.sanitize_string(item, max_length=500))
                else:
                    validated_list.append(item)
            else:
                raise ValidationError(f"Unsupported list item type: {type(item)}")
        
        return validated_list


class DataQualityValidator:
    """Data quality validation utilities."""
    
    @staticmethod
    def validate_ocr_result(text: str, confidence: float) -> Tuple[bool, str]:
        """
        Validate OCR result quality.
        
        Args:
            text: Extracted text
            confidence: OCR confidence score
            
        Returns:
            Tuple of (is_valid, warning_message)
        """
        warnings = []
        
        # Check confidence threshold
        if confidence < settings.CONFIDENCE_THRESHOLD:
            warnings.append(f"Low OCR confidence: {confidence:.2f} (threshold: {settings.CONFIDENCE_THRESHOLD})")
        
        # Check text length
        if len(text.strip()) < 10:
            warnings.append("Extracted text is very short")
        
        # Check for common OCR errors
        if DataQualityValidator._has_common_ocr_errors(text):
            warnings.append("Text contains common OCR errors")
        
        # Check for gibberish
        if DataQualityValidator._is_gibberish(text):
            warnings.append("Text appears to be gibberish")
        
        is_valid = len(warnings) == 0 or confidence >= 0.5  # Allow with warnings if confidence is reasonable
        
        return is_valid, "; ".join(warnings)
    
    @staticmethod
    def validate_ner_result(entities: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """
        Validate NER result quality.
        
        Args:
            entities: List of extracted entities
            
        Returns:
            Tuple of (is_valid, warning_message)
        """
        warnings = []
        
        # Check entity count
        if len(entities) == 0:
            warnings.append("No entities extracted")
        elif len(entities) > 1000:
            warnings.append("Very high number of entities extracted")
        
        # Check entity quality
        low_confidence_count = 0
        for entity in entities:
            if entity.get('confidence', 1.0) < 0.5:
                low_confidence_count += 1
        
        if low_confidence_count > len(entities) * 0.5:
            warnings.append("High proportion of low-confidence entities")
        
        # Check for duplicate entities
        entity_texts = [entity.get('text', '').lower() for entity in entities]
        if len(entity_texts) != len(set(entity_texts)):
            warnings.append("Duplicate entities detected")
        
        is_valid = len(warnings) == 0
        
        return is_valid, "; ".join(warnings)
    
    @staticmethod
    def _has_common_ocr_errors(text: str) -> bool:
        """Check for common OCR errors."""
        common_errors = [
            r'[0O]{3,}',  # Multiple zeros/Os
            r'[1lI]{3,}',  # Multiple ones/ls/Is
            r'[5S]{3,}',   # Multiple fives/Ss
            r'[8B]{3,}',   # Multiple eights/Bs
        ]
        
        for pattern in common_errors:
            if re.search(pattern, text):
                return True
        
        return False
    
    @staticmethod
    def _is_gibberish(text: str) -> bool:
        """Check if text appears to be gibberish."""
        # Check for excessive special characters
        special_char_ratio = len(re.findall(r'[^a-zA-Z0-9\s]', text)) / len(text) if text else 0
        if special_char_ratio > 0.3:
            return True
        
        # Check for excessive numbers
        number_ratio = len(re.findall(r'\d', text)) / len(text) if text else 0
        if number_ratio > 0.5:
            return True
        
        # Check for repeated patterns
        words = text.split()
        if len(words) > 10:
            word_freq = {}
            for word in words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            max_freq = max(word_freq.values()) if word_freq else 0
            if max_freq > len(words) * 0.3:
                return True
        
        return False


class BusinessLogicValidator:
    """Business logic validation utilities."""
    
    @staticmethod
    def validate_document_processing(document: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate document processing business rules.
        
        Args:
            document: Document data
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check required fields
        required_fields = ['id', 'filename', 'status']
        for field in required_fields:
            if field not in document:
                errors.append(f"Missing required field: {field}")
        
        # Check status consistency
        if 'status' in document:
            status = document['status']
            if status == 'completed':
                if not document.get('extracted_text'):
                    errors.append("Completed document missing extracted text")
                if not document.get('entities'):
                    errors.append("Completed document missing entities")
            elif status == 'failed':
                if not document.get('error_message'):
                    errors.append("Failed document missing error message")
        
        # Check processing time
        if 'processing_time' in document:
            processing_time = document['processing_time']
            if processing_time < 0:
                errors.append("Invalid processing time: negative value")
            elif processing_time > 3600:  # 1 hour
                errors.append("Processing time too long: over 1 hour")
        
        # Check entity count consistency
        if 'entities' in document and 'entity_count' in document:
            actual_count = len(document['entities'])
            recorded_count = document['entity_count']
            if actual_count != recorded_count:
                errors.append(f"Entity count mismatch: recorded {recorded_count}, actual {actual_count}")
        
        return len(errors) == 0, errors
    
    @staticmethod
    def validate_search_parameters(query: str, n_results: int, max_results: int = 100) -> Tuple[bool, List[str]]:
        """
        Validate search parameters.
        
        Args:
            query: Search query
            n_results: Number of results requested
            max_results: Maximum allowed results
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        if not query or not query.strip():
            errors.append("Search query cannot be empty")
        
        if n_results < 1:
            errors.append("Number of results must be at least 1")
        elif n_results > max_results:
            errors.append(f"Number of results too high: {n_results} (max: {max_results})")
        
        return len(errors) == 0, errors


class RateLimitValidator:
    """Rate limiting validation utilities."""
    
    def __init__(self):
        """Initialize rate limiter."""
        self.request_counts = {}
        self.max_requests_per_minute = 60
        self.max_requests_per_hour = 1000
    
    def check_rate_limit(self, client_id: str) -> Tuple[bool, str]:
        """
        Check if client has exceeded rate limits.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Tuple of (is_allowed, error_message)
        """
        current_time = datetime.now()
        
        # Clean old entries
        self._cleanup_old_entries(current_time)
        
        # Check minute limit
        minute_key = f"{client_id}:{current_time.strftime('%Y%m%d%H%M')}"
        minute_count = self.request_counts.get(minute_key, 0)
        
        if minute_count >= self.max_requests_per_minute:
            return False, "Rate limit exceeded: too many requests per minute"
        
        # Check hour limit
        hour_key = f"{client_id}:{current_time.strftime('%Y%m%d%H')}"
        hour_count = self.request_counts.get(hour_key, 0)
        
        if hour_count >= self.max_requests_per_hour:
            return False, "Rate limit exceeded: too many requests per hour"
        
        # Increment counters
        self.request_counts[minute_key] = minute_count + 1
        self.request_counts[hour_key] = hour_count + 1
        
        return True, ""
    
    def _cleanup_old_entries(self, current_time: datetime):
        """Clean up old rate limit entries."""
        cutoff_time = current_time - timedelta(hours=2)
        cutoff_str = cutoff_time.strftime('%Y%m%d%H%M')
        
        keys_to_remove = []
        for key in self.request_counts.keys():
            if ':' in key:
                timestamp_str = key.split(':')[1]
                if timestamp_str < cutoff_str:
                    keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.request_counts[key]


# Global rate limiter instance
rate_limiter = RateLimitValidator() 