"""
BRD Agent - Project Schedule Models
Pydantic schemas for Project Schedule output
"""

from typing import Optional
from pydantic import BaseModel, Field


# === Project Info ===

class ProjectInfo(BaseModel):
    """Basic project schedule information"""
    project_name: str = Field(description="Project name")
    start_date: str = Field(description="Project start date (YYYY-MM-DD)")
    estimated_end_date: str = Field(default="", description="Estimated end date (YYYY-MM-DD)")
    total_duration_weeks: int = Field(default=0, description="Total duration in weeks")
    total_effort_person_weeks: int = Field(default=0, description="Total effort in person-weeks")


# === Tasks ===

class Task(BaseModel):
    """A single task within a phase"""
    task_id: str = Field(description="Task ID (e.g., T1)")
    task_name: str = Field(description="Task name")
    description: str = Field(default="", description="Task description")
    assigned_to: str = Field(default="", description="Who is assigned")
    start_date: str = Field(description="Task start date (YYYY-MM-DD)")
    end_date: str = Field(description="Task end date (YYYY-MM-DD)")
    effort_days: int = Field(default=0, description="Effort in days")
    status: str = Field(default="Not Started", description="Task status")
    dependencies: list[str] = Field(default_factory=list, description="Task dependencies")
    priority: str = Field(default="Medium", description="Critical/High/Medium/Low")


# === Milestones ===

class Milestone(BaseModel):
    """A milestone within a phase"""
    milestone_id: str = Field(description="Milestone ID (e.g., M1)")
    name: str = Field(description="Milestone name")
    target_date: str = Field(description="Target date (YYYY-MM-DD)")
    deliverables: list[str] = Field(default_factory=list, description="Milestone deliverables")
    dependencies: list[str] = Field(default_factory=list, description="Dependencies")


# === Phases ===

class Phase(BaseModel):
    """A project phase containing tasks and milestones"""
    phase_id: str = Field(description="Phase ID (e.g., P1)")
    phase_name: str = Field(description="Phase name")
    start_date: str = Field(description="Phase start date (YYYY-MM-DD)")
    end_date: str = Field(description="Phase end date (YYYY-MM-DD)")
    duration_weeks: int = Field(default=0, description="Duration in weeks")
    milestones: list[Milestone] = Field(default_factory=list, description="Phase milestones")
    tasks: list[Task] = Field(default_factory=list, description="Phase tasks")


# === Resource Allocation ===

class ResourceAllocation(BaseModel):
    """Resource allocation entry"""
    role: str = Field(description="Role name")
    name: Optional[str] = Field(default=None, description="Person name if assigned")
    allocation: str = Field(default="", description="Allocation percentage or description")
    phase: Optional[str] = Field(default=None, description="Which phase they're allocated to")


# === Critical Path ===

class CriticalPathItem(BaseModel):
    """An item on the critical path"""
    task_id: str = Field(description="Task ID")
    task_name: str = Field(description="Task name")
    duration_days: int = Field(default=0, description="Duration in days")


# === Risk Timeline ===

class RiskTimelineItem(BaseModel):
    """A risk with timeline context"""
    risk_id: str = Field(description="Risk ID")
    description: str = Field(description="Risk description")
    phase: str = Field(default="", description="Which phase this risk applies to")
    mitigation: str = Field(default="", description="Mitigation strategy")


# === Key Deliverables ===

class KeyDeliverable(BaseModel):
    """A key project deliverable"""
    deliverable_id: str = Field(description="Deliverable ID")
    name: str = Field(description="Deliverable name")
    target_date: str = Field(description="Target delivery date")
    phase: str = Field(default="", description="Which phase")


# === Main Project Schedule ===

class ProjectScheduleContent(BaseModel):
    """The content of a project schedule"""
    project_info: ProjectInfo = Field(default_factory=lambda: ProjectInfo(
        project_name="",
        start_date="",
    ))
    phases: list[Phase] = Field(default_factory=list)
    resource_allocation: list[ResourceAllocation] = Field(default_factory=list)
    critical_path: list[CriticalPathItem] = Field(default_factory=list)
    risk_timeline: list[RiskTimelineItem] = Field(default_factory=list)
    key_deliverables: list[KeyDeliverable] = Field(default_factory=list)
    
    # Optional fields that may be present
    assumptions: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)


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

