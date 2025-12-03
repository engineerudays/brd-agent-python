"""
BRD Agent - Multi-Agent Engineering Manager
Transform Business Requirements Documents into Engineering Artifacts
"""

__version__ = "2.0.0"
__author__ = "Uday Ammanagi"

# Main exports
from .graph import BRDWorkflow, create_workflow, AgentState
from .agents import ParserAgent, PlannerAgent, SchedulerAgent
from .config import get_settings

__all__ = [
    "BRDWorkflow",
    "create_workflow", 
    "AgentState",
    "ParserAgent",
    "PlannerAgent",
    "SchedulerAgent",
    "get_settings",
]
