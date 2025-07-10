"""
OCR service for extracting text from medical documents.
"""

import os
import cv2
import numpy as np
from PIL import Image
import pytesseract
from pdf2image import convert_from_path
from PyPDF2 import PdfReader
from typing import Tuple, Optional, List
from loguru import logger

from ..config import settings


class OCRService:
    """OCR service for medical document text extraction."""
    
    def __init__(self):
        """Initialize OCR service."""
        self.language = settings.OCR_LANGUAGE
        self.config = settings.OCR_CONFIG
        
        # Set tesseract path if provided
        if settings.TESSERACT_PATH:
            pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_PATH
    
    def extract_text_from_image(self, image_path: str) -> Tuple[str, float]:
        """
        Extract text from an image file.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        try:
            # Load and preprocess image
            image = self._preprocess_image(image_path)
            
            # Extract text with confidence
            data = pytesseract.image_to_data(
                image, 
                lang=self.language, 
                config=self.config,
                output_type=pytesseract.Output.DICT
            )
            
            # Extract text and confidence
            text = pytesseract.image_to_string(image, lang=self.language, config=self.config)
            confidence = self._calculate_confidence(data)
            
            logger.info(f"OCR extracted {len(text)} characters with {confidence:.2f} confidence")
            return text.strip(), confidence
            
        except Exception as e:
            logger.error(f"OCR extraction failed for {image_path}: {str(e)}")
            raise
    
    def extract_text_from_pdf(self, pdf_path: str) -> List[Tuple[str, float]]:
        """
        Extract text from a PDF file.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of (page_text, confidence) tuples
        """
        try:
            results = []
            
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=300)
            
            for i, image in enumerate(images):
                # Convert PIL image to OpenCV format for preprocessing
                opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
                
                # Preprocess the image
                processed_image = self._preprocess_opencv_image(opencv_image)
                
                # Extract text
                text = pytesseract.image_to_string(
                    processed_image, 
                    lang=self.language, 
                    config=self.config
                )
                
                # Get confidence data
                data = pytesseract.image_to_data(
                    processed_image,
                    lang=self.language,
                    config=self.config,
                    output_type=pytesseract.Output.DICT
                )
                
                confidence = self._calculate_confidence(data)
                results.append((text.strip(), confidence))
                
                logger.info(f"PDF page {i+1}: {len(text)} characters, {confidence:.2f} confidence")
            
            return results
            
        except Exception as e:
            logger.error(f"PDF OCR extraction failed for {pdf_path}: {str(e)}")
            raise
    
    def _preprocess_image(self, image_path: str) -> Image.Image:
        """
        Preprocess image for better OCR results.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Preprocessed PIL Image
        """
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply preprocessing
        processed = self._preprocess_opencv_image(gray)
        
        # Convert back to PIL
        return Image.fromarray(processed)
    
    def _preprocess_opencv_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess OpenCV image for better OCR.
        
        Args:
            image: OpenCV image array
            
        Returns:
            Preprocessed image array
        """
        # Ensure grayscale
        if len(image.shape) == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Resize if too small
        height, width = image.shape
        if width < 1000:
            scale = 1000 / width
            image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        
        # Apply noise reduction
        image = cv2.medianBlur(image, 3)
        
        # Apply thresholding
        _, image = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Apply morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
        
        return image
    
    def _calculate_confidence(self, data: dict) -> float:
        """
        Calculate average confidence from OCR data.
        
        Args:
            data: OCR data dictionary
            
        Returns:
            Average confidence score
        """
        confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
        return np.mean(confidences) / 100.0 if confidences else 0.0
    
    def validate_file(self, file_path: str) -> bool:
        """
        Validate if file can be processed by OCR.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file can be processed
        """
        if not os.path.exists(file_path):
            return False
        
        # Check file extension
        ext = os.path.splitext(file_path)[1].lower()
        return ext in ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.bmp']
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats."""
        return ['PDF', 'JPG', 'JPEG', 'PNG', 'TIFF', 'BMP'] 