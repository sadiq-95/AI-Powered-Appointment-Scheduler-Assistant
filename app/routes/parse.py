"""Parse endpoint for OCR/text extraction."""

from fastapi import APIRouter, HTTPException

from app.exceptions import OCRError
from app.schemas.input import ParseInput
from app.schemas.output import ParseOutput
from app.services.ocr_service import (
    extract_text_from_image,
    extract_text_from_raw,
    is_image_content,
)

router = APIRouter()


@router.post("/parse", response_model=ParseOutput, tags=["Parsing"])
async def parse_input(data: ParseInput) -> ParseOutput:
    """
    Parse text or image input and extract raw text.
    
    - **text**: Directly processes the text content
    - **image**: Uses OCR to extract text from base64-encoded image
    
    Returns the extracted text with a confidence score.
    """
    try:
        if data.input_type == "text":
            # Direct text processing
            raw_text, confidence = extract_text_from_raw(data.content)
        elif data.input_type == "image":
            # OCR processing for images
            raw_text, confidence = extract_text_from_image(data.content)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported input type: {data.input_type}"
            )
        
        return ParseOutput(raw_text=raw_text, confidence=confidence)
        
    except OCRError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
