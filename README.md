# Medical Vector Database with OCR and NER

A comprehensive system for processing medical invoices and unstructured data using OCR (Optical Character Recognition) and Named Entity Recognition (NER) to create a searchable vector database.

## Features

- **OCR Processing**: Extract text from medical invoices, PDFs, and images
- **Named Entity Recognition**: Identify medical entities like medications, procedures, diagnoses
- **Vector Database**: Store and search processed documents using ChromaDB
- **REST API**: FastAPI-based API for document upload and search
- **Web Dashboard**: Modern React frontend for document management and search
- **Medical NER**: Specialized models for medical text analysis
- **Batch Processing**: Process multiple documents efficiently

## Project Structure

```
medical-vector-database-ner/
├── app/                       # Backend API
│   ├── __init__.py
│   ├── main.py               # FastAPI application
│   ├── config.py             # Configuration settings
│   ├── models/               # Data models
│   ├── services/             # Business logic
│   ├── api/                  # API routes
│   └── utils/                # Utilities
├── frontend/                 # React Dashboard
│   ├── src/
│   │   ├── components/       # UI components
│   │   ├── pages/           # Page components
│   │   ├── services/        # API services
│   │   └── types/           # TypeScript types
│   ├── package.json
│   └── README.md
├── scripts/                  # Utility scripts
├── tests/                    # Backend tests
├── data/                     # Data storage
├── config/                   # Configuration
├── requirements.txt          # Python dependencies
└── README.md
```

## Installation

### Backend Setup

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

### Frontend Setup

1. **Install Node.js** (version 16+):
   - Download from https://nodejs.org/

2. **Install frontend dependencies**:
   ```bash
   cd frontend
   npm install
   ```

3. **Start the frontend**:
   ```bash
   npm run dev
   ```

The dashboard will be available at `http://localhost:3000`

## Usage

### Starting the Backend API

```bash
python -m app.main
```

The API will be available at `http://localhost:8000`

### Using the Web Dashboard

1. **Start the backend API** (see above)
2. **Start the frontend**:
   ```bash
   cd frontend
   npm run dev
   ```
3. **Open your browser** to `http://localhost:3000`

### Dashboard Features

- **Upload Documents**: Drag-and-drop interface for uploading medical documents
- **Search**: Advanced search with entity filtering and confidence scoring
- **Document Management**: View, delete, and manage all uploaded documents
- **Analytics**: Charts and statistics for processing insights
- **Real-time Updates**: Live updates of processing status and results

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