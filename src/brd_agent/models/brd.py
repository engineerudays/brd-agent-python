"""
BRD Agent - BRD Input Models
Pydantic schemas for Business Requirements Document input
"""

from typing import Optional
from pydantic import BaseModel, Field


# === Document Info ===

class DocumentInfo(BaseModel):
    """BRD document metadata"""
    title: str = Field(default="Untitled Project")
    version: str = Field(default="1.0")
    status: str = Field(default="Draft")
    date: Optional[str] = None


# === Business Objectives ===

class BusinessObjective(BaseModel):
    """A single business objective"""
    id: str = Field(description="Objective ID (e.g., BO-01)")
    objective: str = Field(description="Objective name")
    metric_success_criteria: str = Field(default="", description="How success is measured")
    priority: str = Field(default="Should", description="Must/Should/Could/Won't")


# === Project Scope ===

class ProjectScope(BaseModel):
    """What's in and out of scope"""
    in_scope: list[str] = Field(default_factory=list)
    out_of_scope: list[str] = Field(default_factory=list)


# === Stakeholders ===

class Stakeholder(BaseModel):
    """A project stakeholder"""
    role: str = Field(description="Role title")
    team: str = Field(default="", description="Team or department")
    responsibility: str = Field(default="", description="What they're responsible for")


# === Requirements ===

class FunctionalRequirement(BaseModel):
    """A functional requirement"""
    id: str = Field(description="Requirement ID (e.g., FR-01)")
    description: str = Field(description="Requirement description")
    priority: str = Field(default="Medium", description="Critical/High/Medium/Low")
    rationale: str = Field(default="", description="Why this requirement exists")


class NonFunctionalRequirement(BaseModel):
    """A non-functional requirement"""
    id: str = Field(description="Requirement ID (e.g., NFR-01)")
    description: str = Field(description="Requirement description")
    category: str = Field(default="", description="Category (Speed, Security, etc.)")
    priority: str = Field(default="Medium", description="Critical/High/Medium/Low")


class Requirements(BaseModel):
    """All requirements"""
    functional: list[FunctionalRequirement] = Field(default_factory=list)
    non_functional: list[NonFunctionalRequirement] = Field(default_factory=list)


# === Constraints, Assumptions, Dependencies ===

class ConstraintsAssumptionsDependencies(BaseModel):
    """Project constraints, assumptions, and dependencies"""
    constraints: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)


# === Main BRD Structure ===

class ParsedBRD(BaseModel):
    """
    Fully parsed BRD structure.
    This is the internal representation after parsing raw BRD text.
    """
    document_info: DocumentInfo = Field(default_factory=DocumentInfo)
    executive_summary: str = Field(default="")
    business_objectives: list[BusinessObjective] = Field(default_factory=list)
    project_scope: ProjectScope = Field(default_factory=ProjectScope)
    stakeholders: list[Stakeholder] = Field(default_factory=list)
    requirements: Requirements = Field(default_factory=Requirements)
    constraints_assumptions_dependencies: ConstraintsAssumptionsDependencies = Field(
        default_factory=ConstraintsAssumptionsDependencies
    )


# === Input Formats ===

class BRDInput(BaseModel):
    """
    BRD input - accepts multiple formats:
    1. raw_brd_text: JSON string of the full BRD
    2. pdf_file: Base64 encoded PDF (will be parsed)
    3. Direct fields: project, features, etc.
    """
    # Format 1: Raw BRD text (JSON string)
    raw_brd_text: Optional[str] = Field(
        default=None,
        description="Raw BRD as JSON string"
    )
    
    # Format 2: PDF file (base64 encoded)
    pdf_file: Optional[str] = Field(
        default=None,
        description="Base64 encoded PDF file"
    )
    filename: Optional[str] = Field(
        default=None,
        description="Original filename (for PDF uploads)"
    )
    
    # Format 3: Direct project/features structure (simpler format)
    project: Optional[dict] = Field(
        default=None,
        description="Project info (name, description, objectives)"
    )
    features: Optional[list[dict]] = Field(
        default=None,
        description="List of features"
    )


# === Simplified Project Format (alternative input) ===

class Feature(BaseModel):
    """A simplified feature definition"""
    id: str = Field(description="Feature ID")
    name: str = Field(description="Feature name")
    description: str = Field(default="")
    priority: str = Field(default="Medium", description="Critical/High/Medium/Low")


class Project(BaseModel):
    """Simplified project definition"""
    name: str = Field(description="Project name")
    description: str = Field(default="")
    objectives: list[str] = Field(default_factory=list)
    features: list[Feature] = Field(default_factory=list)

