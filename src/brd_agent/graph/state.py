"""
BRD Agent - LangGraph State
Defines the state that flows through the agent pipeline
"""

from typing import Any, Optional
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    """
    State that flows through the BRD Agent pipeline.
    
    Each agent reads from and writes to this state.
    Using total=False makes all fields optional.
    """
    
    # === Input ===
    raw_input: dict  # Original input (PDF or JSON)
    is_pdf: bool  # Whether input is a PDF file
    
    # === After Parser ===
    parsed_brd: dict  # Normalized BRD data
    
    # === After Retriever (RAG) ===
    retrieved_context: Optional[list]  # Retrieved document chunks from RAG
    repo_url: Optional[str]  # Repository URL for RAG (optional, uses default if not provided)
    
    # === After Planner ===
    engineering_plan: dict  # Generated engineering plan
    
    # === After Scheduler ===
    project_schedule: dict  # Generated project schedule
    
    # === Metadata ===
    stages_completed: list[str]  # Track which stages completed
    errors: list[str]  # Any errors encountered
    
    # === Output ===
    status: str  # "success" or "error"
    message: str  # Status message
    timestamp: str  # Completion timestamp

