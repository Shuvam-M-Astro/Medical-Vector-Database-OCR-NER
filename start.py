#!/usr/bin/env python3
"""
Startup script for the Medical Vector Database application.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = [
        'fastapi',
        'uvicorn',
        'pydantic',
        'chromadb',
        'sentence-transformers',
        'pytesseract',
        'Pillow',
        'pdf2image',
        'spacy',
        'transformers',
        'torch',
        'opencv-python',
        'loguru'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("Missing required packages:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nPlease install missing packages with:")
        print("pip install -r requirements.txt")
        return False
    
    return True


def check_tesseract():
    """Check if Tesseract OCR is installed."""
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        print("✓ Tesseract OCR is available")
        return True
    except Exception as e:
        print("✗ Tesseract OCR not found or not working")
        print("Please install Tesseract OCR:")
        print("  Windows: https://github.com/UB-Mannheim/tesseract/wiki")
        print("  macOS: brew install tesseract")
        print("  Ubuntu: sudo apt-get install tesseract-ocr")
        return False


def check_spacy_models():
    """Check if spaCy models are installed."""
    try:
        import spacy
        spacy.load('en_core_web_sm')
        print("✓ Basic spaCy model is available")
        
        # Try to load medical model
        try:
            spacy.load('en_core_sci_md')
            print("✓ Medical spaCy model is available")
        except OSError:
            print("⚠ Medical spaCy model not found")
            print("Run: python scripts/setup_models.py")
        
        return True
    except Exception as e:
        print("✗ spaCy models not found")
        print("Run: python scripts/setup_models.py")
        return False


def create_directories():
    """Create necessary directories."""
    directories = [
        'data/raw',
        'data/processed',
        'data/models',
        'logs',
        'test_output'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✓ Directories created")


def setup_environment():
    """Setup environment variables."""
    env_file = Path('.env')
    if not env_file.exists():
        env_example = Path('env.example')
        if env_example.exists():
            import shutil
            shutil.copy('env.example', '.env')
            print("✓ Created .env file from template")
        else:
            print("⚠ No .env file found, using default settings")


def main():
    """Main startup function."""
    print("Medical Vector Database - Startup Check")
    print("=" * 50)
    
    # Check dependencies
    print("\nChecking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    
    # Check Tesseract
    print("\nChecking OCR...")
    if not check_tesseract():
        print("⚠ OCR may not work properly")
    
    # Check spaCy models
    print("\nChecking NER models...")
    if not check_spacy_models():
        print("⚠ NER may not work properly")
    
    # Create directories
    print("\nSetting up directories...")
    create_directories()
    
    # Setup environment
    print("\nSetting up environment...")
    setup_environment()
    
    print("\n" + "=" * 50)
    print("Setup complete!")
    print("\nTo start the API server:")
    print("  python -m app.main")
    print("\nTo run tests:")
    print("  pytest tests/")
    print("\nTo process documents:")
    print("  python scripts/batch_process.py --input-dir data/raw")
    print("\nTo test OCR:")
    print("  python scripts/test_ocr.py --file path/to/document.pdf")


if __name__ == "__main__":
    main() 