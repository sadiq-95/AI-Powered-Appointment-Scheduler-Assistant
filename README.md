# AI-Powered Appointment Scheduler Backend

A backend service that converts unstructured text or image inputs into validated, normalized appointment data using OCR, entity extraction (Gemini LLM), and deterministic date normalization.

## 🏗️ Architecture Flow

```
Input (Text/Image)
        ↓
OCR / Text Extraction (/parse)
        ↓
Entity Extraction - LLM (/extract)
        ↓
Normalization - Date/Time (/normalize)
        ↓
Guardrails & Validation
        ↓
Final Structured Appointment JSON (/appointment)
```

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.10+, FastAPI, Pydantic |
| OCR | Tesseract via pytesseract |
| LLM | Google Gemini API |
| Date Parsing | dateparser, pytz |
| Timezone | Asia/Kolkata |

## 📦 Setup Instructions

### Prerequisites

1. **Python 3.10+** installed
2. **Tesseract OCR** installed:
   ```bash
   # macOS
   brew install tesseract
   
   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr
   
   # Windows
   # Download from https://github.com/UB-Mannheim/tesseract/wiki
   ```
3. **Gemini API Key** from [Google AI Studio](https://makersuite.google.com/app/apikey)

### Installation

```bash
# Clone the repository
cd plum_hq_assignment

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file and add your API key
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### Environment Variables

Create a `.env` file with:

```env
GEMINI_API_KEY=your_gemini_api_key_here
TZ=Asia/Kolkata
```

### Running the Server

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

## 📖 API Usage Examples

### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{"status": "healthy", "version": "1.0.0"}
```

### Parse Text Input

```bash
curl -X POST http://localhost:8000/parse \
  -H "Content-Type: application/json" \
  -d '{"input_type": "text", "content": "Book dentist next Friday at 3pm"}'
```

Response:
```json
{
  "raw_text": "Book dentist next Friday at 3pm",
  "confidence": 0.92
}
```

### Extract Entities

```bash
curl -X POST http://localhost:8000/extract \
  -H "Content-Type: application/json" \
  -d '{"raw_text": "Book dentist next Friday at 3pm", "confidence": 0.92}'
```

Response:
```json
{
  "entities": {
    "date_phrase": "next Friday",
    "time_phrase": "3pm",
    "department": "dentist"
  },
  "entities_confidence": 0.95
}
```

### Normalize Date/Time

```bash
curl -X POST http://localhost:8000/normalize \
  -H "Content-Type: application/json" \
  -d '{
    "entities": {
      "date_phrase": "next Friday",
      "time_phrase": "3pm",
      "department": "dentist"
    },
    "entities_confidence": 0.95
  }'
```

Response:
```json
{
  "normalized": {
    "date": "2026-01-24",
    "time": "15:00",
    "tz": "Asia/Kolkata"
  },
  "normalization_confidence": 0.86,
  "status": "ok",
  "message": null
}
```

### Full Pipeline (Recommended)

```bash
curl -X POST http://localhost:8000/appointment \
  -H "Content-Type: application/json" \
  -d '{"input_type": "text", "content": "Book dentist next Friday at 3pm"}'
```

Response:
```json
{
  "appointment": {
    "department": "Dentistry",
    "date": "2026-01-24",
    "time": "15:00",
    "tz": "Asia/Kolkata"
  },
  "status": "ok",
  "message": null
}
```

### Image Input (Base64)

```bash
# First, encode your image to base64
base64 -i appointment_note.jpg | tr -d '\n' > image_base64.txt

# Then make the request
curl -X POST http://localhost:8000/appointment \
  -H "Content-Type: application/json" \
  -d "{\"input_type\": \"image\", \"content\": \"$(cat image_base64.txt)\"}"
```

## 🚧 Guardrail Behavior

The service explicitly fails with `needs_clarification` status in these cases:

| Scenario | Response |
|----------|----------|
| Ambiguous date/time | `{"status": "needs_clarification", "message": "Could not parse date or time..."}` |
| Missing department | `{"status": "needs_clarification", "message": "Missing required information: department..."}` |
| Low OCR confidence | `{"status": "needs_clarification", "message": "Text extraction confidence too low..."}` |
| Missing date or time | `{"status": "needs_clarification", "message": "Missing required information: date, time"}` |

Example ambiguous input:

```bash
curl -X POST http://localhost:8000/appointment \
  -H "Content-Type: application/json" \
  -d '{"input_type": "text", "content": "maybe sometime next week?"}'
```

Response:
```json
{
  "appointment": null,
  "status": "needs_clarification",
  "message": "Missing required information: time, department/appointment type"
}
```

## 🚀 Deployment Instructions

### Deploy to Railway

1. Create a [Railway](https://railway.app/) account
2. Connect your GitHub repository
3. Add environment variables:
   - `GEMINI_API_KEY`
   - `TZ=Asia/Kolkata`
4. Railway will auto-detect the Python project and deploy

### Deploy to Render

1. Create a [Render](https://render.com/) account
2. Create a new Web Service
3. Connect your repository
4. Set the build command: `pip install -r requirements.txt`
5. Set the start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Add environment variables

### Procfile (for Heroku/Railway)

```
web: uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

## ⚠️ Known Limitations

1. **OCR Accuracy**: Tesseract may struggle with handwritten notes or low-quality images
2. **Language Support**: Currently optimized for English inputs only
3. **Relative Dates**: Relative dates (e.g., "next Friday") are resolved based on server time
4. **No Persistence**: Appointments are not stored; this service only parses and structures requests
5. **Rate Limits**: Subject to Gemini API rate limits
6. **Timezone**: Hardcoded to Asia/Kolkata as per requirements

## 📚 API Documentation

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🧪 Running Tests

```bash
pip install pytest pytest-asyncio httpx
pytest tests/ -v
```

## 📁 Project Structure

```
app/
├── main.py              # FastAPI application
├── config.py            # Configuration settings
├── exceptions.py        # Custom exceptions
├── routes/
│   ├── parse.py         # /parse endpoint
│   ├── extract.py       # /extract endpoint
│   ├── normalize.py     # /normalize endpoint
│   └── appointment.py   # /appointment & /health endpoints
├── services/
│   ├── ocr_service.py   # Tesseract OCR
│   ├── llm_service.py   # Gemini API
│   └── normalization_service.py  # Date/time parsing
├── schemas/
│   ├── input.py         # Request models
│   └── output.py        # Response models
└── utils/
    └── confidence.py    # Confidence scoring

```
### LIVE DEPLOYMENT
## STREAMLIT LINK
https://sadiq-95-ai-powered-appointment-scheduler--streamlit-app-odff4b.streamlit.app/
## Backend (FastAPI on Render):  
https://ai-powered-appointment-scheduler-hkbi.onrender.com/docs#/

The Streamlit frontend sends requests to the backend APIs, which handle OCR/text parsing, entity extraction, normalization, and guardrail validation.
