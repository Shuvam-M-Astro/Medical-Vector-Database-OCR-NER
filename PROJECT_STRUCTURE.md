# Medical Vector Database - Project Structure

## Overview
This project implements a comprehensive medical document processing system with OCR, Named Entity Recognition (NER), and vector database storage for search and retrieval.

## Directory Structure

```
medical-vector-database-ner/
├── app/                          # Main application package
│   ├── __init__.py              # Package initialization
│   ├── main.py                  # FastAPI application entry point
│   ├── config.py                # Configuration settings
│   ├── models/                  # Data models
│   │   ├── __init__.py
│   │   ├── document.py          # Document and entity models
│   │   └── response.py          # API response models
│   ├── services/                # Core business logic
│   │   ├── __init__.py
│   │   ├── ocr_service.py       # OCR processing service
│   │   ├── ner_service.py       # Named Entity Recognition service
│   │   ├── vector_service.py    # Vector database operations
│   │   └── document_service.py  # Main document processing pipeline
│   ├── api/                     # API layer
│   │   ├── __init__.py
│   │   ├── routes.py            # FastAPI route definitions
│   │   └── middleware.py        # API middleware
│   └── utils/                   # Utility functions
│       ├── __init__.py
│       ├── file_utils.py        # File handling utilities
│       └── text_utils.py        # Text processing utilities
├── scripts/                     # Utility scripts
│   ├── __init__.py
│   ├── setup_models.py          # Download and setup NER models
│   ├── batch_process.py         # Batch document processing
│   └── test_ocr.py             # OCR testing script
├── tests/                       # Test suite
│   ├── __init__.py
│   ├── test_ocr.py             # OCR service tests
│   ├── test_ner.py             # NER service tests
│   └── test_vector.py          # Vector database tests
├── data/                        # Data directories
│   ├── raw/                    # Raw documents for processing
│   │   └── .gitkeep
│   ├── processed/              # Processed documents and results
│   │   └── .gitkeep
│   └── models/                 # Downloaded ML models
├── config/                      # Configuration files
│   └── settings.yaml           # Application settings
├── logs/                        # Application logs
│   └── .gitkeep
├── requirements.txt             # Python dependencies
├── env.example                 # Environment variables template
├── start.py                    # Startup script
├── README.md                   # Project documentation
└── PROJECT_STRUCTURE.md        # This file
```

## Key Components

### 1. Application Core (`app/`)

#### Main Application (`app/main.py`)
- FastAPI application setup
- Middleware configuration
- Route registration
- Logging setup

#### Configuration (`app/config.py`)
- Environment-based settings
- Default configuration values
- Directory creation utilities

#### Data Models (`app/models/`)
- **Document Models**: Document, Entity, and related data structures
- **Response Models**: API response schemas
- **Enums**: Document status, entity types

### 2. Services (`app/services/`)

#### OCR Service (`app/services/ocr_service.py`)
- Text extraction from images and PDFs
- Image preprocessing for better OCR
- Confidence scoring
- Multiple format support (PDF, JPG, PNG, etc.)

#### NER Service (`app/services/ner_service.py`)
- Medical entity recognition
- Multiple model support (spaCy, transformers)
- Entity type mapping
- Confidence filtering

#### Vector Service (`app/services/vector_service.py`)
- ChromaDB integration
- Document embedding and storage
- Semantic search capabilities
- Metadata management

#### Document Service (`app/services/document_service.py`)
- Orchestrates OCR, NER, and vector operations
- Complete document processing pipeline
- Batch processing support
- Error handling and logging

### 3. API Layer (`app/api/`)

#### Routes (`app/api/routes.py`)
- Document upload and processing
- Search functionality
- Document management (CRUD operations)
- Statistics and health checks

#### Middleware (`app/api/middleware.py`)
- CORS configuration
- Request logging
- Error handling
- Security headers

### 4. Utilities (`app/utils/`)

#### File Utils (`app/utils/file_utils.py`)
- File validation and processing
- Hash calculation
- Temporary file management
- Directory operations

#### Text Utils (`app/utils/text_utils.py`)
- Text cleaning and normalization
- Keyword extraction
- Medical term recognition
- Pattern matching utilities

### 5. Scripts (`scripts/`)

#### Setup Models (`scripts/setup_models.py`)
- Downloads spaCy models
- Installs medical NER models
- Tests model functionality
- Creates necessary directories

#### Batch Processing (`scripts/batch_process.py`)
- Processes multiple documents
- Generates processing reports
- Handles errors gracefully
- Saves results to files

#### OCR Testing (`scripts/test_ocr.py`)
- Tests OCR on single files or directories
- Generates confidence reports
- Saves extracted text
- Performance benchmarking

### 6. Tests (`tests/`)

#### OCR Tests (`tests/test_ocr.py`)
- OCR service functionality
- Image preprocessing
- Confidence calculation
- Error handling

#### NER Tests (`tests/test_ner.py`)
- Entity extraction
- Model loading
- Entity validation
- Medical term recognition

#### Vector Tests (`tests/test_vector.py`)
- Document storage and retrieval
- Search functionality
- Metadata handling
- Performance testing

## Data Flow

1. **Document Upload**: Files are uploaded via API or placed in `data/raw/`
2. **OCR Processing**: Text is extracted from images/PDFs
3. **NER Processing**: Medical entities are identified and extracted
4. **Vector Storage**: Documents are embedded and stored in ChromaDB
5. **Search & Retrieval**: Users can search documents by text or entities

## Configuration

### Environment Variables (`env.example`)
- API settings (host, port)
- Database configuration
- OCR and NER model paths
- File processing limits
- Logging configuration

### Settings File (`config/settings.yaml`)
- Detailed configuration options
- Model parameters
- Processing settings
- Security configurations

## Usage Examples

### Starting the Application
```bash
# Setup environment
python start.py

# Start API server
python -m app.main

# Run tests
pytest tests/

# Process documents
python scripts/batch_process.py --input-dir data/raw

# Test OCR
python scripts/test_ocr.py --file document.pdf
```

### API Usage
```bash
# Upload document
curl -X POST "http://localhost:8000/api/v1/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"

# Search documents
curl -X GET "http://localhost:8000/api/v1/search?query=aspirin&n_results=10"

# Get statistics
curl -X GET "http://localhost:8000/api/v1/stats"
```

## Dependencies

### Core Dependencies
- **FastAPI**: Web framework
- **ChromaDB**: Vector database
- **spaCy**: NLP and NER
- **Transformers**: Medical NER models
- **Pytesseract**: OCR processing
- **OpenCV**: Image preprocessing

### Development Dependencies
- **pytest**: Testing framework
- **black**: Code formatting
- **flake8**: Linting

## File Types Supported

### Input Formats
- **PDF**: Multi-page documents
- **Images**: JPG, JPEG, PNG, TIFF, BMP
- **Text**: Plain text files

### Output Formats
- **JSON**: Processing results
- **Text**: Extracted text
- **Logs**: Processing logs
- **Vectors**: Embeddings in ChromaDB

## Security Considerations

- File size limits
- File type validation
- CORS configuration
- Input sanitization
- Error message filtering

## Performance Optimizations

- Batch processing
- Parallel OCR processing
- Caching of embeddings
- Efficient image preprocessing
- Memory management for large files

## Monitoring and Logging

- Structured logging with loguru
- Processing time tracking
- Error reporting
- Performance metrics
- Health checks

This structure provides a scalable, maintainable, and extensible foundation for medical document processing with comprehensive testing, documentation, and utility scripts. 