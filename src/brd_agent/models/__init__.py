"""
BRD Agent - Models Module
Pydantic schemas for BRD, Engineering Plan, Project Schedule
"""

# BRD Input Models
from .brd import (
    BRDInput,
    ParsedBRD,
    DocumentInfo,
    BusinessObjective,
    ProjectScope,
    Stakeholder,
    FunctionalRequirement,
    NonFunctionalRequirement,
    Requirements,
    ConstraintsAssumptionsDependencies,
    Project,
    Feature,
)

# Engineering Plan Models
from .plan import (
    EngineeringPlan,
    EngineeringPlanContent,
    ProjectOverview,
    FeatureBreakdown,
    TechnicalArchitecture,
    ImplementationPhase,
    Risk,
    ResourceRequirements,
    SuccessMetric,
)

# Project Schedule Models
from .schedule import (
    ProjectSchedule,
    ProjectScheduleContent,
    ProjectInfo,
    Phase,
    Task,
    Milestone,
    ResourceAllocation,
    CriticalPathItem,
    RiskTimelineItem,
    KeyDeliverable,
)

__all__ = [
    # BRD Input
    "BRDInput",
    "ParsedBRD",
    "DocumentInfo",
    "BusinessObjective",
    "ProjectScope",
    "Stakeholder",
    "FunctionalRequirement",
    "NonFunctionalRequirement",
    "Requirements",
    "ConstraintsAssumptionsDependencies",
    "Project",
    "Feature",
    # Engineering Plan
    "EngineeringPlan",
    "EngineeringPlanContent",
    "ProjectOverview",
    "FeatureBreakdown",
    "TechnicalArchitecture",
    "ImplementationPhase",
    "Risk",
    "ResourceRequirements",
    "SuccessMetric",
    # Project Schedule
    "ProjectSchedule",
    "ProjectScheduleContent",
    "ProjectInfo",
    "Phase",
    "Task",
    "Milestone",
    "ResourceAllocation",
    "CriticalPathItem",
    "RiskTimelineItem",
    "KeyDeliverable",
]
