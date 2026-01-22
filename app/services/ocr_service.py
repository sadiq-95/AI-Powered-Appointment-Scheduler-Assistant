"""OCR service for text extraction from images."""

import base64
import io
import re
from typing import Tuple

from PIL import Image

from app.exceptions import OCRError
from app.utils.confidence import calculate_ocr_confidence

# Try to import pytesseract, handle gracefully if not installed
try:
    import pytesseract
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


def extract_text_from_image(image_data: str) -> Tuple[str, float]:
    """
    Extract text from a base64-encoded image using Tesseract OCR.
    
    Args:
        image_data: Base64-encoded image string (may include data URI prefix)
        
    Returns:
        Tuple of (extracted_text, confidence_score)
        
    Raises:
        OCRError: If OCR processing fails
    """
    if not TESSERACT_AVAILABLE:
        raise OCRError("Tesseract OCR is not installed. Please install pytesseract and tesseract-ocr.")
    
    try:
        # Remove data URI prefix if present
        if "," in image_data:
            image_data = image_data.split(",", 1)[1]
        
        # Decode base64 image
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if necessary (handles RGBA, grayscale, etc.)
        if image.mode != "RGB":
            image = image.convert("RGB")
        
        # Perform OCR with detailed output
        ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        
        # Extract text and calculate confidence
        texts = []
        confidences = []
        
        for i, text in enumerate(ocr_data["text"]):
            text = text.strip()
            if text:
                texts.append(text)
                conf = ocr_data["conf"][i]
                if conf != -1:  # -1 indicates no confidence data
                    confidences.append(conf / 100.0)  # Convert to 0-1 scale
        
        if not texts:
            raise OCRError("No text could be extracted from the image")
        
        # Combine text and calculate overall confidence
        extracted_text = " ".join(texts)
        
        # Calculate confidence based on OCR output and heuristics
        ocr_confidence = sum(confidences) / len(confidences) if confidences else 0.7
        final_confidence = calculate_ocr_confidence(extracted_text, ocr_confidence)
        
        # Clean up the text
        extracted_text = clean_ocr_text(extracted_text)
        
        return extracted_text, final_confidence
        
    except OCRError:
        raise
    except Exception as e:
        raise OCRError(f"Failed to process image: {str(e)}")


def extract_text_from_raw(text: str) -> Tuple[str, float]:
    """
    Process raw text input (no OCR needed).
    
    Args:
        text: Raw text string
        
    Returns:
        Tuple of (cleaned_text, confidence_score)
    """
    if not text or not text.strip():
        raise OCRError("Empty text input provided")
    
    cleaned_text = clean_ocr_text(text.strip())
    confidence = calculate_ocr_confidence(cleaned_text)
    
    return cleaned_text, confidence


def clean_ocr_text(text: str) -> str:
    """
    Clean up OCR output text.
    
    - Remove excessive whitespace
    - Fix common OCR errors
    - Normalize line breaks
    """
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    # Common OCR error corrections
    corrections = {
        r"\bl\b": "1",  # Standalone 'l' often misread for '1'
        r"\bO\b": "0",  # Standalone 'O' often misread for '0'
        r"1(?=st|nd|rd|th)": "",  # Handle ordinal numbers
    }
    
    # Only apply corrections conservatively
    # These are disabled by default as they can cause issues
    # for text in corrections:
    #     text = re.sub(text, corrections[text], text)
    
    return text


def is_image_content(content: str) -> bool:
    """
    Check if content appears to be base64-encoded image data.
    
    Args:
        content: Content string to check
        
    Returns:
        True if content appears to be base64 image data
    """
    # Check for data URI prefix
    if content.startswith("data:image/"):
        return True
    
    # Check if it looks like base64
    try:
        # Remove any whitespace
        cleaned = content.replace(" ", "").replace("\n", "")
        
        # Check for base64 pattern (simplified check)
        if len(cleaned) > 100 and re.match(r"^[A-Za-z0-9+/]+=*$", cleaned[:100]):
            return True
    except Exception:
        pass
    
    return False
