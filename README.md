# Medical Vector Database with OCR and NER

A comprehensive system for processing medical invoices and unstructured data using OCR (Optical Character Recognition) and Named Entity Recognition (NER) to create a searchable vector database.

## Features

- **OCR Processing**: Extract text from medical invoices, PDFs, and images
- **Named Entity Recognition**: Identify medical entities like medications, procedures, diagnoses
- **Vector Database**: Store and search processed documents using ChromaDB
- **REST API**: FastAPI-based API for document upload and search
- **Medical NER**: Specialized models for medical text analysis
- **Batch Processing**: Process multiple documents efficiently

## Project Structure

```
medical-vector-database-ner/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── config.py              # Configuration settings
│   ├── models/
│   │   ├── __init__.py
│   │   ├── document.py        # Document data models
│   │   └── response.py        # API response models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ocr_service.py     # OCR processing
│   │   ├── ner_service.py     # Named Entity Recognition
│   │   ├── vector_service.py  # Vector database operations
│   │   └── document_service.py # Document processing pipeline
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py          # API endpoints
│   │   └── middleware.py      # API middleware
│   └── utils/
│       ├── __init__.py
│       ├── file_utils.py      # File handling utilities
│       └── text_utils.py      # Text processing utilities
├── scripts/
│   ├── setup_models.py        # Download and setup NER models
│   ├── batch_process.py       # Batch document processing
│   └── test_ocr.py           # OCR testing script
├── tests/
│   ├── __init__.py
│   ├── test_ocr.py
│   ├── test_ner.py
│   └── test_vector.py
├── data/
│   ├── raw/                   # Raw documents
│   ├── processed/             # Processed documents
│   └── models/               # Downloaded models
├── config/
│   └── settings.yaml         # Configuration file
├── requirements.txt
├── .env.example
└── README.md
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd medical-vector-database-ner
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Download models**:
   ```bash
   python scripts/setup_models.py
   ```

## Usage

### Starting the API Server

```bash
python -m app.main
```

The API will be available at `http://localhost:8000`

### API Endpoints

- `POST /upload` - Upload and process documents
- `GET /search` - Search documents by text
- `GET /documents` - List all documents
- `GET /documents/{id}` - Get specific document
- `DELETE /documents/{id}` - Delete document

### Batch Processing

```bash
python scripts/batch_process.py --input-dir data/raw --output-dir data/processed
```

### Testing OCR

```bash
python scripts/test_ocr.py --image path/to/image.jpg
```

## Configuration

Edit `config/settings.yaml` to configure:
- OCR settings
- NER model parameters
- Vector database settings
- Processing options

## Medical NER Entities

The system recognizes the following medical entities:
- **MEDICATION**: Drug names, dosages, frequencies
- **PROCEDURE**: Medical procedures and treatments
- **DIAGNOSIS**: Medical conditions and diagnoses
- **BODY_PART**: Anatomical locations
- **ORGANIZATION**: Healthcare providers, hospitals
- **PERSON**: Patient names, doctor names
- **DATE**: Important dates and timestamps
- **MONEY**: Costs, charges, payments

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details 