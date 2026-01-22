"""OCR service for text extraction from images."""

import base64
import io
import re
from typing import Tuple

from PIL import Image

from app.exceptions import OCRError
from app.utils.confidence import calculate_ocr_confidence
from app.config import get_settings

# Try to import pytesseract, handle gracefully if not installed
try:
    import pytesseract
    # Check if tesseract binary is actually available
    try:
        pytesseract.get_tesseract_version()
        TESSERACT_AVAILABLE = True
    except pytesseract.TesseractNotFoundError:
        TESSERACT_AVAILABLE = False
except ImportError:
    TESSERACT_AVAILABLE = False

# Try to import Google Generative AI for vision fallback
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


def extract_text_with_gemini_vision(image_data: str) -> Tuple[str, float]:
    """
    Extract text from an image using Gemini Vision API.
    
    Args:
        image_data: Base64-encoded image string
        
    Returns:
        Tuple of (extracted_text, confidence_score)
    """
    if not GEMINI_AVAILABLE:
        raise OCRError("Gemini API not available for vision-based OCR")
    
    settings = get_settings()
    if not settings.gemini_api_key:
        raise OCRError("GEMINI_API_KEY not configured for vision-based OCR")
    
    try:
        # Remove data URI prefix if present
        if "," in image_data:
            image_data = image_data.split(",", 1)[1]
        
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(settings.gemini_model_name)
        
        # Create the image part for the API
        image_part = {
            "mime_type": "image/jpeg",
            "data": image_data
        }
        
        prompt = """Extract all text from this image exactly as written. 
Return ONLY the extracted text, nothing else. 
If there is no text visible, respond with 'NO_TEXT_FOUND'."""
        
        response = model.generate_content([prompt, image_part])
        
        extracted_text = response.text.strip()
        
        if extracted_text == "NO_TEXT_FOUND" or not extracted_text:
            raise OCRError("No text could be extracted from the image")
        
        # Clean up the text
        extracted_text = clean_ocr_text(extracted_text)
        
        # Calculate confidence (Gemini vision is generally reliable)
        confidence = calculate_ocr_confidence(extracted_text, 0.85)
        
        return extracted_text, confidence
        
    except OCRError:
        raise
    except Exception as e:
        raise OCRError(f"Gemini Vision OCR failed: {str(e)}")


def extract_text_from_image(image_data: str) -> Tuple[str, float]:
    """
    Extract text from a base64-encoded image.
    
    Uses Tesseract OCR if available, otherwise falls back to Gemini Vision API.
    
    Args:
        image_data: Base64-encoded image string (may include data URI prefix)
        
    Returns:
        Tuple of (extracted_text, confidence_score)
        
    Raises:
        OCRError: If OCR processing fails
    """
    # Try Tesseract first if available
    if TESSERACT_AVAILABLE:
        try:
            return extract_text_with_tesseract(image_data)
        except OCRError:
            # If Tesseract fails, try Gemini Vision as fallback
            if GEMINI_AVAILABLE:
                return extract_text_with_gemini_vision(image_data)
            raise
    
    # Fall back to Gemini Vision if Tesseract is not available
    if GEMINI_AVAILABLE:
        return extract_text_with_gemini_vision(image_data)
    
    raise OCRError("No OCR engine available. Install Tesseract or configure Gemini API key.")


def extract_text_with_tesseract(image_data: str) -> Tuple[str, float]:
    """
    Extract text from a base64-encoded image using Tesseract OCR.
    
    Args:
        image_data: Base64-encoded image string
        
    Returns:
        Tuple of (extracted_text, confidence_score)
    """
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
        raise OCRError(f"Failed to process image with Tesseract: {str(e)}")


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
