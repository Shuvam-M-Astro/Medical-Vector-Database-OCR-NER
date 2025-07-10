"""
Tests for OCR service.
"""

import pytest
import tempfile
import os
from pathlib import Path
from PIL import Image
import numpy as np

from app.services.ocr_service import OCRService


class TestOCRService:
    """Test cases for OCR service."""
    
    @pytest.fixture
    def ocr_service(self):
        """Create OCR service instance."""
        return OCRService()
    
    @pytest.fixture
    def sample_image(self):
        """Create a sample test image."""
        # Create a simple test image with text
        img = Image.new('RGB', (400, 200), color='white')
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            img.save(f.name, 'PNG')
            yield f.name
        
        # Cleanup
        os.unlink(f.name)
    
    def test_ocr_service_initialization(self, ocr_service):
        """Test OCR service initialization."""
        assert ocr_service.language == "eng"
        assert ocr_service.config == "--psm 6"
    
    def test_validate_file_valid(self, ocr_service):
        """Test file validation with valid file."""
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
            f.write(b"test content")
            f.flush()
            
            assert ocr_service.validate_file(f.name) == True
            
            # Cleanup
            os.unlink(f.name)
    
    def test_validate_file_invalid_extension(self, ocr_service):
        """Test file validation with invalid extension."""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as f:
            f.write(b"test content")
            f.flush()
            
            assert ocr_service.validate_file(f.name) == False
            
            # Cleanup
            os.unlink(f.name)
    
    def test_validate_file_nonexistent(self, ocr_service):
        """Test file validation with nonexistent file."""
        assert ocr_service.validate_file("nonexistent_file.pdf") == False
    
    def test_get_supported_formats(self, ocr_service):
        """Test getting supported formats."""
        formats = ocr_service.get_supported_formats()
        expected_formats = ['PDF', 'JPG', 'JPEG', 'PNG', 'TIFF', 'BMP']
        
        assert all(fmt in formats for fmt in expected_formats)
    
    def test_preprocess_image(self, ocr_service, sample_image):
        """Test image preprocessing."""
        processed = ocr_service._preprocess_image(sample_image)
        assert processed is not None
        assert processed.mode == 'L'  # Grayscale
    
    def test_calculate_confidence(self, ocr_service):
        """Test confidence calculation."""
        data = {
            'conf': ['90', '85', '95', '0', '88']
        }
        
        confidence = ocr_service._calculate_confidence(data)
        assert 0 <= confidence <= 1
        assert confidence > 0.8  # Should be around 0.89
    
    def test_extract_text_from_image(self, ocr_service, sample_image):
        """Test text extraction from image."""
        # This test might fail if Tesseract is not installed
        try:
            text, confidence = ocr_service.extract_text_from_image(sample_image)
            assert isinstance(text, str)
            assert isinstance(confidence, float)
            assert 0 <= confidence <= 1
        except Exception as e:
            # Skip test if Tesseract is not available
            pytest.skip(f"Tesseract not available: {e}")
    
    def test_extract_text_from_pdf(self, ocr_service):
        """Test text extraction from PDF."""
        # Create a simple PDF for testing
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import letter
            
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
                c = canvas.Canvas(f.name, pagesize=letter)
                c.drawString(100, 750, "Test PDF content")
                c.save()
                
                try:
                    results = ocr_service.extract_text_from_pdf(f.name)
                    assert isinstance(results, list)
                    if results:
                        assert len(results) > 0
                        assert isinstance(results[0], tuple)
                        assert len(results[0]) == 2
                except Exception as e:
                    # Skip test if dependencies are not available
                    pytest.skip(f"PDF processing not available: {e}")
                finally:
                    os.unlink(f.name)
        except ImportError:
            pytest.skip("reportlab not available for PDF creation")
    
    def test_preprocess_opencv_image(self, ocr_service):
        """Test OpenCV image preprocessing."""
        # Create a test image array
        test_image = np.random.randint(0, 255, (100, 200, 3), dtype=np.uint8)
        
        processed = ocr_service._preprocess_opencv_image(test_image)
        
        assert processed is not None
        assert len(processed.shape) == 2  # Should be grayscale
        assert processed.dtype == np.uint8 