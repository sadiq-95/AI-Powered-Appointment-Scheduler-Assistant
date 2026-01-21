"""Confidence scoring utilities."""

from typing import Optional


# Confidence thresholds
MIN_OCR_CONFIDENCE = 0.5
MIN_EXTRACTION_CONFIDENCE = 0.6
MIN_NORMALIZATION_CONFIDENCE = 0.7


def calculate_ocr_confidence(text: str, original_confidence: Optional[float] = None) -> float:
    """
    Calculate confidence score for OCR output.
    
    Uses heuristics based on:
    - Character quality (no excessive special characters)
    - Word completeness (average word length)
    - Original OCR confidence if available
    """
    if not text or not text.strip():
        return 0.0
    
    text = text.strip()
    
    # Start with original confidence or base score
    confidence = original_confidence if original_confidence is not None else 0.8
    
    # Check for excessive special characters (indicates noise)
    special_char_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / len(text)
    if special_char_ratio > 0.3:
        confidence *= 0.6
    elif special_char_ratio > 0.15:
        confidence *= 0.8
    
    # Check average word length (very short or very long words are suspicious)
    words = text.split()
    if words:
        avg_word_len = sum(len(w) for w in words) / len(words)
        if avg_word_len < 2 or avg_word_len > 15:
            confidence *= 0.7
    
    # Check for minimum meaningful content
    if len(text) < 5:
        confidence *= 0.5
    
    return round(min(max(confidence, 0.0), 1.0), 2)


def calculate_extraction_confidence(
    entities: dict, 
    has_date: bool = False, 
    has_time: bool = False, 
    has_department: bool = False
) -> float:
    """
    Calculate confidence score for entity extraction.
    
    Higher confidence when more entities are found.
    """
    confidence = 0.7  # Base confidence
    
    found_count = sum([has_date, has_time, has_department])
    
    if found_count == 3:
        confidence = 0.95
    elif found_count == 2:
        confidence = 0.85
    elif found_count == 1:
        confidence = 0.70
    else:
        confidence = 0.40
    
    return round(confidence, 2)


def calculate_normalization_confidence(
    date_parsed: bool,
    time_parsed: bool,
    is_relative: bool = False
) -> float:
    """
    Calculate confidence score for normalization.
    
    Lower confidence for relative dates, higher for absolute dates.
    """
    if not date_parsed and not time_parsed:
        return 0.0
    
    confidence = 0.9
    
    if not date_parsed:
        confidence *= 0.5
    if not time_parsed:
        confidence *= 0.7
    
    # Relative dates have slightly lower confidence
    if is_relative:
        confidence *= 0.95
    
    return round(min(max(confidence, 0.0), 1.0), 2)


def meets_threshold(confidence: float, stage: str) -> bool:
    """Check if confidence meets the threshold for a given stage."""
    thresholds = {
        "ocr": MIN_OCR_CONFIDENCE,
        "extraction": MIN_EXTRACTION_CONFIDENCE,
        "normalization": MIN_NORMALIZATION_CONFIDENCE,
    }
    return confidence >= thresholds.get(stage, 0.5)
