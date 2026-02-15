"""
BRD Agent - Planner Agent
Generates Engineering Plans from parsed BRD
(Prompts migrated from n8n structured_plan_generator.json)
"""

import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

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
        retrieved_context: Optional[List[Dict[str, Any]]] = None,
        include_metadata: bool = True
    ) -> EngineeringPlan:
        """
        Generate an Engineering Plan from a parsed BRD, optionally using retrieved context.
        
        Args:
            parsed_brd: Parsed BRD to plan from
            retrieved_context: Optional list of retrieved document chunks from RAG
            include_metadata: Whether to include generation metadata
        
        Returns:
            EngineeringPlan with full feature breakdown and phases
        """
        logger.info(f"{self.name}: Generating engineering plan for '{parsed_brd.document_info.title}'")
        
        if retrieved_context:
            logger.info(f"{self.name}: Using {len(retrieved_context)} retrieved chunks for context-aware planning")
        else:
            logger.info(f"{self.name}: No retrieved context provided (RAG disabled or unavailable)")
        
        # Convert ParsedBRD to dict for the prompt (matches n8n behavior)
        full_brd = parsed_brd.model_dump()
        
        # Build the prompt with optional System Context
        prompt = self._build_prompt(full_brd, retrieved_context=retrieved_context)
        
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
        
        # Generate metadata with source citations if context was used
        metadata = None
        if include_metadata:
            metadata = self._generate_metadata(parsed_brd, retrieved_context=retrieved_context)
        
        result = EngineeringPlan(
            engineering_plan=content,
            metadata=metadata
        )
        
        logger.info(
            f"{self.name}: Generated plan with "
            f"{len(content.feature_breakdown)} features, "
            f"{len(content.implementation_phases)} phases"
        )
        
        return result
    
    def _build_prompt(self, full_brd: dict, retrieved_context: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        Build the prompt with optional System Context from retrieved chunks.
        
        Args:
            full_brd: Parsed BRD as dictionary
            retrieved_context: Optional list of retrieved document chunks
        """
        # Build System Context section if chunks are available
        system_context_section = ""
        if retrieved_context and len(retrieved_context) > 0:
            # Prioritize chunks by relevance (lower distance = more relevant)
            sorted_chunks = sorted(
                retrieved_context,
                key=lambda x: x.get('distance', float('inf')) if x.get('distance') is not None else float('inf')
            )
            
            # Limit to top 20 chunks to avoid token limit issues
            top_chunks = sorted_chunks[:20]
            
            # Group chunks by source file for better organization
            chunks_by_source = {}
            for chunk in top_chunks:
                source = chunk.get('source', 'unknown')
                if source not in chunks_by_source:
                    chunks_by_source[source] = []
                chunks_by_source[source].append(chunk)
            
            # Format chunks with source citations
            context_parts = []
            for source, chunks in chunks_by_source.items():
                context_parts.append(f"\n[Source: {source}]")
                for chunk in chunks:
                    content = chunk.get('content', '').strip()
                    if content:
                        # Truncate very long chunks (keep first 500 chars)
                        if len(content) > 500:
                            content = content[:500] + "..."
                        context_parts.append(f"Content: {content}")
            
            system_context_section = f"""
## System Context (Existing Architecture and Patterns)

The following context has been retrieved from the existing system's documentation. Use this information to align your engineering plan with existing architecture patterns, technologies, and conventions.

{''.join(context_parts)}

**IMPORTANT**: Use the System Context above to:
- Align your engineering plan with existing architecture patterns
- Reference specific patterns, technologies, and conventions found in the System Context
- Ensure technical recommendations match the existing tech stack and architecture
- Cite source files when referencing existing patterns (e.g., "As documented in docs/api.md...")
- Do NOT suggest technologies or patterns that conflict with the existing system

---
"""
        
        return f"""You are an expert Software Engineering Manager and Technical Architect. Your task is to create a comprehensive, structured engineering plan based on a Business Requirements Document (BRD).

{system_context_section}Here is the complete BRD:
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
{f"9. **CRITICAL**: If System Context was provided above, ensure your plan aligns with existing architecture patterns, uses the same tech stack, and follows established conventions. Reference source files when applicable." if retrieved_context and len(retrieved_context) > 0 else ""}

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
    
    def _generate_metadata(
        self, 
        brd: ParsedBRD, 
        retrieved_context: Optional[List[Dict[str, Any]]] = None
    ) -> dict:
        """
        Generate metadata for the engineering plan (matches n8n structure).
        
        Args:
            brd: Parsed BRD used for planning
            retrieved_context: Optional retrieved chunks used for context
        """
        metadata = {
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
        
        # Add source citations if context was used
        if retrieved_context and len(retrieved_context) > 0:
            # Extract unique source files
            sources = list(set([
                chunk.get('source', 'unknown') 
                for chunk in retrieved_context 
                if chunk.get('source')
            ]))
            
            metadata["rag_context"] = {
                "enabled": True,
                "chunks_used": len(retrieved_context),
                "source_files": sources,
                "note": "Plan generated using retrieved context from existing system documentation"
            }
        else:
            metadata["rag_context"] = {
                "enabled": False,
                "note": "Plan generated without RAG context"
            }
        
        return metadata
