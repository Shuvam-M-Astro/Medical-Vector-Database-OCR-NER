"""
Text utility functions for processing extracted text.
"""

import re
import string
from typing import List, Dict, Any
from collections import Counter
import unicodedata


def clean_text(text: str) -> str:
    """
    Clean and normalize text.
    
    Args:
        text: Raw text to clean
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove special characters but keep medical terms
    text = re.sub(r'[^\w\s\-\.\,\;\:\!\?\(\)\[\]\{\}]', ' ', text)
    
    # Normalize unicode
    text = unicodedata.normalize('NFKC', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def normalize_text(text: str) -> str:
    """
    Normalize text for better processing.
    
    Args:
        text: Text to normalize
        
    Returns:
        Normalized text
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove punctuation except medical terms
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def extract_keywords(text: str, min_length: int = 3, max_keywords: int = 50) -> List[str]:
    """
    Extract keywords from text.
    
    Args:
        text: Text to extract keywords from
        min_length: Minimum keyword length
        max_keywords: Maximum number of keywords to return
        
    Returns:
        List of keywords
    """
    if not text:
        return []
    
    # Clean text
    cleaned_text = clean_text(text)
    
    # Split into words
    words = cleaned_text.split()
    
    # Filter words
    keywords = []
    for word in words:
        word = word.lower().strip()
        
        # Skip short words and common stop words
        if (len(word) >= min_length and 
            word not in get_stop_words() and
            not word.isdigit()):
            keywords.append(word)
    
    # Count frequency
    word_counts = Counter(keywords)
    
    # Return most common keywords
    return [word for word, count in word_counts.most_common(max_keywords)]


def get_stop_words() -> set:
    """Get common stop words."""
    return {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
        'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her',
        'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their',
        'mine', 'yours', 'his', 'hers', 'ours', 'theirs'
    }


def extract_medical_terms(text: str) -> List[str]:
    """
    Extract potential medical terms from text.
    
    Args:
        text: Text to extract medical terms from
        
    Returns:
        List of potential medical terms
    """
    if not text:
        return []
    
    # Medical term patterns
    patterns = [
        r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b',  # Capitalized terms
        r'\b\d+(?:\.\d+)?\s*(?:mg|ml|g|kg|mcg|units?)\b',  # Dosages
        r'\b(?:patient|doctor|nurse|hospital|clinic|medical|treatment|diagnosis|symptom|condition|disease|infection|injury|surgery|procedure|medication|drug|prescription|dose|dosage|tablet|capsule|injection|iv|oral|topical)\b',
        r'\b(?:heart|lung|liver|kidney|brain|stomach|intestine|muscle|bone|blood|nerve|artery|vein|joint|spine|skull|chest|abdomen|pelvis|limb|hand|foot|eye|ear|nose|mouth|throat)\b',
        r'\b(?:hypertension|diabetes|cancer|arthritis|asthma|pneumonia|bronchitis|hepatitis|nephritis|carditis|gastritis|colitis|dermatitis|meningitis|encephalitis)\b'
    ]
    
    medical_terms = set()
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        medical_terms.update(matches)
    
    return list(medical_terms)


def extract_numbers(text: str) -> List[Dict[str, Any]]:
    """
    Extract numbers and their context from text.
    
    Args:
        text: Text to extract numbers from
        
    Returns:
        List of number information dictionaries
    """
    if not text:
        return []
    
    numbers = []
    
    # Pattern for various number formats
    patterns = [
        (r'\b(\d+(?:\.\d+)?)\s*(mg|ml|g|kg|mcg|units?)\b', 'dosage'),
        (r'\b(\d+(?:\.\d+)?)\s*(years?|months?|weeks?|days?|hours?|minutes?)\b', 'duration'),
        (r'\b(\d+(?:\.\d+)?)\s*(dollars?|cents?|usd|eur|gbp)\b', 'money'),
        (r'\b(\d{1,2}):(\d{2})\s*(am|pm)?\b', 'time'),
        (r'\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b', 'date'),
        (r'\b(\d+(?:\.\d+)?)\s*(percent|%)\b', 'percentage'),
        (r'\b(\d+(?:\.\d+)?)\s*(temperature|temp|fahrenheit|f|celsius|c)\b', 'temperature'),
        (r'\b(\d+(?:\.\d+)?)\s*(pounds?|lbs?|kilograms?|kg)\b', 'weight'),
        (r'\b(\d+(?:\.\d+)?)\s*(inches?|in|centimeters?|cm|meters?|m)\b', 'measurement')
    ]
    
    for pattern, number_type in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            numbers.append({
                'value': match.group(1),
                'unit': match.group(2) if len(match.groups()) > 1 else None,
                'type': number_type,
                'start': match.start(),
                'end': match.end(),
                'full_match': match.group(0)
            })
    
    return numbers


def extract_dates(text: str) -> List[Dict[str, Any]]:
    """
    Extract dates from text.
    
    Args:
        text: Text to extract dates from
        
    Returns:
        List of date information dictionaries
    """
    if not text:
        return []
    
    dates = []
    
    # Date patterns
    patterns = [
        (r'\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b', 'MM/DD/YYYY'),
        (r'\b(\d{1,2})-(\d{1,2})-(\d{2,4})\b', 'MM-DD-YYYY'),
        (r'\b(\d{4})-(\d{1,2})-(\d{1,2})\b', 'YYYY-MM-DD'),
        (r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{1,2}),?\s+(\d{4})\b', 'Month DD, YYYY'),
        (r'\b(\d{1,2})\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})\b', 'DD Month YYYY')
    ]
    
    for pattern, format_type in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            dates.append({
                'date': match.group(0),
                'format': format_type,
                'start': match.start(),
                'end': match.end(),
                'groups': match.groups()
            })
    
    return dates


def extract_emails(text: str) -> List[str]:
    """
    Extract email addresses from text.
    
    Args:
        text: Text to extract emails from
        
    Returns:
        List of email addresses
    """
    if not text:
        return []
    
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(email_pattern, text)


def extract_phone_numbers(text: str) -> List[str]:
    """
    Extract phone numbers from text.
    
    Args:
        text: Text to extract phone numbers from
        
    Returns:
        List of phone numbers
    """
    if not text:
        return []
    
    phone_patterns = [
        r'\b\d{3}-\d{3}-\d{4}\b',  # 123-456-7890
        r'\b\(\d{3}\)\s*\d{3}-\d{4}\b',  # (123) 456-7890
        r'\b\d{3}\.\d{3}\.\d{4}\b',  # 123.456.7890
        r'\b\d{10}\b',  # 1234567890
        r'\b\+\d{1,3}\s*\d{3}\s*\d{3}\s*\d{4}\b'  # +1 123 456 7890
    ]
    
    phone_numbers = []
    for pattern in phone_patterns:
        matches = re.findall(pattern, text)
        phone_numbers.extend(matches)
    
    return phone_numbers 