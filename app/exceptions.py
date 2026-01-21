"""Custom exceptions for the appointment scheduler service."""

from typing import Optional


class AppointmentSchedulerError(Exception):
    """Base exception for appointment scheduler errors."""

    def __init__(self, message: str, error_type: str = "unknown_error"):
        self.message = message
        self.error_type = error_type
        super().__init__(self.message)


class OCRError(AppointmentSchedulerError):
    """Exception raised when OCR processing fails."""

    def __init__(self, message: str = "Failed to extract text from image"):
        super().__init__(message, error_type="ocr_error")


class ExtractionError(AppointmentSchedulerError):
    """Exception raised when entity extraction fails."""

    def __init__(self, message: str = "Failed to extract entities from text"):
        super().__init__(message, error_type="extraction_error")


class NormalizationError(AppointmentSchedulerError):
    """Exception raised when date/time normalization fails."""

    def __init__(self, message: str = "Failed to normalize date/time"):
        super().__init__(message, error_type="normalization_error")


class AmbiguityError(AppointmentSchedulerError):
    """Exception raised when input is ambiguous and requires clarification."""

    def __init__(
        self, 
        message: str = "Input is ambiguous and requires clarification",
        ambiguous_field: Optional[str] = None
    ):
        self.ambiguous_field = ambiguous_field
        super().__init__(message, error_type="ambiguity_error")


class LLMError(AppointmentSchedulerError):
    """Exception raised when LLM API call fails."""

    def __init__(self, message: str = "Failed to communicate with LLM service"):
        super().__init__(message, error_type="llm_error")


class ValidationError(AppointmentSchedulerError):
    """Exception raised when input validation fails."""

    def __init__(self, message: str = "Input validation failed"):
        super().__init__(message, error_type="validation_error")
