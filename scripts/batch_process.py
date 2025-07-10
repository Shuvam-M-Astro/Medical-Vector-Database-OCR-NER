#!/usr/bin/env python3
"""
Batch processing script for medical documents.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List
import json
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from app.services.document_service import DocumentService
from app.utils.file_utils import validate_file, get_file_info


def find_documents(input_dir: str, extensions: List[str] = None) -> List[str]:
    """
    Find all documents in the input directory.
    
    Args:
        input_dir: Input directory path
        extensions: List of file extensions to include
        
    Returns:
        List of document file paths
    """
    if extensions is None:
        extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.tiff', '.bmp']
    
    documents = []
    input_path = Path(input_dir)
    
    if not input_path.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        return documents
    
    for file_path in input_path.rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in extensions:
            documents.append(str(file_path))
    
    logger.info(f"Found {len(documents)} documents in {input_dir}")
    return documents


def process_documents(documents: List[str], output_dir: str = None) -> dict:
    """
    Process a list of documents.
    
    Args:
        documents: List of document file paths
        output_dir: Output directory for results
        
    Returns:
        Processing results dictionary
    """
    document_service = DocumentService()
    
    results = {
        "total_documents": len(documents),
        "processed": 0,
        "failed": 0,
        "processing_time": 0,
        "documents": []
    }
    
    start_time = datetime.now()
    
    for i, doc_path in enumerate(documents, 1):
        try:
            logger.info(f"Processing document {i}/{len(documents)}: {doc_path}")
            
            # Validate file
            if not validate_file(doc_path):
                logger.warning(f"Skipping invalid file: {doc_path}")
                results["failed"] += 1
                continue
            
            # Get file info
            file_info = get_file_info(doc_path)
            
            # Process document
            document = document_service.process_document(doc_path)
            
            # Save results
            doc_result = {
                "filename": document.filename,
                "document_id": document.id,
                "status": document.status.value,
                "processing_time": document.processing_time,
                "ocr_confidence": document.ocr_confidence,
                "entity_count": document.entity_count,
                "entities": [
                    {
                        "text": entity.text,
                        "type": entity.entity_type.value,
                        "confidence": entity.confidence
                    }
                    for entity in document.entities
                ],
                "file_info": file_info
            }
            
            results["documents"].append(doc_result)
            results["processed"] += 1
            
            logger.info(f"Successfully processed {document.filename}: {document.entity_count} entities")
            
        except Exception as e:
            logger.error(f"Failed to process {doc_path}: {str(e)}")
            results["failed"] += 1
            
            # Add failed document to results
            failed_result = {
                "filename": Path(doc_path).name,
                "status": "failed",
                "error": str(e),
                "processing_time": 0
            }
            results["documents"].append(failed_result)
    
    # Calculate total processing time
    end_time = datetime.now()
    results["processing_time"] = (end_time - start_time).total_seconds()
    
    # Save results to file
    if output_dir:
        save_results(results, output_dir)
    
    return results


def save_results(results: dict, output_dir: str):
    """
    Save processing results to files.
    
    Args:
        results: Processing results
        output_dir: Output directory
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save JSON results
    json_file = output_path / f"batch_results_{timestamp}.json"
    with open(json_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    # Save summary
    summary_file = output_path / f"batch_summary_{timestamp}.txt"
    with open(summary_file, 'w') as f:
        f.write(f"Batch Processing Summary\n")
        f.write(f"=======================\n\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
        f.write(f"Total Documents: {results['total_documents']}\n")
        f.write(f"Successfully Processed: {results['processed']}\n")
        f.write(f"Failed: {results['failed']}\n")
        f.write(f"Total Processing Time: {results['processing_time']:.2f} seconds\n")
        f.write(f"Average Time per Document: {results['processing_time'] / results['total_documents']:.2f} seconds\n\n")
        
        # Entity statistics
        entity_types = {}
        total_entities = 0
        
        for doc in results["documents"]:
            if "entities" in doc:
                for entity in doc["entities"]:
                    entity_type = entity["type"]
                    entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
                    total_entities += 1
        
        f.write(f"Total Entities Found: {total_entities}\n")
        f.write(f"Entity Types:\n")
        for entity_type, count in sorted(entity_types.items()):
            f.write(f"  {entity_type}: {count}\n")
    
    logger.info(f"Results saved to {output_dir}")
    logger.info(f"JSON file: {json_file}")
    logger.info(f"Summary file: {summary_file}")


def print_summary(results: dict):
    """Print processing summary."""
    print("\n" + "="*50)
    print("BATCH PROCESSING SUMMARY")
    print("="*50)
    print(f"Total Documents: {results['total_documents']}")
    print(f"Successfully Processed: {results['processed']}")
    print(f"Failed: {results['failed']}")
    print(f"Processing Time: {results['processing_time']:.2f} seconds")
    print(f"Average Time per Document: {results['processing_time'] / results['total_documents']:.2f} seconds")
    
    # Entity statistics
    entity_types = {}
    total_entities = 0
    
    for doc in results["documents"]:
        if "entities" in doc:
            for entity in doc["entities"]:
                entity_type = entity["type"]
                entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
                total_entities += 1
    
    print(f"\nTotal Entities Found: {total_entities}")
    print("Entity Types:")
    for entity_type, count in sorted(entity_types.items()):
        print(f"  {entity_type}: {count}")
    
    print("="*50)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Batch process medical documents")
    parser.add_argument("--input-dir", required=True, help="Input directory containing documents")
    parser.add_argument("--output-dir", help="Output directory for results")
    parser.add_argument("--extensions", nargs="+", default=[".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".bmp"],
                       help="File extensions to process")
    parser.add_argument("--max-files", type=int, help="Maximum number of files to process")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    
    # Find documents
    documents = find_documents(args.input_dir, args.extensions)
    
    if not documents:
        logger.error("No documents found to process")
        sys.exit(1)
    
    # Limit number of files if specified
    if args.max_files and len(documents) > args.max_files:
        documents = documents[:args.max_files]
        logger.info(f"Limited to {args.max_files} documents")
    
    # Process documents
    logger.info(f"Starting batch processing of {len(documents)} documents...")
    results = process_documents(documents, args.output_dir)
    
    # Print summary
    print_summary(results)
    
    # Exit with error if any documents failed
    if results["failed"] > 0:
        logger.warning(f"{results['failed']} documents failed to process")
        sys.exit(1)
    else:
        logger.info("All documents processed successfully!")


if __name__ == "__main__":
    main() 