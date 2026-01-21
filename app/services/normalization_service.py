"""Normalization service for date/time parsing."""

from datetime import datetime
from typing import Dict, Optional, Tuple

import dateparser
import pytz

from app.config import get_settings
from app.exceptions import AmbiguityError, NormalizationError
from app.utils.confidence import calculate_normalization_confidence


# Department name normalization mapping
DEPARTMENT_MAPPING = {
    # Dental
    "dentist": "Dentistry",
    "dental": "Dentistry",
    "teeth": "Dentistry",
    "tooth": "Dentistry",
    "orthodontist": "Dentistry",
    
    # General Medicine
    "doctor": "General Medicine",
    "physician": "General Medicine",
    "gp": "General Medicine",
    "general": "General Medicine",
    "checkup": "General Medicine",
    "check-up": "General Medicine",
    "consultation": "General Medicine",
    
    # Cardiology
    "cardiologist": "Cardiology",
    "cardiology": "Cardiology",
    "heart": "Cardiology",
    
    # Dermatology
    "dermatologist": "Dermatology",
    "dermatology": "Dermatology",
    "skin": "Dermatology",
    
    # Ophthalmology
    "ophthalmologist": "Ophthalmology",
    "ophthalmology": "Ophthalmology",
    "eye": "Ophthalmology",
    "eyes": "Ophthalmology",
    "optometrist": "Ophthalmology",
    
    # Orthopedics
    "orthopedic": "Orthopedics",
    "orthopedics": "Orthopedics",
    "bone": "Orthopedics",
    "bones": "Orthopedics",
    "joints": "Orthopedics",
    
    # Pediatrics
    "pediatrician": "Pediatrics",
    "pediatrics": "Pediatrics",
    "child": "Pediatrics",
    "children": "Pediatrics",
    
    # ENT
    "ent": "ENT",
    "ear": "ENT",
    "nose": "ENT",
    "throat": "ENT",
    
    # Neurology
    "neurologist": "Neurology",
    "neurology": "Neurology",
    "brain": "Neurology",
    "nerve": "Neurology",
    
    # Psychiatry
    "psychiatrist": "Psychiatry",
    "psychiatry": "Psychiatry",
    "mental": "Psychiatry",
    "psychological": "Psychiatry",
    
    # Gynecology
    "gynecologist": "Gynecology",
    "gynecology": "Gynecology",
    "obgyn": "Gynecology",
    "ob-gyn": "Gynecology",
}


def normalize_datetime(
    date_phrase: Optional[str],
    time_phrase: Optional[str]
) -> Tuple[Optional[Dict], float]:
    """
    Normalize date and time phrases to ISO format.
    
    Args:
        date_phrase: Natural language date (e.g., "next Friday")
        time_phrase: Natural language time (e.g., "3pm")
        
    Returns:
        Tuple of (normalized_dict, confidence_score)
        normalized_dict contains: date, time, tz
        
    Raises:
        NormalizationError: If normalization fails
        AmbiguityError: If date/time is ambiguous
    """
    settings = get_settings()
    tz = pytz.timezone(settings.tz)
    now = datetime.now(tz)
    
    parsed_date = None
    parsed_time = None
    is_relative = False
    
    # Parse date
    if date_phrase:
        parsed_date, is_relative = parse_date(date_phrase, now, tz)
    
    # Parse time
    if time_phrase:
        parsed_time = parse_time(time_phrase, now, tz)
    
    # If we have neither, it's an error
    if parsed_date is None and parsed_time is None:
        return None, 0.0
    
    # Use today if no date provided but time is
    if parsed_date is None and parsed_time is not None:
        parsed_date = now.date()
        is_relative = True
    
    # Use a default time if date provided but no time
    if parsed_time is None and parsed_date is not None:
        # No default time - require explicit time
        return None, 0.0
    
    # Calculate confidence
    confidence = calculate_normalization_confidence(
        date_parsed=parsed_date is not None,
        time_parsed=parsed_time is not None,
        is_relative=is_relative
    )
    
    normalized = {
        "date": parsed_date.strftime("%Y-%m-%d") if parsed_date else None,
        "time": parsed_time.strftime("%H:%M") if parsed_time else None,
        "tz": settings.tz
    }
    
    if normalized["date"] is None or normalized["time"] is None:
        return None, confidence
    
    return normalized, confidence


