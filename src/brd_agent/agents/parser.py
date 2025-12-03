"""
BRD Agent - Parser Agent (Simplified)
Normalizes and validates BRD input for the pipeline.

Note: Heavy lifting (PDF parsing, AI extraction) is done by api/pdf_parser.py
This agent just normalizes various JSON input formats.
"""

import json
import logging
from typing import Union

from .base import BaseAgent


logger = logging.getLogger(__name__)


class ParserAgent(BaseAgent):
    """
    Parser Agent - Normalizes BRD input for the pipeline.
    
    Accepts various JSON input formats and outputs a normalized
    structure that the PlannerAgent can work with.
    
    Input formats supported:
    1. Already structured BRD (from PDF Parser service)
    2. Raw JSON with project/features
    3. String JSON that needs parsing
    """
    
    name = "ParserAgent"
    description = "Normalizes BRD input for the pipeline"
    
    def run(self, input_data: Union[dict, str]) -> dict:
        """
        Normalize BRD input into a consistent format.
        
        Args:
            input_data: BRD data as dict or JSON string
            
        Returns:
            Normalized BRD dict ready for PlannerAgent
        """
        logger.info(f"{self.name}: Normalizing BRD input")
        
        # Step 1: Ensure we have a dict
        if isinstance(input_data, str):
            try:
                data = json.loads(input_data)
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON input: {e}")
                raise ValueError(f"Invalid JSON input: {e}")
        else:
            data = input_data
        
        # Step 2: Validate we have something to work with
        if not data:
            raise ValueError("Empty BRD input")
        
        # Step 3: Normalize to expected format
        normalized = self._normalize(data)
        
        logger.info(f"{self.name}: Normalized BRD - Project: {normalized.get('project', {}).get('name', 'Unknown')}")
        
        return normalized
    
    def _normalize(self, data: dict) -> dict:
        """
        Normalize various input formats to a consistent structure.
        
        Expected output format (matches PDF Parser output):
        {
            "project": {"name": ..., "description": ..., "objectives": [...], "constraints": [...]},
            "features": [...],
            "stakeholders": [...],
            "technical_requirements": {...},
            "success_criteria": [...]
        }
        """
        # If already in expected format (from PDF Parser), return as-is
        if "project" in data and "features" in data:
            return self._ensure_complete(data)
        
        # If wrapped in "data" key (from PDF Parser API response)
        if "data" in data and isinstance(data["data"], dict):
            return self._ensure_complete(data["data"])
        
        # If it's the full ParsedBRD format (from our models)
        if "document_info" in data:
            return self._convert_from_parsed_brd(data)
        
        # If it's a raw_brd_text wrapper (from n8n orchestrator)
        if "raw_brd_text" in data:
            inner = data["raw_brd_text"]
            if isinstance(inner, str):
                inner = json.loads(inner)
            return self._normalize(inner)
        
        # Unknown format - wrap it minimally
        logger.warning(f"{self.name}: Unknown input format, wrapping minimally")
        return {
            "project": {
                "name": data.get("name", "Unknown Project"),
                "description": data.get("description", ""),
                "objectives": data.get("objectives", []),
                "constraints": data.get("constraints", [])
            },
            "features": data.get("features", []),
            "stakeholders": data.get("stakeholders", []),
            "technical_requirements": data.get("technical_requirements", {}),
            "success_criteria": data.get("success_criteria", [])
        }
    
    def _ensure_complete(self, data: dict) -> dict:
        """Ensure all expected fields exist with defaults."""
        return {
            "project": data.get("project", {
                "name": "Unknown Project",
                "description": "",
                "objectives": [],
                "constraints": []
            }),
            "features": data.get("features", []),
            "stakeholders": data.get("stakeholders", []),
            "technical_requirements": data.get("technical_requirements", {}),
            "success_criteria": data.get("success_criteria", [])
        }
    
    def _convert_from_parsed_brd(self, data: dict) -> dict:
        """Convert from our ParsedBRD model format to the simpler format."""
        doc_info = data.get("document_info", {})
        requirements = data.get("requirements", {})
        cad = data.get("constraints_assumptions_dependencies", {})
        
        # Convert functional requirements to features
        features = []
        for req in requirements.get("functional", []):
            features.append({
                "id": req.get("id", f"F{len(features)+1:03d}"),
                "name": req.get("description", "")[:50],  # Use first 50 chars as name
                "description": req.get("description", ""),
                "priority": req.get("priority", "Medium"),
                "requirements": [req.get("rationale", "")] if req.get("rationale") else []
            })
        
        # Convert business objectives to objectives list
        objectives = [
            obj.get("objective", "") 
            for obj in data.get("business_objectives", [])
        ]
        
        return {
            "project": {
                "name": doc_info.get("title", "Unknown Project"),
                "description": data.get("executive_summary", ""),
                "objectives": objectives,
                "constraints": cad.get("constraints", [])
            },
            "features": features,
            "stakeholders": [
                s.get("role", "") for s in data.get("stakeholders", [])
            ],
            "technical_requirements": {
                "platforms": [],
                "integrations": cad.get("dependencies", []),
                "performance": "",
                "security": "",
                "scalability": ""
            },
            "success_criteria": [
                obj.get("metric_success_criteria", "")
                for obj in data.get("business_objectives", [])
                if obj.get("metric_success_criteria")
            ]
        }
