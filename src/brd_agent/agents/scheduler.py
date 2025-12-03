"""
BRD Agent - Scheduler Agent
Generates Project Schedules from Engineering Plans
(Prompts migrated from n8n project_schedule_generator.json)
"""

import json
import logging
from datetime import datetime
from typing import Optional

from .base import BaseAgent
from ..models.plan import EngineeringPlan
from ..models.schedule import ProjectSchedule, ProjectScheduleContent


logger = logging.getLogger(__name__)


class SchedulerAgent(BaseAgent):
    """
    Scheduler Agent - Generates Project Schedules from Engineering Plans.
    
    Takes an EngineeringPlan and produces a detailed ProjectSchedule
    with phases, tasks, milestones, and resource allocation.
    
    Migrated from n8n: planning_agent/project_schedule/project_schedule_generator.json
    """
    
    name = "SchedulerAgent"
    description = "Generates Project Schedules from Engineering Plans"
    
    def run(
        self,
        engineering_plan: EngineeringPlan,
        start_date: Optional[str] = None,
        include_metadata: bool = True
    ) -> ProjectSchedule:
        """
        Generate a Project Schedule from an Engineering Plan.
        
        Args:
            engineering_plan: Engineering plan to schedule
            start_date: Project start date (YYYY-MM-DD), defaults to today
            include_metadata: Whether to include generation metadata
            
        Returns:
            ProjectSchedule with phases, tasks, and timeline
        """
        plan = engineering_plan.engineering_plan
        project_name = plan.project_overview.name
        
        logger.info(f"{self.name}: Generating schedule for '{project_name}'")
        
        # Use today's date as default (matches n8n behavior)
        if not start_date:
            start_date = datetime.now().strftime("%Y-%m-%d")
        
        # Extract scheduling information (matches n8n Parse Engineering Plan node)
        schedule_input = {
            "project_name": plan.project_overview.name or "Unnamed Project",
            "features": [f.model_dump() for f in plan.feature_breakdown],
            "phases": [p.model_dump() for p in plan.implementation_phases],
            "risks": [r.model_dump() for r in plan.risk_analysis],
            "resources": plan.resource_requirements.model_dump(),
            "total_features": len(plan.feature_breakdown),
            "total_phases": len(plan.implementation_phases),
        }
        
        # Build the exact prompt from n8n workflow
        prompt = self._build_prompt(schedule_input, start_date)
        
        # Call LLM (matches n8n: claude-3-haiku, temp=0.7, max_tokens=4000)
        response_text = self.llm.generate(
            prompt=prompt,
            max_tokens=4000,
            temperature=0.7
        )
        
        # Parse the response
        schedule_data = self._parse_response(response_text)
        
        # Build the ProjectSchedule
        content = ProjectScheduleContent.model_validate(
            schedule_data.get("project_schedule", schedule_data)
        )
        
        # Calculate summary stats (matches n8n)
        summary = self._calculate_summary(content)
        
        # Generate Gantt chart data (matches n8n Generate Gantt Chart Data node)
        gantt_data = self._generate_gantt_data(content)
        
        result = ProjectSchedule(
            success=True,
            project_schedule=content,
            summary=summary,
            visualization={"gantt_chart": gantt_data},
            metadata=self._generate_metadata(project_name, start_date) if include_metadata else None
        )
        
        logger.info(
            f"{self.name}: Generated schedule with "
            f"{len(content.phases)} phases, "
            f"{summary['total_tasks']} tasks, "
            f"{summary['total_milestones']} milestones"
        )
        
        return result
    
    def _build_prompt(self, data: dict, current_date: str) -> str:
        """
        Build the exact prompt from n8n project_schedule_generator.json
        """
        return f"""You are an expert Project Manager and Engineering Leader specializing in software project scheduling and resource planning.

Based on the following Engineering Plan, create a detailed Project Schedule:

Project: {data['project_name']}
Total Features: {data['total_features']}
Implementation Phases: {json.dumps(data['phases'])}
Features Details: {json.dumps(data['features'])}
Risks: {json.dumps(data['risks'])}
Resource Requirements: {json.dumps(data['resources'])}

**IMPORTANT: Use {current_date} as the project start date (today's date).**

Generate a comprehensive Project Schedule in JSON format with this structure:

{{
  "project_schedule": {{
    "project_info": {{
      "project_name": "string",
      "start_date": "YYYY-MM-DD",
      "estimated_end_date": "YYYY-MM-DD",
      "total_duration_weeks": "number",
      "total_effort_person_weeks": "number"
    }},
    "phases": [
      {{
        "phase_id": "string",
        "phase_name": "string",
        "start_date": "YYYY-MM-DD",
        "end_date": "YYYY-MM-DD",
        "duration_weeks": "number",
        "milestones": [
          {{
            "milestone_id": "string",
            "name": "string",
            "target_date": "YYYY-MM-DD",
            "deliverables": ["string"],
            "dependencies": ["string"]
          }}
        ],
        "tasks": [
          {{
            "task_id": "string",
            "task_name": "string",
            "description": "string",
            "assigned_to": "string (role)",
            "start_date": "YYYY-MM-DD",
            "end_date": "YYYY-MM-DD",
            "effort_days": "number",
            "status": "Not Started|In Progress|Completed",
            "dependencies": ["string"],
            "priority": "Critical|High|Medium|Low"
          }}
        ]
      }}
    ],
    "resource_allocation": [
      {{
        "role": "string",
        "allocation_percentage": "number",
        "start_date": "YYYY-MM-DD",
        "end_date": "YYYY-MM-DD",
        "key_responsibilities": ["string"]
      }}
    ],
    "critical_path": [
      {{
        "task_id": "string",
        "task_name": "string",
        "duration_days": "number",
        "slack_days": "number"
      }}
    ],
    "risk_timeline": [
      {{
        "risk_id": "string",
        "description": "string",
        "impact_on_schedule": "string",
        "contingency_buffer_days": "number"
      }}
    ],
    "key_deliverables": [
      {{
        "deliverable_name": "string",
        "due_date": "YYYY-MM-DD",
        "responsible_team": "string",
        "dependencies": ["string"]
      }}
    ],
    "assumptions": ["string"],
    "constraints": ["string"]
  }}
}}

IMPORTANT: 
- Return ONLY valid JSON, no markdown formatting, no explanation text. Start with {{ and end with }}.
- Use {current_date} as the start_date for the project.
- Calculate all other dates relative to {current_date}.
- Be realistic with timelines, account for dependencies, and include buffer time for risks.
- Provide specific dates in YYYY-MM-DD format and detailed task breakdowns."""
    
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
                "project_schedule": {
                    "raw_response": response_text,
                    "parsing_error": str(e),
                    "generated_at": datetime.utcnow().isoformat(),
                    "note": "AI response could not be parsed as JSON"
                }
            }
    
    def _calculate_summary(self, content: ProjectScheduleContent) -> dict:
        """Calculate summary statistics (matches n8n Format Schedule Output node)."""
        total_tasks = sum(len(phase.tasks) for phase in content.phases)
        total_milestones = sum(len(phase.milestones) for phase in content.phases)
        
        return {
            "total_phases": len(content.phases),
            "total_tasks": total_tasks,
            "total_milestones": total_milestones,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    def _generate_gantt_data(self, content: ProjectScheduleContent) -> dict:
        """
        Generate Gantt chart data for visualization.
        Matches n8n Generate Gantt Chart Data node exactly.
        """
        gantt_data = {
            "chart_type": "gantt",
            "project_name": content.project_info.project_name,
            "start_date": content.project_info.start_date,
            "end_date": content.project_info.estimated_end_date,
            "tasks": []
        }
        
        # Convert phases and tasks to Gantt format (exact n8n logic)
        for phase_index, phase in enumerate(content.phases):
            # Add phase as a group
            gantt_data["tasks"].append({
                "id": f"phase-{phase_index}",
                "name": phase.phase_name,
                "start": phase.start_date,
                "end": phase.end_date,
                "type": "phase",
                "progress": 0,
                "dependencies": []
            })
            
            # Add tasks under the phase
            for task_index, task in enumerate(phase.tasks):
                progress = 0
                if task.status == "Completed":
                    progress = 100
                elif task.status == "In Progress":
                    progress = 50
                
                gantt_data["tasks"].append({
                    "id": task.task_id or f"task-{phase_index}-{task_index}",
                    "name": task.task_name,
                    "start": task.start_date,
                    "end": task.end_date,
                    "type": "task",
                    "progress": progress,
                    "dependencies": task.dependencies,
                    "assigned_to": task.assigned_to,
                    "priority": task.priority,
                    "parent": f"phase-{phase_index}"
                })
        
        gantt_data["generated_at"] = datetime.utcnow().isoformat()
        
        return gantt_data
    
    def _generate_metadata(self, project_name: str, start_date: str) -> dict:
        """Generate metadata for the project schedule (matches n8n structure)."""
        return {
            "generated_by": "Planning Agent - Project Schedule Generator",
            "timestamp": datetime.utcnow().isoformat(),
            "source_plan": project_name,
            "version": "1.0",
            "ai_model": getattr(self.llm, 'model', 'claude-3-haiku-20240307'),
            "tokens_used": {
                "input": 0,  # Would need to track from LLM response
                "output": 0
            }
        }
