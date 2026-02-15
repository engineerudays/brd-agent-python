"""
BRD Agent - FastAPI Orchestrator
Main API endpoint for processing BRDs through the agent pipeline

This is the Python equivalent of the n8n Master Orchestrator.
"""

import logging
import base64
import io
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pypdf import PdfReader

# Import ingestion router
from api.ingest import router as ingest_router

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="BRD Agent - Orchestrator API",
    description="Multi-Agent Engineering Manager - Process BRDs into Engineering Artifacts",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include ingestion router
app.include_router(ingest_router)


# === Request/Response Models ===

class BRDRequest(BaseModel):
    """Request model for BRD processing"""
    # PDF input (base64 encoded)
    pdf_file: Optional[str] = None
    filename: Optional[str] = None
    
    # JSON input - direct BRD data
    project: Optional[dict] = None
    features: Optional[list] = None
    
    # Alternative: raw BRD text
    raw_brd_text: Optional[str] = None
    
    # Alternative: wrapped data
    brd_data: Optional[dict] = None
    
    class Config:
        extra = "allow"  # Allow additional fields


class ProcessingResponse(BaseModel):
    """Response model for BRD processing"""
    status: str
    message: str
    stages_completed: list[str]
    timestamp: str
    engineering_plan: Optional[dict] = None
    project_schedule: Optional[dict] = None
    note: Optional[str] = None
    errors: Optional[list[str]] = None


# === Lazy workflow initialization ===
# We initialize the workflow lazily to avoid loading LLM on module import

_workflow = None

def get_workflow():
    """Get or create the BRD workflow instance."""
    global _workflow
    if _workflow is None:
        logger.info("Initializing BRD workflow...")
        from src.brd_agent.graph import create_workflow
        _workflow = create_workflow()
        logger.info("BRD workflow initialized")
    return _workflow


# === Helper Functions ===

def extract_text_from_pdf_base64(pdf_base64: str) -> str:
    """Extract text from base64-encoded PDF."""
    try:
        pdf_bytes = base64.b64decode(pdf_base64)
        pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
        
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


def normalize_input(request_data: dict) -> dict:
    """
    Normalize various input formats into a consistent structure.
    
    Handles:
    - PDF file (base64)
    - Direct project/features JSON
    - raw_brd_text wrapper
    - brd_data wrapper
    """
    # Case 1: PDF file
    if request_data.get("pdf_file"):
        logger.info("Processing PDF input")
        # Extract text from PDF
        pdf_text = extract_text_from_pdf_base64(request_data["pdf_file"])
        
        # For now, return the text as a simple structure
        # The Parser agent will handle AI-based structuring if needed
        return {
            "project": {
                "name": request_data.get("filename", "PDF Document").replace(".pdf", ""),
                "description": pdf_text[:500] + "..." if len(pdf_text) > 500 else pdf_text,
                "objectives": [],
                "constraints": []
            },
            "features": [],
            "stakeholders": [],
            "technical_requirements": {},
            "success_criteria": [],
            "_raw_text": pdf_text,
            "_source": "pdf"
        }
    
    # Case 2: Direct project/features
    if request_data.get("project") or request_data.get("features"):
        logger.info("Processing direct JSON input")
        return {
            "project": request_data.get("project", {}),
            "features": request_data.get("features", []),
            "stakeholders": request_data.get("stakeholders", []),
            "technical_requirements": request_data.get("technical_requirements", {}),
            "success_criteria": request_data.get("success_criteria", []),
            "_source": "json"
        }
    
    # Case 3: raw_brd_text wrapper
    if request_data.get("raw_brd_text"):
        logger.info("Processing raw_brd_text input")
        import json
        try:
            inner_data = json.loads(request_data["raw_brd_text"])
            return normalize_input(inner_data)
        except json.JSONDecodeError:
            # Treat as plain text
            return {
                "project": {
                    "name": "Unknown Project",
                    "description": request_data["raw_brd_text"],
                    "objectives": [],
                    "constraints": []
                },
                "features": [],
                "_source": "text"
            }
    
    # Case 4: brd_data wrapper
    if request_data.get("brd_data"):
        logger.info("Processing brd_data wrapper input")
        return normalize_input(request_data["brd_data"])
    
    # Case 5: Unknown format - return as-is and let parser handle it
    logger.warning("Unknown input format, passing through to parser")
    return request_data


# === API Endpoints ===

@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "service": "BRD Agent - Orchestrator API",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "process_brd": "POST /api/process-brd",
            "health": "GET /health",
            "docs": "GET /docs",
            "ingestion": {
                "ingest_document": "POST /api/ingest/document",
                "ingest_repo_path": "POST /api/ingest/repo-path",
                "get_status": "GET /api/ingest/status",
                "list_repos": "GET /api/ingest/repos",
                "delete_document": "DELETE /api/ingest/document",
                "delete_repo": "DELETE /api/ingest/repo"
            }
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "workflow_initialized": _workflow is not None
    }


@app.post("/api/process-brd", response_model=ProcessingResponse)
async def process_brd(request: BRDRequest):
    """
    Process a BRD through the multi-agent pipeline.
    
    Accepts:
    - PDF file (base64 encoded in pdf_file field)
    - JSON BRD (project/features fields)
    - raw_brd_text wrapper
    - brd_data wrapper
    
    Returns:
    - Engineering Plan
    - Project Schedule
    - Processing status and metadata
    """
    logger.info("Received BRD processing request")
    
    try:
        # Convert request to dict
        request_data = request.model_dump(exclude_none=True)
        
        # Normalize input
        normalized_input = normalize_input(request_data)
        
        # Get the workflow
        workflow = get_workflow()
        
        # Run the pipeline
        logger.info("Starting BRD pipeline...")
        result = workflow.run(normalized_input)
        
        # Extract results
        engineering_plan = result.get("engineering_plan", {})
        project_schedule = result.get("project_schedule", {})
        
        # Format response to match what the Streamlit UI expects
        response = ProcessingResponse(
            status=result.get("status", "unknown"),
            message=result.get("message", ""),
            stages_completed=result.get("stages_completed", []),
            timestamp=result.get("timestamp", datetime.utcnow().isoformat()),
            engineering_plan=engineering_plan.get("engineering_plan") if engineering_plan else None,
            project_schedule=project_schedule,
            note="Generated by BRD Agent Python v2.0",
            errors=result.get("errors") if result.get("errors") else None
        )
        
        logger.info(f"BRD processing completed with status: {response.status}")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"BRD processing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"BRD processing failed: {str(e)}"
        )


@app.post("/api/process-brd/upload")
async def process_brd_upload(file: UploadFile = File(...)):
    """
    Process an uploaded PDF BRD file.
    
    Alternative to base64 encoding - direct file upload.
    """
    logger.info(f"Received PDF upload: {file.filename}")
    
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )
    
    try:
        # Read file content
        pdf_content = await file.read()
        
        # Convert to base64 and process
        pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
        
        request = BRDRequest(
            pdf_file=pdf_base64,
            filename=file.filename
        )
        
        return await process_brd(request)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF upload processing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"PDF processing failed: {str(e)}"
        )


# === Run with uvicorn ===

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

