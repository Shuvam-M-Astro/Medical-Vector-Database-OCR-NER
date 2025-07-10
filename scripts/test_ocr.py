#!/usr/bin/env python3
"""
OCR testing script for medical documents.
"""

import os
import sys
import argparse
from pathlib import Path
import json
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from app.services.ocr_service import OCRService
from app.utils.file_utils import validate_file, get_file_info


def test_ocr_on_file(file_path: str, save_output: bool = False) -> dict:
    """
    Test OCR on a single file.
    
    Args:
        file_path: Path to the file to test
        save_output: Whether to save OCR output to file
        
    Returns:
        OCR test results
    """
    ocr_service = OCRService()
    
    # Get file info
    file_info = get_file_info(file_path)
    
    # Test OCR
    start_time = datetime.now()
    
    try:
        if file_path.lower().endswith('.pdf'):
            # Test PDF OCR
            page_results = ocr_service.extract_text_from_pdf(file_path)
            extracted_text = " ".join([text for text, _ in page_results])
            confidence = sum(conf for _, conf in page_results) / len(page_results) if page_results else 0
            page_count = len(page_results)
        else:
            # Test image OCR
            extracted_text, confidence = ocr_service.extract_text_from_image(file_path)
            page_count = 1
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        results = {
            "filename": file_info["filename"],
            "file_path": file_path,
            "file_size": file_info["file_size"],
            "file_type": file_info["file_extension"],
            "success": True,
            "extracted_text": extracted_text,
            "text_length": len(extracted_text),
            "confidence": confidence,
            "processing_time": processing_time,
            "page_count": page_count,
            "file_info": file_info
        }
        
        # Save output if requested
        if save_output:
            output_dir = Path("test_output")
            output_dir.mkdir(exist_ok=True)
            
            # Save extracted text
            text_file = output_dir / f"{file_info['filename']}_ocr.txt"
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(extracted_text)
            
            # Save results JSON
            json_file = output_dir / f"{file_info['filename']}_results.json"
            with open(json_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            results["output_files"] = {
                "text_file": str(text_file),
                "json_file": str(json_file)
            }
        
        return results
        
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "filename": file_info["filename"],
            "file_path": file_path,
            "file_size": file_info["file_size"],
            "file_type": file_info["file_extension"],
            "success": False,
            "error": str(e),
            "processing_time": processing_time,
            "file_info": file_info
        }


def test_ocr_on_directory(directory: str, save_output: bool = False) -> dict:
    """
    Test OCR on all files in a directory.
    
    Args:
        directory: Directory to test
        save_output: Whether to save OCR output
        
    Returns:
        Batch test results
    """
    ocr_service = OCRService()
    supported_formats = ocr_service.get_supported_formats()
    
    # Find all files
    files = []
    for file_path in Path(directory).rglob("*"):
        if file_path.is_file() and file_path.suffix.lower() in [f.lower() for f in supported_formats]:
            files.append(str(file_path))
    
    logger.info(f"Found {len(files)} files to test in {directory}")
    
    results = {
        "directory": directory,
        "total_files": len(files),
        "successful": 0,
        "failed": 0,
        "total_processing_time": 0,
        "average_confidence": 0,
        "total_text_length": 0,
        "files": []
    }
    
    confidences = []
    text_lengths = []
    
    for i, file_path in enumerate(files, 1):
        logger.info(f"Testing file {i}/{len(files)}: {file_path}")
        
        file_result = test_ocr_on_file(file_path, save_output)
        results["files"].append(file_result)
        
        if file_result["success"]:
            results["successful"] += 1
            confidences.append(file_result["confidence"])
            text_lengths.append(file_result["text_length"])
        else:
            results["failed"] += 1
        
        results["total_processing_time"] += file_result["processing_time"]
    
    # Calculate averages
    if confidences:
        results["average_confidence"] = sum(confidences) / len(confidences)
    if text_lengths:
        results["total_text_length"] = sum(text_lengths)
    
    return results


