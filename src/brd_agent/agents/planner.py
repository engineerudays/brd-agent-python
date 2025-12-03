"""
BRD Agent - Planner Agent
Generates Engineering Plans from parsed BRD
(Prompts migrated from n8n structured_plan_generator.json)
"""

import json
import logging
from datetime import datetime
from typing import Optional

from .base import BaseAgent
from ..models.brd import ParsedBRD
from ..models.plan import EngineeringPlan, EngineeringPlanContent


logger = logging.getLogger(__name__)


class PlannerAgent(BaseAgent):
    """
    Planner Agent - Generates Engineering Plans from parsed BRDs.
    
    Takes a ParsedBRD and produces a comprehensive EngineeringPlan
    with features, phases, risks, and resource requirements.
    
    Migrated from n8n: planning_agent/engineering_plan/structured_plan_generator.json
    """
    
    name = "PlannerAgent"
    description = "Generates Engineering Plans from Business Requirements"
    
    def run(
        self,
        parsed_brd: ParsedBRD,
        include_metadata: bool = True
    ) -> EngineeringPlan:
        """
        Generate an Engineering Plan from a parsed BRD.
        
        Args:
            parsed_brd: Parsed BRD to plan from
            include_metadata: Whether to include generation metadata
            
        Returns:
            EngineeringPlan with full feature breakdown and phases
        """
        logger.info(f"{self.name}: Generating engineering plan for '{parsed_brd.document_info.title}'")
        
        # Convert ParsedBRD to dict for the prompt (matches n8n behavior)
        full_brd = parsed_brd.model_dump()
        
        # Build the exact prompt from n8n workflow
        prompt = self._build_prompt(full_brd)
        
        # Call LLM (matches n8n: claude-3-haiku, temp=0.7, max_tokens=4096)
        response_text = self.llm.generate(
            prompt=prompt,
            max_tokens=4096,
            temperature=0.7
        )
        
        # Parse the response (with markdown cleanup like n8n does)
        plan_data = self._parse_response(response_text)
        
        # Build the EngineeringPlan
        content = EngineeringPlanContent.model_validate(plan_data.get("engineering_plan", plan_data))
        
        result = EngineeringPlan(
            engineering_plan=content,
            metadata=self._generate_metadata(parsed_brd) if include_metadata else None
        )
        
        logger.info(
            f"{self.name}: Generated plan with "
            f"{len(content.feature_breakdown)} features, "
            f"{len(content.implementation_phases)} phases"
        )
        
        return result
    
    def _build_prompt(self, full_brd: dict) -> str:
        """
        Build the exact prompt from n8n structured_plan_generator.json
        """
        return f"""You are an expert Software Engineering Manager and Technical Architect. Your task is to create a comprehensive, structured engineering plan based on a Business Requirements Document (BRD).

Here is the complete BRD:
{json.dumps(full_brd, indent=2)}

Please analyze this BRD thoroughly and generate a detailed, comprehensive Structured Engineering Plan in JSON format with the following structure:

{{
  "engineering_plan": {{
    "project_overview": {{
      "name": "string",
      "description": "string",
      "objectives": ["string"]
    }},
    "feature_breakdown": [
      {{
        "feature_id": "string",
        "feature_name": "string",
        "description": "string",
        "priority": "Critical|High|Medium|Low",
        "complexity": "High|Medium|Low",
        "estimated_effort": "string (e.g., 2 weeks)",
        "dependencies": ["string"],
        "technical_requirements": ["string"],
        "acceptance_criteria": ["string"]
      }}
    ],
    "technical_architecture": {{
      "system_components": ["string"],
      "integration_points": ["string"],
      "data_flow": "string",
      "security_considerations": ["string"]
    }},
    "implementation_phases": [
      {{
        "phase_number": "number",
        "phase_name": "string",
        "description": "string",
        "features_included": ["string"],
        "estimated_duration": "string",
        "deliverables": ["string"]
      }}
    ],
    "risk_analysis": [
      {{
        "risk_id": "string",
        "description": "string",
        "impact": "High|Medium|Low",
        "probability": "High|Medium|Low",
        "mitigation_strategy": "string"
      }}
    ],
    "resource_requirements": {{
      "team_composition": ["string"],
      "tools_and_technologies": ["string"],
      "infrastructure_needs": ["string"]
    }},
    "success_metrics": [
      {{
        "metric_name": "string",
        "target_value": "string",
        "measurement_method": "string"
      }}
    ]
  }}
}}

IMPORTANT GUIDELINES:
1. Be EXTREMELY thorough and detailed in every section
2. For each feature, provide comprehensive technical requirements and acceptance criteria (at least 2-4 items each)
3. Include specific technology recommendations where applicable (e.g., OAuth 2.0, SAML 2.0, specific frameworks)
4. Provide realistic effort estimates (in weeks or months)
5. Include detailed risk mitigation strategies for each identified risk
6. Be specific about team roles, tools, and infrastructure needs
7. Ensure all dependencies and integration points are clearly identified
8. Return ONLY valid JSON, no markdown formatting, no explanation text. Start with {{ and end with }}.

Focus on technical feasibility, implementation details, and actionable recommendations. This plan will be used by engineering teams, so be as specific and detailed as possible."""
    
    def _parse_response(self, response_text: str) -> dict:
        """
        Parse LLM response, cleaning up markdown if present (matches n8n logic).
        """
        ai_response = response_text.strip()
        
        # Clean up markdown formatting if present (from n8n)
        if ai_response.startswith("```json"):
            ai_response = ai_response[7:]
        elif ai_response.startswith("```"):
            ai_response = ai_response[3:]
        if ai_response.endswith("```"):
            ai_response = ai_response[:-3]
        ai_response = ai_response.strip()
        
        try:
            return json.loads(ai_response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Raw response: {response_text[:500]}...")
            # Return error structure like n8n does
            return {
                "engineering_plan": {
                    "raw_response": response_text,
                    "parsing_error": str(e),
                    "generated_at": datetime.utcnow().isoformat(),
                    "note": "AI response could not be parsed as JSON"
                }
            }
    
    def _generate_metadata(self, brd: ParsedBRD) -> dict:
        """Generate metadata for the engineering plan (matches n8n structure)."""
        return {
            "generated_by": "Planning Agent - Engineering Plan Generator",
            "timestamp": datetime.utcnow().isoformat(),
            "source_brd": brd.document_info.title,
            "version": "1.0",
            "ai_model": getattr(self.llm, 'model', 'claude-3-haiku-20240307'),
            "tokens_used": {
                "input": 0,  # Would need to track from LLM response
                "output": 0
            }
        }
