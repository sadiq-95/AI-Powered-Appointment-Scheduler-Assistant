"""Input schemas for API requests."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class ParseInput(BaseModel):
    """Input for the /parse endpoint."""

    input_type: Literal["text", "image"] = Field(
        ..., description="Type of input: 'text' for raw text, 'image' for base64-encoded image"
    )
    content: str = Field(
        ..., description="The content to parse (text string or base64-encoded image)"
    )


class ExtractInput(BaseModel):
    """Input for the /extract endpoint."""

    raw_text: str = Field(..., description="Raw text extracted from OCR or direct input")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score from previous parsing step"
    )


class EntityData(BaseModel):
    """Extracted entity data."""

    date_phrase: Optional[str] = Field(None, description="Date phrase (e.g., 'next Friday')")
    time_phrase: Optional[str] = Field(None, description="Time phrase (e.g., '3pm')")
    department: Optional[str] = Field(None, description="Department/service type (e.g., 'dentist')")


class NormalizeInput(BaseModel):
    """Input for the /normalize endpoint."""

    entities: EntityData = Field(..., description="Extracted entities from text")
    entities_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score for entity extraction"
    )


class AppointmentInput(BaseModel):
    """Input for the /appointment full pipeline endpoint."""

    input_type: Literal["text", "image"] = Field(
        ..., description="Type of input: 'text' for raw text, 'image' for base64-encoded image"
    )
    content: str = Field(
        ..., description="The content to process (text string or base64-encoded image)"
    )
