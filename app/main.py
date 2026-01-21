"""FastAPI application for AI-Powered Appointment Scheduler."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions import AppointmentSchedulerError
from app.routes import appointment, extract, normalize, parse

# Create FastAPI application
app = FastAPI(
    title="AI-Powered Appointment Scheduler",
    description="""
A backend service that converts unstructured text or image inputs into 
validated, normalized appointment data using OCR, entity extraction (LLM), 
and deterministic date normalization.

## Features

- **Text/Image Parsing**: Accept raw text or images via OCR
- **Entity Extraction**: Extract date, time, and department using Gemini LLM
- **Normalization**: Convert natural language to ISO format dates/times
- **Guardrails**: Explicit failure on ambiguous inputs

## Endpoints

- `/parse` - OCR/text extraction
- `/extract` - Entity extraction
- `/normalize` - Date/time normalization
- `/appointment` - Full pipeline orchestration
- `/health` - Service health check
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# Register exception handler for custom exceptions
@app.exception_handler(AppointmentSchedulerError)
async def appointment_scheduler_error_handler(
    request: Request, 
    exc: AppointmentSchedulerError
) -> JSONResponse:
    """Handle custom application exceptions."""
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.message,
            "error_type": exc.error_type
        }
    )


# Register routers
app.include_router(parse.router)
app.include_router(extract.router)
app.include_router(normalize.router)
app.include_router(appointment.router)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with service information."""
    return {
        "service": "AI-Powered Appointment Scheduler",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }
