"""Appointment endpoint for full pipeline orchestration."""

from fastapi import APIRouter, HTTPException

from app.exceptions import (
    AmbiguityError,
    ExtractionError,
    LLMError,
    NormalizationError,
    OCRError,
)
from app.schemas.input import AppointmentInput
from app.schemas.output import AppointmentData, AppointmentOutput, HealthOutput
from app.services.normalization_service import normalize_datetime, normalize_department
from app.services.ocr_service import extract_text_from_image, extract_text_from_raw
from app.utils.confidence import MIN_EXTRACTION_CONFIDENCE, MIN_OCR_CONFIDENCE

router = APIRouter()


@router.post("/appointment", response_model=AppointmentOutput, tags=["Appointment"])
async def create_appointment(data: AppointmentInput) -> AppointmentOutput:
    """
    Full pipeline: Parse → Extract → Normalize → Appointment
    
    Takes text or image input and returns a structured appointment.
    
    Pipeline stages:
    1. **Parse**: Extract text from input (OCR for images)
    2. **Extract**: Use LLM to extract entities (date, time, department)
    3. **Normalize**: Convert to ISO date/time format
    4. **Validate**: Apply guardrails and return result
    
    Returns structured appointment data or needs_clarification status.
    """
    try:
        # Stage 1: Parse/OCR
        if data.input_type == "text":
            raw_text, ocr_confidence = extract_text_from_raw(data.content)
        else:
            raw_text, ocr_confidence = extract_text_from_image(data.content)
        
        # Check OCR confidence threshold
        if ocr_confidence < MIN_OCR_CONFIDENCE:
            return AppointmentOutput(
                appointment=None,
                status="needs_clarification",
                message=f"Text extraction confidence too low ({ocr_confidence:.2f}). Please provide clearer input."
            )
        
        # Stage 2: Entity Extraction
        from app.services.llm_service import extract_entities
        
        entities, extraction_confidence = extract_entities(raw_text)
        
        # Check extraction confidence threshold
        if extraction_confidence < MIN_EXTRACTION_CONFIDENCE:
            return AppointmentOutput(
                appointment=None,
                status="needs_clarification",
                message="Could not extract sufficient information. Please include date, time, and appointment type."
            )
        
        # Validate required entities
        date_phrase = entities.get("date_phrase")
        time_phrase = entities.get("time_phrase")
        department = entities.get("department")
        
        missing_fields = []
        if not date_phrase:
            missing_fields.append("date")
        if not time_phrase:
            missing_fields.append("time")
        if not department:
            missing_fields.append("department/appointment type")
        
        if missing_fields:
            return AppointmentOutput(
                appointment=None,
                status="needs_clarification",
                message=f"Missing required information: {', '.join(missing_fields)}"
            )
        
        # Stage 3: Normalization
        normalized, norm_confidence = normalize_datetime(date_phrase, time_phrase)
        
        if normalized is None or normalized.get("date") is None or normalized.get("time") is None:
            return AppointmentOutput(
                appointment=None,
                status="needs_clarification",
                message="Could not parse date or time. Please provide a specific date and time."
            )
        
        # Normalize department name
        normalized_department = normalize_department(department)
        
        # Stage 4: Create appointment
        return AppointmentOutput(
            appointment=AppointmentData(
                department=normalized_department,
                date=normalized["date"],
                time=normalized["time"],
                tz=normalized["tz"]
            ),
            status="ok",
            message=None
        )
        
    except OCRError as e:
        return AppointmentOutput(
            appointment=None,
            status="needs_clarification",
            message=f"Could not process input: {str(e)}"
        )
    except LLMError as e:
        raise HTTPException(status_code=503, detail=f"LLM service error: {str(e)}")
    except ExtractionError as e:
        return AppointmentOutput(
            appointment=None,
            status="needs_clarification",
            message=f"Could not extract information: {str(e)}"
        )
    except AmbiguityError as e:
        return AppointmentOutput(
            appointment=None,
            status="needs_clarification",
            message=str(e)
        )
    except NormalizationError as e:
        return AppointmentOutput(
            appointment=None,
            status="needs_clarification",
            message=str(e)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/health", response_model=HealthOutput, tags=["Health"])
async def health_check() -> HealthOutput:
    """
    Check the health status of the service.
    
    Returns the service status and version.
    """
    return HealthOutput(status="healthy", version="1.0.0")
