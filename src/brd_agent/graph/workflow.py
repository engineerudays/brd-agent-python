"""
BRD Agent - LangGraph Workflow
Defines the agent pipeline using LangGraph
"""

import logging
from datetime import datetime
from typing import Optional

from langgraph.graph import StateGraph, END

from .state import AgentState
from ..agents import ParserAgent, PlannerAgent, SchedulerAgent, RetrieverAgent
from ..services.llm import LLMService, get_llm_service
from ..config import get_settings


logger = logging.getLogger(__name__)


class BRDWorkflow:
    """
    LangGraph workflow that orchestrates the BRD agent pipeline.
    
    Pipeline:
        Input → Parser → Retriever (RAG) → Planner → Scheduler → Output
    """
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        """
        Initialize the workflow with agents.
        
        Args:
            llm_service: Optional LLM service to share across agents
        """
        self.llm = llm_service or get_llm_service()
        
        # Initialize agents with shared LLM service
        self.parser = ParserAgent(llm_service=self.llm)
        self.retriever = RetrieverAgent(llm_service=self.llm)
        self.planner = PlannerAgent(llm_service=self.llm)
        self.scheduler = SchedulerAgent(llm_service=self.llm)
        self.settings = get_settings()
        
        # Build the graph
        self.graph = self._build_graph()
        
        logger.info("BRDWorkflow initialized")
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state graph."""
        
        # Create the graph with our state type
        workflow = StateGraph(AgentState)
        
        # Add nodes (each node is a function that takes state and returns updated state)
        workflow.add_node("parser", self._parser_node)
        workflow.add_node("retriever", self._retriever_node)
        workflow.add_node("planner", self._planner_node)
        workflow.add_node("scheduler", self._scheduler_node)
        workflow.add_node("finalize", self._finalize_node)
        
        # Define the edges (flow)
        workflow.set_entry_point("parser")
        workflow.add_edge("parser", "retriever")
        workflow.add_edge("retriever", "planner")
        workflow.add_edge("planner", "scheduler")
        workflow.add_edge("scheduler", "finalize")
        workflow.add_edge("finalize", END)
        
        # Compile the graph
        return workflow.compile()
    
    def _parser_node(self, state: AgentState) -> AgentState:
        """Parser node - normalizes BRD input."""
        logger.info("Workflow: Running Parser node")
        
        try:
            raw_input = state.get("raw_input", {})
            
            # Run the parser agent
            parsed_brd = self.parser.run(raw_input)
            
            # Update state
            stages = state.get("stages_completed", [])
            stages.append("brd_parsing")
            
            return {
                **state,
                "parsed_brd": parsed_brd,
                "stages_completed": stages
            }
            
        except Exception as e:
            logger.error(f"Parser node failed: {e}")
            errors = state.get("errors", [])
            errors.append(f"Parser error: {str(e)}")
            return {
                **state,
                "errors": errors,
                "status": "error",
                "message": f"BRD parsing failed: {str(e)}"
            }
    
    def _retriever_node(self, state: AgentState) -> AgentState:
        """Retriever node - retrieves relevant context from ingested repositories (RAG)."""
        logger.info("Workflow: Running Retriever node")
        
        # Skip if previous stage failed
        if state.get("status") == "error":
            return state
        
        # Check if RAG is enabled
        if not self.settings.rag_enabled:
            logger.info("RAG is disabled in config, skipping retrieval")
            return {
                **state,
                "retrieved_context": None,
                "stages_completed": state.get("stages_completed", [])
            }
        
        try:
            parsed_brd = state.get("parsed_brd", {})
            
            # Get repo_url from state or use default
            repo_url = state.get("repo_url") or self.settings.default_repo_url
            
            # Convert dict to ParsedBRD model for retriever
            from ..models.brd import ParsedBRD
            
            try:
                brd_model = self._dict_to_parsed_brd(parsed_brd)
            except Exception:
                # Create minimal ParsedBRD if conversion fails
                brd_model = ParsedBRD(
                    document_info={"title": parsed_brd.get("project", {}).get("name", "Unknown Project")},
                    executive_summary=parsed_brd.get("project", {}).get("description", ""),
                )
            
            # Check if collection exists before querying
            from ..services.vector_store import VectorStore
            vector_store = VectorStore()
            
            try:
                collection = vector_store.get_collection(repo_url)
                if collection is None or collection.count() == 0:
                    logger.warning(f"Collection for {repo_url} does not exist or is empty. Skipping RAG.")
                    return {
                        **state,
                        "retrieved_context": None,
                        "repo_url": repo_url,
                        "stages_completed": state.get("stages_completed", [])
                    }
            except Exception as e:
                logger.warning(f"Could not check collection existence: {e}. Skipping RAG.")
                return {
                    **state,
                    "retrieved_context": None,
                    "repo_url": repo_url,
                    "stages_completed": state.get("stages_completed", [])
                }
            
            # Run the retriever agent
            retrieved_context = self.retriever.run(brd_model, repo_url=repo_url)
            
            # Update state
            stages = state.get("stages_completed", [])
            stages.append("context_retrieval")
            
            logger.info(f"Retrieved {len(retrieved_context)} chunks from {repo_url}")
            
            return {
                **state,
                "retrieved_context": retrieved_context,
                "repo_url": repo_url,
                "stages_completed": stages
            }
            
        except Exception as e:
            # Don't fail the workflow if retrieval fails - graceful degradation
            logger.warning(f"Retriever node failed (continuing without RAG): {e}")
            return {
                **state,
                "retrieved_context": None,
                "repo_url": state.get("repo_url"),
                "stages_completed": state.get("stages_completed", [])
            }
    
    def _planner_node(self, state: AgentState) -> AgentState:
        """Planner node - generates engineering plan."""
        logger.info("Workflow: Running Planner node")
        
        # Skip if previous stage failed
        if state.get("status") == "error":
            return state
        
        try:
            parsed_brd = state.get("parsed_brd", {})
            
            # Convert dict to format expected by planner
            # The planner expects a ParsedBRD model, but we'll pass the dict
            # and let it work with the raw data
            from ..models.brd import ParsedBRD
            
            # Try to create ParsedBRD from the normalized data
            # If it fails, create a minimal one
            try:
                brd_model = self._dict_to_parsed_brd(parsed_brd)
            except Exception:
                # Create minimal ParsedBRD from the data
                brd_model = ParsedBRD(
                    document_info={"title": parsed_brd.get("project", {}).get("name", "Unknown Project")},
                    executive_summary=parsed_brd.get("project", {}).get("description", ""),
                )
            
            # Get retrieved context from state (from RetrieverAgent)
            retrieved_context = state.get("retrieved_context")
            
            # Run the planner agent with retrieved context
            engineering_plan = self.planner.run(
                brd_model, 
                retrieved_context=retrieved_context
            )
            
            # Update state
            stages = state.get("stages_completed", [])
            stages.append("engineering_plan")
            
            return {
                **state,
                "engineering_plan": engineering_plan.model_dump(),
                "stages_completed": stages
            }
            
        except Exception as e:
            logger.error(f"Planner node failed: {e}")
            errors = state.get("errors", [])
            errors.append(f"Planner error: {str(e)}")
            return {
                **state,
                "errors": errors,
                "status": "error",
                "message": f"Engineering plan generation failed: {str(e)}"
            }
    
    def _scheduler_node(self, state: AgentState) -> AgentState:
        """Scheduler node - generates project schedule."""
        logger.info("Workflow: Running Scheduler node")
        
        # Skip if previous stage failed
        if state.get("status") == "error":
            return state
        
        try:
            engineering_plan_data = state.get("engineering_plan", {})
            
            # Convert dict to EngineeringPlan model
            from ..models.plan import EngineeringPlan
            
            engineering_plan = EngineeringPlan.model_validate(engineering_plan_data)
            
            # Run the scheduler agent
            project_schedule = self.scheduler.run(engineering_plan)
            
            # Update state
            stages = state.get("stages_completed", [])
            stages.append("project_schedule")
            
            return {
                **state,
                "project_schedule": project_schedule.model_dump(),
                "stages_completed": stages
            }
            
        except Exception as e:
            logger.error(f"Scheduler node failed: {e}")
            errors = state.get("errors", [])
            errors.append(f"Scheduler error: {str(e)}")
            return {
                **state,
                "errors": errors,
                "status": "error",
                "message": f"Project schedule generation failed: {str(e)}"
            }
    
    def _finalize_node(self, state: AgentState) -> AgentState:
        """Finalize node - prepare final output."""
        logger.info("Workflow: Running Finalize node")
        
        # If no error status set, mark as success
        if state.get("status") != "error":
            return {
                **state,
                "status": "success",
                "message": "BRD processed successfully through entire pipeline",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # If error, just add timestamp
        return {
            **state,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _dict_to_parsed_brd(self, data: dict):
        """Convert normalized dict to ParsedBRD model."""
        from ..models.brd import ParsedBRD, DocumentInfo, BusinessObjective, ProjectScope, Requirements, FunctionalRequirement
        
        project = data.get("project", {})
        features = data.get("features", [])
        
        # Build objectives
        objectives = []
        for i, obj in enumerate(project.get("objectives", [])):
            objectives.append(BusinessObjective(
                id=f"BO-{i+1:02d}",
                objective=obj,
                priority="Should"
            ))
        
        # Build functional requirements from features
        functional = []
        for feature in features:
            functional.append(FunctionalRequirement(
                id=feature.get("id", f"FR-{len(functional)+1:02d}"),
                description=f"{feature.get('name', '')}: {feature.get('description', '')}",
                priority=feature.get("priority", "Medium")
            ))
        
        return ParsedBRD(
            document_info=DocumentInfo(
                title=project.get("name", "Unknown Project"),
                version="1.0",
                status="Draft"
            ),
            executive_summary=project.get("description", ""),
            business_objectives=objectives,
            project_scope=ProjectScope(
                in_scope=[f.get("name", "") for f in features],
                out_of_scope=[]
            ),
            stakeholders=[],
            requirements=Requirements(
                functional=functional,
                non_functional=[]
            )
        )
    
    def run(self, input_data: dict) -> dict:
        """
        Run the full BRD processing pipeline.
        
        Args:
            input_data: BRD input (raw JSON or PDF data)
            
        Returns:
            Final state with all outputs
        """
        logger.info("Starting BRD workflow")
        
        # Prepare initial state
        initial_state: AgentState = {
            "raw_input": input_data,
            "is_pdf": "pdf_file" in input_data,
            "stages_completed": [],
            "errors": []
        }
        
        # Run the graph
        final_state = self.graph.invoke(initial_state)
        
        logger.info(f"Workflow completed with status: {final_state.get('status', 'unknown')}")
        
        return final_state


def create_workflow(llm_service: Optional[LLMService] = None) -> BRDWorkflow:
    """
    Factory function to create a BRD workflow instance.
    
    Args:
        llm_service: Optional LLM service to use
        
    Returns:
        Configured BRDWorkflow instance
    """
    return BRDWorkflow(llm_service=llm_service)

