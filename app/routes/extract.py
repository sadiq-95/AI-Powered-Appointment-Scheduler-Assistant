"""Extract endpoint for LLM-based entity extraction."""

from fastapi import APIRouter, HTTPException

from app.exceptions import ExtractionError, LLMError
from app.schemas.input import ExtractInput
from app.schemas.output import EntityData, ExtractOutput

router = APIRouter()


@router.post("/extract", response_model=ExtractOutput, tags=["Extraction"])
async def extract_entities(data: ExtractInput) -> ExtractOutput:
    """
    Extract appointment entities from raw text using LLM.
    
    Extracts:
    - **date_phrase**: Date mentioned in text (e.g., "next Friday")
    - **time_phrase**: Time mentioned in text (e.g., "3pm")
    - **department**: Service/department type (e.g., "dentist")
    
    Returns extracted entities with a confidence score.
    """
    try:
        from app.services.llm_service import extract_entities as llm_extract
        
        entities, confidence = llm_extract(data.raw_text)
        
        return ExtractOutput(
            entities=EntityData(
                date_phrase=entities.get("date_phrase"),
                time_phrase=entities.get("time_phrase"),
                department=entities.get("department"),
            ),
            entities_confidence=confidence
        )
        
    except LLMError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ExtractionError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
