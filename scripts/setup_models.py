#!/usr/bin/env python3
"""
Script to download and setup NER models for the medical vector database.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger


def install_spacy_models():
    """Install required spaCy models."""
    models = [
        "en_core_web_sm",
        "en_core_sci_md"
    ]
    
    for model in models:
        try:
            logger.info(f"Installing spaCy model: {model}")
            subprocess.run([
                sys.executable, "-m", "spacy", "download", model
            ], check=True)
            logger.info(f"Successfully installed {model}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install {model}: {e}")
            return False
    
    return True


def install_scispacy():
    """Install scispacy and medical models."""
    try:
        logger.info("Installing scispacy...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "scispacy"
        ], check=True)
        
        # Install medical models
        medical_models = [
            "https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.3/en_core_sci_sm-0.5.3.tar.gz",
            "https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.3/en_core_sci_md-0.5.3.tar.gz"
        ]
        
        for model_url in medical_models:
            logger.info(f"Installing medical model: {model_url}")
            subprocess.run([
                sys.executable, "-m", "pip", "install", model_url
            ], check=True)
        
        logger.info("Successfully installed scispacy and medical models")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install scispacy: {e}")
        return False


def install_med7():
    """Install Med7 model."""
    try:
        logger.info("Installing Med7...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "med7"
        ], check=True)
        
        # Download Med7 model
        subprocess.run([
            sys.executable, "-m", "med7.download"
        ], check=True)
        
        logger.info("Successfully installed Med7")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install Med7: {e}")
        return False


def test_models():
    """Test if models are working correctly."""
    try:
        import spacy
        from transformers import pipeline
        
        logger.info("Testing spaCy models...")
        
        # Test basic spaCy model
        nlp = spacy.load("en_core_web_sm")
        doc = nlp("Patient John Smith was diagnosed with diabetes.")
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        logger.info(f"Basic NER test: {entities}")
        
        # Test medical spaCy model
        try:
            medical_nlp = spacy.load("en_core_sci_md")
            medical_doc = medical_nlp("The patient was prescribed Aspirin 100mg.")
            medical_entities = [(ent.text, ent.label_) for ent in medical_doc.ents]
            logger.info(f"Medical NER test: {medical_entities}")
        except OSError:
            logger.warning("Medical spaCy model not available")
        
        # Test transformer model
        logger.info("Testing transformer model...")
        ner_pipeline = pipeline("ner", model="dmis-lab/biobert-base-cased-v1.1")
        results = ner_pipeline("Patient was given Aspirin for pain.")
        logger.info(f"Transformer NER test: {results[:3]}")  # Show first 3 results
        
        logger.info("All model tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"Model test failed: {e}")
        return False


def create_model_directories():
    """Create necessary directories for models."""
    directories = [
        "data/models",
        "data/raw",
        "data/processed",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {directory}")


def main():
    """Main setup function."""
    logger.info("Starting model setup...")
    
    # Create directories
    create_model_directories()
    
    # Install models
    success = True
    
    if not install_spacy_models():
        success = False
    
    if not install_scispacy():
        logger.warning("Scispacy installation failed, continuing...")
    
    if not install_med7():
        logger.warning("Med7 installation failed, continuing...")
    
    # Test models
    if not test_models():
        success = False
    
    if success:
        logger.info("Model setup completed successfully!")
        logger.info("You can now run the medical vector database application.")
    else:
        logger.error("Model setup failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main() 