def parse_date(
    date_phrase: str, 
    reference_date: datetime,
    tz: pytz.timezone
) -> Tuple[Optional[datetime], bool]:
    """
    Parse a natural language date phrase.
    
    Returns:
        Tuple of (parsed_date, is_relative)
    """
    is_relative = False
    
    # Check for relative date indicators
    relative_indicators = [
        "today", "tomorrow", "yesterday",
        "next", "this", "coming",
        "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"
    ]
    
    date_lower = date_phrase.lower()
    for indicator in relative_indicators:
        if indicator in date_lower:
            is_relative = True
            break
    
    # Configure dateparser settings
    parser_settings = {
        "TIMEZONE": str(tz),
        "RETURN_AS_TIMEZONE_AWARE": True,
        "PREFER_DATES_FROM": "future",
        "RELATIVE_BASE": reference_date,
        "STRICT_PARSING": True,
    }
    
    try:
        # First try strict parsing
        parsed = dateparser.parse(
            date_phrase,
            settings=parser_settings,
            languages=["en"]
        )
        
        if parsed is None:
            # Try less strict parsing
            parser_settings["STRICT_PARSING"] = False
            parsed = dateparser.parse(
                date_phrase,
                settings=parser_settings,
                languages=["en"]
            )
        
        if parsed:
            return parsed.date(), is_relative
        
        return None, is_relative
        
    except Exception:
        return None, is_relative


def parse_time(
    time_phrase: str,
    reference_date: datetime,
    tz: pytz.timezone
) -> Optional[datetime]:
    """
    Parse a natural language time phrase.
    
    Returns:
        Parsed time as datetime object (only time component is used)
    """
    # Handle common time phrases
    time_lower = time_phrase.lower().strip()
    
    # Handle explicit time phrases
    time_mappings = {
        "morning": "09:00",
        "noon": "12:00",
        "afternoon": "14:00",
        "evening": "18:00",
        "night": "20:00",
    }
    
    if time_lower in time_mappings:
        time_str = time_mappings[time_lower]
        return datetime.strptime(time_str, "%H:%M")
    
    # Configure dateparser settings
    parser_settings = {
        "TIMEZONE": str(tz),
        "RETURN_AS_TIMEZONE_AWARE": True,
        "RELATIVE_BASE": reference_date,
    }
    
    try:
        parsed = dateparser.parse(
            time_phrase,
            settings=parser_settings,
            languages=["en"]
        )
        
        if parsed:
            return parsed
        
        return None
        
    except Exception:
        return None


def normalize_department(department: Optional[str]) -> Optional[str]:
    """
    Normalize department name to standard format.
    
    Args:
        department: Raw department name
        
    Returns:
        Normalized department name
    """
    if not department:
        return None
    
    dept_lower = department.lower().strip()
    
    # Check for exact match in mapping
    if dept_lower in DEPARTMENT_MAPPING:
        return DEPARTMENT_MAPPING[dept_lower]
    
    # Check for partial match
    for key, value in DEPARTMENT_MAPPING.items():
        if key in dept_lower or dept_lower in key:
            return value
    
    # Return title-cased original if no mapping found
    return department.title()


def validate_appointment_date(date_str: str, tz_str: str) -> bool:
    """
    Validate that the appointment date is not in the past.
    
    Args:
        date_str: ISO format date string
        tz_str: Timezone string
        
    Returns:
        True if date is valid (today or future)
    """
    try:
        tz = pytz.timezone(tz_str)
        now = datetime.now(tz)
        appointment_date = datetime.strptime(date_str, "%Y-%m-%d")
        
        return appointment_date.date() >= now.date()
    except Exception:
        return False
