"""
BRD Agent - Engineering Plan Models
Pydantic schemas for Engineering Plan output
"""

from typing import Optional
from pydantic import BaseModel, Field


# === Project Overview ===

class ProjectOverview(BaseModel):
    """High-level project information"""
    name: str = Field(description="Project name")
    description: str = Field(default="", description="Project description")
    objectives: list[str] = Field(default_factory=list, description="Project objectives")


# === Feature Breakdown ===

class FeatureBreakdown(BaseModel):
    """Detailed breakdown of a single feature"""
    feature_id: str = Field(description="Feature ID (e.g., F-01)")
    feature_name: str = Field(description="Feature name")
    description: str = Field(default="", description="Feature description")
    priority: str = Field(default="Medium", description="Critical/High/Medium/Low")
    complexity: str = Field(default="Medium", description="High/Medium/Low")
    estimated_effort: str = Field(default="", description="Effort estimate (e.g., '2 weeks')")
    dependencies: list[str] = Field(default_factory=list, description="Feature dependencies")
    technical_requirements: list[str] = Field(default_factory=list, description="Technical requirements")
    acceptance_criteria: list[str] = Field(default_factory=list, description="Acceptance criteria")


# === Technical Architecture ===

class TechnicalArchitecture(BaseModel):
    """System architecture overview"""
    system_components: list[str] = Field(default_factory=list, description="Main system components")
    integration_points: list[str] = Field(default_factory=list, description="External integrations")
    data_flow: str = Field(default="", description="Data flow description")
    security_considerations: list[str] = Field(default_factory=list, description="Security considerations")


# === Implementation Phases ===

class ImplementationPhase(BaseModel):
    """A single implementation phase"""
    phase_number: int = Field(description="Phase number")
    phase_name: str = Field(description="Phase name")
    description: str = Field(default="", description="Phase description")
    features_included: list[str] = Field(default_factory=list, description="Features in this phase")
    estimated_duration: str = Field(default="", description="Duration estimate")
    deliverables: list[str] = Field(default_factory=list, description="Phase deliverables")


# === Risk Analysis ===

class Risk(BaseModel):
    """A single risk item"""
    risk_id: str = Field(description="Risk ID (e.g., R-01)")
    description: str = Field(description="Risk description")
    impact: str = Field(default="Medium", description="High/Medium/Low")
    probability: str = Field(default="Medium", description="High/Medium/Low")
    mitigation_strategy: str = Field(default="", description="How to mitigate this risk")


# === Resource Requirements ===

class ResourceRequirements(BaseModel):
    """Team and resource needs"""
    team_composition: list[str] = Field(default_factory=list, description="Required team members/roles")
    tools_and_technologies: list[str] = Field(default_factory=list, description="Required tools/tech")
    infrastructure_needs: list[str] = Field(default_factory=list, description="Infrastructure requirements")


# === Success Metrics ===

class SuccessMetric(BaseModel):
    """A single success metric"""
    metric_name: str = Field(description="Metric name")
    target_value: str = Field(default="", description="Target value")
    measurement_method: str = Field(default="", description="How to measure")


# === Main Engineering Plan ===

class EngineeringPlanContent(BaseModel):
    """The content of an engineering plan"""
    project_overview: ProjectOverview = Field(default_factory=ProjectOverview)
    feature_breakdown: list[FeatureBreakdown] = Field(default_factory=list)
    technical_architecture: TechnicalArchitecture = Field(default_factory=TechnicalArchitecture)
    implementation_phases: list[ImplementationPhase] = Field(default_factory=list)
    risk_analysis: list[Risk] = Field(default_factory=list)
    resource_requirements: ResourceRequirements = Field(default_factory=ResourceRequirements)
    success_metrics: list[SuccessMetric] = Field(default_factory=list)


class EngineeringPlan(BaseModel):
    """
    Full engineering plan output.
    Wraps the content in an 'engineering_plan' key for API compatibility.
    """
    engineering_plan: EngineeringPlanContent = Field(default_factory=EngineeringPlanContent)
    
    # Metadata
    metadata: Optional[dict] = Field(
        default=None,
        description="Generation metadata (timestamp, model, etc.)"
    )