def print_results(results: dict):
    """Print OCR test results."""
    if "directory" in results:
        # Batch results
        print("\n" + "="*60)
        print("OCR BATCH TEST RESULTS")
        print("="*60)
        print(f"Directory: {results['directory']}")
        print(f"Total Files: {results['total_files']}")
        print(f"Successful: {results['successful']}")
        print(f"Failed: {results['failed']}")
        print(f"Success Rate: {results['successful']/results['total_files']*100:.1f}%")
        print(f"Total Processing Time: {results['total_processing_time']:.2f} seconds")
        print(f"Average Processing Time: {results['total_processing_time']/results['total_files']:.2f} seconds")
        print(f"Average Confidence: {results['average_confidence']:.3f}")
        print(f"Total Text Extracted: {results['total_text_length']} characters")
        
        # Show failed files
        failed_files = [f for f in results["files"] if not f["success"]]
        if failed_files:
            print(f"\nFailed Files:")
            for file_result in failed_files:
                print(f"  {file_result['filename']}: {file_result['error']}")
        
        # Show best and worst results
        successful_files = [f for f in results["files"] if f["success"]]
        if successful_files:
            best_file = max(successful_files, key=lambda x: x["confidence"])
            worst_file = min(successful_files, key=lambda x: x["confidence"])
            
            print(f"\nBest Result:")
            print(f"  {best_file['filename']}: {best_file['confidence']:.3f} confidence")
            print(f"Worst Result:")
            print(f"  {worst_file['filename']}: {worst_file['confidence']:.3f} confidence")
    
    else:
        # Single file results
        print("\n" + "="*60)
        print("OCR SINGLE FILE TEST RESULTS")
        print("="*60)
        print(f"File: {results['filename']}")
        print(f"Type: {results['file_type']}")
        print(f"Size: {results['file_size']} bytes")
        print(f"Success: {results['success']}")
        print(f"Processing Time: {results['processing_time']:.2f} seconds")
        
        if results['success']:
            print(f"Text Length: {results['text_length']} characters")
            print(f"Confidence: {results['confidence']:.3f}")
            print(f"Page Count: {results['page_count']}")
            
            # Show first 200 characters of extracted text
            text_preview = results['extracted_text'][:200]
            if len(results['extracted_text']) > 200:
                text_preview += "..."
            print(f"\nText Preview:\n{text_preview}")
        else:
            print(f"Error: {results['error']}")
    
    print("="*60)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Test OCR on medical documents")
    parser.add_argument("--file", help="Single file to test")
    parser.add_argument("--directory", help="Directory to test")
    parser.add_argument("--save-output", action="store_true", help="Save OCR output to files")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Configure logging
    if args.verbose:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    
    if not args.file and not args.directory:
        parser.error("Please specify either --file or --directory")
    
    if args.file:
        # Test single file
        if not os.path.exists(args.file):
            logger.error(f"File not found: {args.file}")
            sys.exit(1)
        
        if not validate_file(args.file):
            logger.error(f"Invalid file: {args.file}")
            sys.exit(1)
        
        logger.info(f"Testing OCR on file: {args.file}")
        results = test_ocr_on_file(args.file, args.save_output)
        print_results(results)
        
    elif args.directory:
        # Test directory
        if not os.path.exists(args.directory):
            logger.error(f"Directory not found: {args.directory}")
            sys.exit(1)
        
        logger.info(f"Testing OCR on directory: {args.directory}")
        results = test_ocr_on_directory(args.directory, args.save_output)
        print_results(results)
        
        # Save batch results
        if args.save_output:
            output_dir = Path("test_output")
            output_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            batch_file = output_dir / f"batch_ocr_results_{timestamp}.json"
            
            with open(batch_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            
            logger.info(f"Batch results saved to: {batch_file}")


if __name__ == "__main__":
    main() 