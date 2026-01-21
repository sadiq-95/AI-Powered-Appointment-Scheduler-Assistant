"""LLM service for entity extraction using Gemini API."""

import json
import re
from typing import Dict, Optional, Tuple

from app.config import get_settings
from app.exceptions import ExtractionError, LLMError
from app.utils.confidence import calculate_extraction_confidence

# Try to import Google Generative AI, handle gracefully if not installed
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


# System prompt for entity extraction
EXTRACTION_PROMPT = """You are an entity extraction assistant. Extract appointment-related entities from the given text.

IMPORTANT RULES:
1. Only extract entities that are EXPLICITLY mentioned in the text
2. Do NOT infer or guess any information
3. Return ONLY a valid JSON object, no other text
4. If an entity is not found, set its value to null
5. Do not add any explanation or commentary

Extract the following entities:
- date_phrase: The date or day mentioned (e.g., "next Friday", "25th January", "tomorrow")
- time_phrase: The time mentioned (e.g., "3pm", "15:00", "morning", "afternoon")
- department: The service, department, or type of appointment (e.g., "dentist", "doctor", "cardiology")

Return format:
{
    "date_phrase": "<extracted date phrase or null>",
    "time_phrase": "<extracted time phrase or null>",
    "department": "<extracted department or null>"
}

Text to analyze:
"""


def extract_entities(raw_text: str) -> Tuple[Dict, float]:
    """
    Extract appointment entities from raw text using Gemini API.
    
    Args:
        raw_text: Raw text to extract entities from
        
    Returns:
        Tuple of (entities_dict, confidence_score)
        
    Raises:
        ExtractionError: If entity extraction fails
        LLMError: If LLM API call fails
    """
    if not GENAI_AVAILABLE:
        raise LLMError("Google Generative AI library is not installed")
    
    settings = get_settings()
    
    if not settings.gemini_api_key:
        raise LLMError("GEMINI_API_KEY is not configured")
    
    try:
        # Configure the API
        genai.configure(api_key=settings.gemini_api_key)
        
        # Create model with JSON-focused configuration
        model = genai.GenerativeModel(
            model_name=settings.gemini_model_name,
            generation_config={
                "temperature": 0.1,  # Low temperature for deterministic output
                "top_p": 0.95,
                "max_output_tokens": 500,
            }
        )
        
        # Generate response
        full_prompt = EXTRACTION_PROMPT + raw_text
        response = model.generate_content(full_prompt)
        
        if not response or not response.text:
            raise LLMError("Empty response from LLM")
        
        # Parse the JSON response
        entities = parse_llm_response(response.text)
        
        # Calculate confidence
        has_date = entities.get("date_phrase") is not None
        has_time = entities.get("time_phrase") is not None
        has_department = entities.get("department") is not None
        
        confidence = calculate_extraction_confidence(
            entities,
            has_date=has_date,
            has_time=has_time,
            has_department=has_department
        )
        
        return entities, confidence
        
    except LLMError:
        raise
    except json.JSONDecodeError as e:
        raise ExtractionError(f"Failed to parse LLM response as JSON: {str(e)}")
    except Exception as e:
        error_msg = str(e)
        if "API_KEY" in error_msg.upper() or "AUTH" in error_msg.upper():
            raise LLMError(f"Authentication error with Gemini API: {error_msg}")
        raise LLMError(f"LLM API error: {error_msg}")


def parse_llm_response(response_text: str) -> Dict:
    """
    Parse the LLM response to extract JSON.
    
    Handles cases where LLM might include markdown code blocks or extra text.
    
    Args:
        response_text: Raw response from LLM
        
    Returns:
        Parsed JSON as dictionary
        
    Raises:
        ExtractionError: If JSON parsing fails
    """
    # Clean the response
    text = response_text.strip()
    
    # Try to extract JSON from markdown code blocks
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if json_match:
        text = json_match.group(1)
    
    # Try to find JSON object directly
    json_match = re.search(r"\{[^{}]*\}", text, re.DOTALL)
    if json_match:
        text = json_match.group(0)
    
    try:
        entities = json.loads(text)
    except json.JSONDecodeError:
        raise ExtractionError(f"Could not parse LLM response as JSON: {response_text[:200]}")
    
    # Validate and normalize the response
    normalized = {
        "date_phrase": normalize_entity(entities.get("date_phrase")),
        "time_phrase": normalize_entity(entities.get("time_phrase")),
        "department": normalize_entity(entities.get("department")),
    }
    
    return normalized


def normalize_entity(value: Optional[str]) -> Optional[str]:
    """
    Normalize an entity value.
    
    - Converts empty strings to None
    - Strips whitespace
    - Handles "null" string
    """
    if value is None:
        return None
    
    if isinstance(value, str):
        value = value.strip()
        if not value or value.lower() in ("null", "none", "n/a", ""):
            return None
        return value
    
    return None
