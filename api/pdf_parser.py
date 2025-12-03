"""
BRD Parser Service - FastAPI Application
Extracts structured data from PDF BRD documents using AI

Ported from: brd_agent_em/brd_parser/main.py
"""

import os
import io
import json
from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pypdf import PdfReader
from anthropic import Anthropic
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="BRD Parser Service",
    description="Extracts structured data from Business Requirements Documents",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Anthropic client
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise ValueError("ANTHROPIC_API_KEY environment variable is required")

anthropic_client = Anthropic(api_key=ANTHROPIC_API_KEY)


class ParsedBRD(BaseModel):
    """Structured BRD output format"""
    project: dict
    features: list
    stakeholders: list
    technical_requirements: dict
    success_criteria: list


def extract_text_from_pdf(pdf_file: bytes) -> str:
    """Extract text content from PDF file"""
    try:
        pdf_reader = PdfReader(io.BytesIO(pdf_file))
        text_content = []
        
        for page in pdf_reader.pages:
            text = page.extract_text()
            if text:
                text_content.append(text)
        
        full_text = "\n\n".join(text_content)
        
        if not full_text.strip():
            raise ValueError("No text content found in PDF")
        
        return full_text
    
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to extract text from PDF: {str(e)}"
        )


def parse_brd_with_ai(text: str) -> dict:
    """Use Claude to extract structured information from BRD text"""
    
    prompt = f"""You are an expert Business Analyst. Extract structured information from this Business Requirements Document (BRD).

BRD Content:
{text}

Extract and return a JSON object with this EXACT structure:

{{
  "project": {{
    "name": "Extract the project/product name",
    "description": "Brief description of the project",
    "objectives": ["List of main project objectives"],
    "constraints": ["List of constraints, limitations, or dependencies"]
  }},
  "features": [
    {{
      "id": "F001",
      "name": "Feature name",
      "description": "Detailed feature description",
      "priority": "High|Medium|Low",
      "requirements": ["List of specific requirements for this feature"]
    }}
  ],
  "stakeholders": [
    "List of stakeholders, teams, or users"
  ],
  "technical_requirements": {{
    "platforms": ["List of target platforms"],
    "integrations": ["Required integrations"],
    "performance": "Performance requirements",
    "security": "Security requirements",
    "scalability": "Scalability requirements"
  }},
  "success_criteria": [
    "List of success criteria and KPIs"
  ]
}}

IMPORTANT RULES:
1. Return ONLY valid JSON, no markdown, no explanation
2. Extract ALL features mentioned in the document
3. Be comprehensive - include all important details
4. If information is not available, use reasonable defaults or empty arrays
5. Assign sequential IDs to features (F001, F002, etc.)
6. Classify feature priorities based on context
7. Include ALL requirements, not just technical ones

Start your response with {{ and end with }}"""

    try:
        # Call Claude API
        response = anthropic_client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=4000,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        # Extract JSON from response
        content = response.content[0].text
        
        # Parse JSON
        parsed_data = json.loads(content)
        
        return parsed_data
    
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse AI response as JSON: {str(e)}\nResponse: {content[:500]}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI parsing failed: {str(e)}"
        )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "BRD Parser",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "parse_pdf": "POST /parse/pdf",
            "parse_text": "POST /parse/text",
            "health": "GET /health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "anthropic_configured": bool(ANTHROPIC_API_KEY)
    }


@app.post("/parse/pdf")
async def parse_pdf(file: UploadFile = File(...)):
    """
    Parse PDF BRD and extract structured information
    
    Returns JSON structure compatible with Engineering Plan Generator
    """
    
    # Validate file type
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )
    
    try:
        # Read file content
        pdf_content = await file.read()
        
        # Extract text from PDF
        text_content = extract_text_from_pdf(pdf_content)
        
        # Parse with AI
        structured_data = parse_brd_with_ai(text_content)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "BRD parsed successfully",
                "data": structured_data,
                "metadata": {
                    "filename": file.filename,
                    "text_length": len(text_content),
                    "features_count": len(structured_data.get("features", []))
                }
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@app.post("/parse/text")
async def parse_text(text: str):
    """
    Parse text BRD and extract structured information
    
    Useful for testing or when text is already extracted
    """
    
    if not text or not text.strip():
        raise HTTPException(
            status_code=400,
            detail="Text content is required"
        )
    
    try:
        # Parse with AI
        structured_data = parse_brd_with_ai(text)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "BRD parsed successfully",
                "data": structured_data,
                "metadata": {
                    "text_length": len(text),
                    "features_count": len(structured_data.get("features", []))
                }
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

