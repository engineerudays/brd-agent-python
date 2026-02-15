"""
BRD Agent - Project Schedule Models
Pydantic schemas for Project Schedule output

Updated to match the field names in the LLM prompt (from n8n)
"""

from typing import Optional, Any
from pydantic import BaseModel, Field


# === Project Info ===

class ProjectInfo(BaseModel):
    """Basic project schedule information"""
    project_name: str = Field(default="", description="Project name")
    start_date: str = Field(default="", description="Project start date (YYYY-MM-DD)")
    estimated_end_date: str = Field(default="", description="Estimated end date (YYYY-MM-DD)")
    total_duration_weeks: int = Field(default=0, description="Total duration in weeks")
    total_effort_person_weeks: int = Field(default=0, description="Total effort in person-weeks")
    
    class Config:
        extra = "allow"  # Allow extra fields from LLM


# === Tasks ===

class Task(BaseModel):
    """A single task within a phase"""
    task_id: str = Field(default="", description="Task ID (e.g., T1)")
    task_name: str = Field(default="", description="Task name")
    description: str = Field(default="", description="Task description")
    assigned_to: str = Field(default="", description="Who is assigned")
    start_date: str = Field(default="", description="Task start date (YYYY-MM-DD)")
    end_date: str = Field(default="", description="Task end date (YYYY-MM-DD)")
    effort_days: int = Field(default=0, description="Effort in days")
    status: str = Field(default="Not Started", description="Task status")
    dependencies: list[str] = Field(default_factory=list, description="Task dependencies")
    priority: str = Field(default="Medium", description="Critical/High/Medium/Low")
    
    class Config:
        extra = "allow"


# === Milestones ===

class Milestone(BaseModel):
    """A milestone within a phase"""
    milestone_id: str = Field(default="", description="Milestone ID (e.g., M1)")
    name: str = Field(default="", description="Milestone name")
    target_date: str = Field(default="", description="Target date (YYYY-MM-DD)")
    deliverables: list[str] = Field(default_factory=list, description="Milestone deliverables")
    dependencies: list[str] = Field(default_factory=list, description="Dependencies")
    
    class Config:
        extra = "allow"


# === Phases ===

class Phase(BaseModel):
    """A project phase containing tasks and milestones"""
    phase_id: str = Field(default="", description="Phase ID (e.g., P1)")
    phase_name: str = Field(default="", description="Phase name")
    start_date: str = Field(default="", description="Phase start date (YYYY-MM-DD)")
    end_date: str = Field(default="", description="Phase end date (YYYY-MM-DD)")
    duration_weeks: int = Field(default=0, description="Duration in weeks")
    milestones: list[Milestone] = Field(default_factory=list, description="Phase milestones")
    tasks: list[Task] = Field(default_factory=list, description="Phase tasks")
    
    class Config:
        extra = "allow"


# === Resource Allocation ===

class ResourceAllocation(BaseModel):
    """Resource allocation entry"""
    role: str = Field(default="", description="Role name")
    name: Optional[str] = Field(default=None, description="Person name if assigned")
    allocation: str = Field(default="", description="Allocation percentage or description")
    allocation_percentage: Optional[int] = Field(default=None, description="Allocation as percentage")
    phase: Optional[str] = Field(default=None, description="Which phase they're allocated to")
    start_date: Optional[str] = Field(default=None, description="Start date")
    end_date: Optional[str] = Field(default=None, description="End date")
    key_responsibilities: list[str] = Field(default_factory=list, description="Key responsibilities")
    
    class Config:
        extra = "allow"


# === Critical Path ===

class CriticalPathItem(BaseModel):
    """An item on the critical path"""
    task_id: str = Field(default="", description="Task ID")
    task_name: str = Field(default="", description="Task name")
    duration_days: int = Field(default=0, description="Duration in days")
    slack_days: int = Field(default=0, description="Slack days")
    
    class Config:
        extra = "allow"


# === Risk Timeline ===

class RiskTimelineItem(BaseModel):
    """A risk with timeline context"""
    risk_id: str = Field(default="", description="Risk ID")
    description: str = Field(default="", description="Risk description")
    phase: str = Field(default="", description="Which phase this risk applies to")
    mitigation: str = Field(default="", description="Mitigation strategy")
    impact_on_schedule: str = Field(default="", description="Impact on schedule")
    contingency_buffer_days: int = Field(default=0, description="Contingency buffer in days")
    
    class Config:
        extra = "allow"


# === Key Deliverables ===

class KeyDeliverable(BaseModel):
    """A key project deliverable - flexible to accept various field names from LLM"""
    # Accept both field name variations
    deliverable_id: str = Field(default="", description="Deliverable ID")
    deliverable_name: str = Field(default="", description="Deliverable name (alt)")
    name: str = Field(default="", description="Deliverable name")
    target_date: str = Field(default="", description="Target delivery date")
    due_date: str = Field(default="", description="Due date (alt)")
    phase: str = Field(default="", description="Which phase")
    responsible_team: str = Field(default="", description="Responsible team")
    dependencies: list[str] = Field(default_factory=list, description="Dependencies")
    
    class Config:
        extra = "allow"


# === Main Project Schedule ===

class ProjectScheduleContent(BaseModel):
    """The content of a project schedule"""
    project_info: ProjectInfo = Field(default_factory=ProjectInfo)
    phases: list[Phase] = Field(default_factory=list)
    resource_allocation: list[ResourceAllocation] = Field(default_factory=list)
    critical_path: list[CriticalPathItem] = Field(default_factory=list)
    risk_timeline: list[RiskTimelineItem] = Field(default_factory=list)
    key_deliverables: list[KeyDeliverable] = Field(default_factory=list)
    
    # Optional fields that may be present
    assumptions: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    
    class Config:
        extra = "allow"


class ProjectSchedule(BaseModel):
    """
    Full project schedule output.
    Wraps the content in a 'project_schedule' key for API compatibility.
    """
    success: bool = Field(default=True, description="Whether generation succeeded")
    project_schedule: ProjectScheduleContent = Field(default_factory=ProjectScheduleContent)
    
    # Summary stats
    summary: Optional[dict] = Field(
        default=None,
        description="Summary stats (total_phases, total_tasks, etc.)"
    )
    
    # Visualization data
    visualization: Optional[dict] = Field(
        default=None,
        description="Gantt chart data for visualization"
    )
    
    # Metadata
    metadata: Optional[dict] = Field(
        default=None,
        description="Generation metadata (timestamp, model, etc.)"
    )

    class Config:
        extra = "allow"
