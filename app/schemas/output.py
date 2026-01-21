"""Output schemas for API responses."""

from typing import Literal, Optional

from pydantic import BaseModel, Field


class ParseOutput(BaseModel):
    """Output from the /parse endpoint."""

    raw_text: str = Field(..., description="Extracted raw text")
    confidence: float = Field(..., ge=0.0, le=1.0, description="OCR/extraction confidence score")


class EntityData(BaseModel):
    """Extracted entity data."""

    date_phrase: Optional[str] = Field(None, description="Date phrase (e.g., 'next Friday')")
    time_phrase: Optional[str] = Field(None, description="Time phrase (e.g., '3pm')")
    department: Optional[str] = Field(None, description="Department/service type (e.g., 'dentist')")


class ExtractOutput(BaseModel):
    """Output from the /extract endpoint."""

    entities: EntityData = Field(..., description="Extracted entities")
    entities_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Entity extraction confidence score"
    )


class NormalizedData(BaseModel):
    """Normalized date/time data."""

    date: str = Field(..., description="ISO format date (YYYY-MM-DD)")
    time: str = Field(..., description="24-hour format time (HH:MM)")
    tz: str = Field(..., description="Timezone identifier")


class NormalizeOutput(BaseModel):
    """Output from the /normalize endpoint."""

    normalized: Optional[NormalizedData] = Field(
        None, description="Normalized date/time data, null if normalization failed"
    )
    normalization_confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Normalization confidence score"
    )
    status: Literal["ok", "needs_clarification"] = Field(
        ..., description="Processing status"
    )
    message: Optional[str] = Field(None, description="Clarification message if needed")


class AppointmentData(BaseModel):
    """Final appointment data."""

    department: str = Field(..., description="Normalized department name")
    date: str = Field(..., description="ISO format date (YYYY-MM-DD)")
    time: str = Field(..., description="24-hour format time (HH:MM)")
    tz: str = Field(..., description="Timezone identifier")


class AppointmentOutput(BaseModel):
    """Output from the /appointment endpoint."""

    appointment: Optional[AppointmentData] = Field(
        None, description="Structured appointment data, null if processing failed"
    )
    status: Literal["ok", "needs_clarification"] = Field(
        ..., description="Processing status"
    )
    message: Optional[str] = Field(None, description="Clarification or error message")


class HealthOutput(BaseModel):
    """Output from the /health endpoint."""

    status: Literal["healthy", "unhealthy"] = Field(..., description="Service health status")
    version: str = Field(default="1.0.0", description="Service version")


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str = Field(..., description="Error description")
    error_type: str = Field(..., description="Error type identifier")
