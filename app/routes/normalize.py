"""Normalize endpoint for date/time normalization."""

from fastapi import APIRouter, HTTPException

from app.exceptions import AmbiguityError, NormalizationError
from app.schemas.input import NormalizeInput
from app.schemas.output import NormalizedData, NormalizeOutput
from app.services.normalization_service import normalize_datetime

router = APIRouter()


@router.post("/normalize", response_model=NormalizeOutput, tags=["Normalization"])
async def normalize_entities(data: NormalizeInput) -> NormalizeOutput:
    """
    Normalize extracted entities into ISO date/time format.
    
    - Converts natural language dates to ISO format (YYYY-MM-DD)
    - Converts natural language times to 24-hour format (HH:MM)
    - Uses Asia/Kolkata timezone
    
    Returns normalized data with a confidence score.
    If normalization fails or is ambiguous, returns needs_clarification status.
    """
    try:
        normalized, confidence = normalize_datetime(
            date_phrase=data.entities.date_phrase,
            time_phrase=data.entities.time_phrase
        )
        
        if normalized is None or normalized.get("date") is None or normalized.get("time") is None:
            return NormalizeOutput(
                normalized=None,
                normalization_confidence=confidence,
                status="needs_clarification",
                message="Could not parse date or time. Please provide a specific date and time."
            )
        
        return NormalizeOutput(
            normalized=NormalizedData(
                date=normalized["date"],
                time=normalized["time"],
                tz=normalized["tz"]
            ),
            normalization_confidence=confidence,
            status="ok",
            message=None
        )
        
    except AmbiguityError as e:
        return NormalizeOutput(
            normalized=None,
            normalization_confidence=0.0,
            status="needs_clarification",
            message=str(e)
        )
    except NormalizationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
