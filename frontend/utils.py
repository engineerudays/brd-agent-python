"""
Utility functions for BRD Agent UI
Ported from: brd_agent_em/frontend/utils.py
"""
import json
import time
import requests
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple


def submit_brd_to_orchestrator(brd_data: Dict[str, Any], orchestrator_url: str, max_retries: int = 3) -> Dict[str, Any]:
    """
    Submit BRD to the orchestrator API with retry logic.
    
    Args:
        brd_data: BRD data as dictionary
        orchestrator_url: Orchestrator endpoint URL
        max_retries: Maximum number of retry attempts (default: 3)
        
    Returns:
        Response from orchestrator
    """
    for attempt in range(max_retries):
        try:
            response = requests.post(
                orchestrator_url,
                json=brd_data,
                headers={"Content-Type": "application/json"},
                timeout=180  # 3 minutes timeout
            )
            response.raise_for_status()
            
            # Check if response has content
            if not response.content:
                return {
                    "success": False,
                    "error": "Empty response from orchestrator. Check if the backend is running.",
                    "status_code": response.status_code,
                    "debug_info": f"URL: {orchestrator_url}",
                    "attempts": attempt + 1
                }
            
            # Try to parse JSON
            try:
                json_data = response.json()
                return {
                    "success": True,
                    "data": json_data,
                    "status_code": response.status_code,
                    "attempts": attempt + 1
                }
            except json.JSONDecodeError as je:
                # JSON decode errors are not retryable
                return {
                    "success": False,
                    "error": f"Invalid JSON response: {str(je)}",
                    "status_code": response.status_code,
                    "debug_info": f"Response preview: {response.text[:500]}",
                    "attempts": attempt + 1
                }
                
        except requests.exceptions.Timeout:
            # Timeout - retry with exponential backoff
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) * 2  # 2s, 4s, 8s
                time.sleep(wait_time)
                continue
            return {
                "success": False,
                "error": f"Request timed out after {max_retries} attempts. The orchestrator may be overloaded or slow.",
                "status_code": 0,
                "attempts": max_retries
            }
            
        except requests.exceptions.ConnectionError as ce:
            # Connection error - retry with exponential backoff
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) * 2  # 2s, 4s, 8s
                time.sleep(wait_time)
                continue
            return {
                "success": False,
                "error": f"Connection failed after {max_retries} attempts: {str(ce)}",
                "status_code": 0,
                "attempts": max_retries
            }
            
        except requests.exceptions.HTTPError as he:
            # HTTP errors (4xx, 5xx)
            status_code = he.response.status_code if hasattr(he, 'response') else 0
            
            # Retry on 5xx server errors, but not 4xx client errors
            if status_code >= 500 and attempt < max_retries - 1:
                wait_time = (2 ** attempt) * 2  # 2s, 4s, 8s
                time.sleep(wait_time)
                continue
            
            error_msg = str(he)
            debug_info = ""
            if hasattr(he, 'response') and he.response is not None:
                try:
                    debug_info = f"Response: {he.response.text[:500]}"
                except:
                    debug_info = "Could not read response text"
            
            return {
                "success": False,
                "error": error_msg,
                "status_code": status_code,
                "debug_info": debug_info,
                "attempts": attempt + 1
            }
            
        except requests.exceptions.RequestException as e:
            # Other request errors - retry
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) * 2  # 2s, 4s, 8s
                time.sleep(wait_time)
                continue
            
            error_msg = str(e)
            debug_info = ""
            if hasattr(e, 'response') and e.response is not None:
                try:
                    debug_info = f"Response: {e.response.text[:500]}"
                except:
                    debug_info = "Could not read response text"
            
            return {
                "success": False,
                "error": error_msg,
                "status_code": getattr(e.response, 'status_code', 0) if hasattr(e, 'response') else 0,
                "debug_info": debug_info,
                "attempts": max_retries
            }
    
    # Should never reach here, but just in case
    return {
        "success": False,
        "error": "Unexpected error in retry logic",
        "status_code": 0,
        "attempts": max_retries
    }


def validate_brd_json(brd_text: str) -> Tuple[bool, Optional[Dict], Optional[str]]:
    """
    Validate BRD JSON format.
    Accepts multiple formats:
    1. Direct BRD: {project: {...}, features: [...]}
    2. Parser format: {raw_brd_text: "..."}
    3. Wrapped format: {brd_data: {...}}
    
    Returns:
        (is_valid, parsed_json, error_message)
    """
    try:
        data = json.loads(brd_text)
        
        # Basic validation
        if not isinstance(data, dict):
            return False, None, "BRD must be a JSON object"
        
        # Accept multiple BRD formats
        # Format 1: Direct BRD with project/features
        if "project" in data or "features" in data:
            return True, data, None
        
        # Format 2: Parser format with raw_brd_text
        if "raw_brd_text" in data:
            return True, data, None
        
        # Format 3: Wrapped in brd_data
        if "brd_data" in data:
            return True, data, None
        
        # Format 4: Full ParsedBRD format (from our models)
        if "document_info" in data:
            return True, data, None
        
        # If none of the expected formats, show helpful error
        return False, None, "BRD must contain one of: 'project', 'features', 'raw_brd_text', 'brd_data', or 'document_info'"
            
    except json.JSONDecodeError as e:
        return False, None, f"Invalid JSON: {str(e)}"


def create_gantt_chart(schedule_data: Dict[str, Any]) -> Optional[go.Figure]:
    """
    Create a Gantt chart from project schedule data.
    
    Args:
        schedule_data: Project schedule with phases and tasks
        
    Returns:
        Plotly figure or None if data is invalid
    """
    try:
        # Handle different nesting levels of schedule data
        if "project_schedule" in schedule_data:
            project_schedule = schedule_data["project_schedule"]
        else:
            project_schedule = schedule_data
        
        # Extract phases - might be directly in the object or nested
        phases = project_schedule.get("phases", [])
        
        if not phases or len(phases) == 0:
            print(f"No phases found. Available keys: {project_schedule.keys() if isinstance(project_schedule, dict) else 'not a dict'}")
            return None
            
        # Prepare data for Gantt chart
        tasks = []
        
        for phase in phases:
            phase_name = phase.get("phase_name", "Unnamed Phase")
            start_date = phase.get("start_date", "2025-01-01")
            end_date = phase.get("end_date", "2025-01-01")
            
            # Add phase as a task
            tasks.append({
                "Task": phase_name,
                "Start": start_date,
                "Finish": end_date,
                "Type": "Phase"
            })
            
            # Add milestones
            for milestone in phase.get("milestones", []):
                milestone_name = milestone.get("name", "Unnamed Milestone")
                target_date = milestone.get("target_date", start_date)
                
                tasks.append({
                    "Task": f"  📍 {milestone_name}",
                    "Start": target_date,
                    "Finish": target_date,
                    "Type": "Milestone"
                })
        
        if not tasks:
            return None
            
        # Create DataFrame
        df = pd.DataFrame(tasks)
        
        # Create Gantt chart
        fig = px.timeline(
            df,
            x_start="Start",
            x_end="Finish",
            y="Task",
            color="Type",
            title="Project Timeline",
            color_discrete_map={"Phase": "#0066cc", "Milestone": "#28a745"}
        )
        
        fig.update_layout(
            xaxis_title="Timeline",
            yaxis_title="Tasks",
            height=400 + len(tasks) * 30,  # Dynamic height
            showlegend=True,
            hovermode="closest"
        )
        
        return fig
        
    except Exception as e:
        print(f"Error creating Gantt chart: {e}")
        return None


def format_duration(weeks: int) -> str:
    """Format duration in weeks to human-readable format."""
    if weeks < 4:
        return f"{weeks} weeks"
    elif weeks < 52:
        months = round(weeks / 4.33, 1)
        return f"{months} months"
    else:
        years = round(weeks / 52, 1)
        return f"{years} years"


def extract_project_summary(response_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract key metrics from orchestrator response for summary display.
    
    Returns:
        Dictionary with summary metrics
    """
    summary = {
        "status": "Unknown",
        "stages_completed": [],
        "timestamp": None
    }
    
    try:
        summary["status"] = response_data.get("status", "Unknown")
        summary["stages_completed"] = response_data.get("stages_completed", [])
        summary["timestamp"] = response_data.get("timestamp")
        
        return summary
        
    except Exception as e:
        print(f"Error extracting summary: {e}")
        return summary


def get_sample_brds() -> Dict[str, str]:
    """
    Get available sample BRDs.
    
    Returns:
        Dictionary mapping BRD name to file path
    """
    from pathlib import Path
    
    samples = {}
    sample_dir = Path(__file__).parent / "sample_brds"
    
    if sample_dir.exists():
        for file_path in sample_dir.glob("*.json"):
            samples[file_path.stem.replace("_", " ").title()] = str(file_path)
    
    return samples


def load_sample_brd(file_path: str) -> Optional[str]:
    """Load a sample BRD file."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            return json.dumps(data, indent=2)
    except Exception as e:
        print(f"Error loading sample BRD: {e}")
        return None


def display_engineering_plan(plan_data: Dict[str, Any]) -> None:
    """Display engineering plan in a structured, human-readable format."""
    import streamlit as st
    
    if not plan_data:
        st.warning("No engineering plan data available.")
        return
    
    # Extract the plan (might be nested)
    plan = plan_data.get('engineering_plan', plan_data)
    
    if not plan:
        st.warning("Engineering plan is empty.")
        return
    
    # Project Overview
    if plan.get('project_overview'):
        with st.expander("📋 Project Overview", expanded=True):
            overview = plan['project_overview']
            st.markdown(f"**Project Name:** {overview.get('name', 'N/A')}")
            st.markdown(f"**Description:** {overview.get('description', 'N/A')}")
            if overview.get('objectives'):
                st.markdown("**Objectives:**")
                for obj in overview['objectives']:
                    st.markdown(f"- {obj}")
    
    # Feature Breakdown
    if plan.get('feature_breakdown'):
        with st.expander(f"🎯 Feature Breakdown ({len(plan['feature_breakdown'])} features)"):
            for feature in plan['feature_breakdown']:
                st.markdown(f"### {feature.get('feature_id', 'N/A')}: {feature.get('feature_name', 'Unnamed')}")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Priority", feature.get('priority', 'N/A'))
                with col2:
                    st.metric("Complexity", feature.get('complexity', 'N/A'))
                with col3:
                    st.metric("Effort", feature.get('estimated_effort', 'N/A'))
                
                st.markdown(f"**Description:** {feature.get('description', 'N/A')}")
                
                if feature.get('technical_requirements'):
                    st.markdown("**Technical Requirements:**")
                    for req in feature['technical_requirements']:
                        st.markdown(f"- {req}")
                
                st.divider()
    
    # Technical Architecture
    if plan.get('technical_architecture'):
        with st.expander("🏗️ Technical Architecture"):
            arch = plan['technical_architecture']
            if arch.get('system_components'):
                st.markdown("**System Components:**")
                for comp in arch['system_components']:
                    st.markdown(f"- {comp}")
            if arch.get('integration_points'):
                st.markdown("**Integration Points:**")
                for integration in arch['integration_points']:
                    st.markdown(f"- {integration}")
            if arch.get('data_flow'):
                st.markdown(f"**Data Flow:** {arch['data_flow']}")
    
    # Implementation Phases
    if plan.get('implementation_phases'):
        with st.expander(f"📅 Implementation Phases ({len(plan['implementation_phases'])} phases)"):
            for phase in plan['implementation_phases']:
                st.markdown(f"### Phase {phase.get('phase_number', 'N/A')}: {phase.get('phase_name', 'Unnamed')}")
                st.markdown(f"**Duration:** {phase.get('estimated_duration', 'N/A')}")
                st.markdown(f"**Description:** {phase.get('description', 'N/A')}")
                if phase.get('features_included'):
                    st.markdown("**Features:**")
                    for feat in phase['features_included']:
                        st.markdown(f"- {feat}")
                st.divider()
    
    # Risk Analysis
    if plan.get('risk_analysis'):
        with st.expander(f"⚠️ Risk Analysis ({len(plan['risk_analysis'])} risks)"):
            for risk in plan['risk_analysis']:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{risk.get('risk_id', 'N/A')}:** {risk.get('description', 'N/A')}")
                with col2:
                    impact = risk.get('impact', 'N/A')
                    color = "🔴" if impact == "High" else "🟡" if impact == "Medium" else "🟢"
                    st.markdown(f"{color} Impact: {impact}")
                st.markdown(f"*Mitigation:* {risk.get('mitigation_strategy', 'N/A')}")
                st.divider()
    
    # Resource Requirements
    if plan.get('resource_requirements'):
        with st.expander("👥 Resource Requirements"):
            resources = plan['resource_requirements']
            if resources.get('team_composition'):
                st.markdown("**Team:**")
                for member in resources['team_composition']:
                    st.markdown(f"- {member}")
            if resources.get('tools_and_technologies'):
                st.markdown("**Technologies:**")
                st.markdown(", ".join(resources['tools_and_technologies']))
    
    # Success Metrics
    if plan.get('success_metrics'):
        with st.expander(f"📊 Success Metrics ({len(plan['success_metrics'])} metrics)"):
            for metric in plan['success_metrics']:
                st.markdown(f"**{metric.get('metric_name', 'Unnamed')}**")
                st.markdown(f"- Target: {metric.get('target_value', 'N/A')}")
                st.markdown(f"- Measurement: {metric.get('measurement_method', 'N/A')}")
                st.divider()


def display_project_schedule(schedule_data: Dict[str, Any]) -> None:
    """Display project schedule in a structured, human-readable format."""
    import streamlit as st
    
    if not schedule_data:
        st.warning("No project schedule data available.")
        return
    
    # Extract the schedule (might be nested)
    schedule = schedule_data.get('project_schedule', schedule_data)
    
    if not schedule:
        st.warning("Project schedule is empty.")
        return
    
    # Project Info
    if schedule.get('project_info'):
        with st.expander("ℹ️ Project Information", expanded=True):
            info = schedule['project_info']
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Start Date", info.get('start_date', 'N/A'))
            with col2:
                st.metric("End Date", info.get('estimated_end_date', info.get('end_date', 'N/A')))
            with col3:
                duration = info.get('total_duration_weeks', 0)
                st.metric("Duration", f"{duration} weeks")
    
    # Phases and Tasks
    if schedule.get('phases'):
        with st.expander(f"📅 Project Phases ({len(schedule['phases'])} phases)", expanded=True):
            for phase in schedule['phases']:
                st.markdown(f"### {phase.get('phase_name', 'Unnamed Phase')}")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"**Start:** {phase.get('start_date', 'N/A')}")
                with col2:
                    st.markdown(f"**End:** {phase.get('end_date', 'N/A')}")
                with col3:
                    st.markdown(f"**Duration:** {phase.get('duration_weeks', 'N/A')} weeks")
                
                # Milestones
                if phase.get('milestones'):
                    st.markdown("**Milestones:**")
                    for milestone in phase['milestones']:
                        st.markdown(f"- 📍 {milestone.get('name', 'Unnamed')} ({milestone.get('target_date', 'TBD')})")
                
                st.divider()
    
    # Resource Allocation
    if schedule.get('resource_allocation'):
        with st.expander("👥 Resource Allocation"):
            resources = schedule['resource_allocation']
            # Handle both dict and list formats
            if isinstance(resources, dict):
                if resources.get('team_assignments'):
                    for assignment in resources['team_assignments']:
                        st.markdown(f"**{assignment.get('role', 'N/A')}:** {assignment.get('allocation', 'N/A')}")
            elif isinstance(resources, list):
                for item in resources:
                    if isinstance(item, dict):
                        role = item.get('role', item.get('name', 'N/A'))
                        allocation = item.get('allocation', item.get('allocation_percentage', 'N/A'))
                        st.markdown(f"**{role}:** {allocation}")
                    else:
                        st.markdown(f"- {item}")
    
    # Critical Path
    if schedule.get('critical_path'):
        with st.expander("🎯 Critical Path"):
            critical = schedule['critical_path']
            # Handle both dict and list formats
            if isinstance(critical, dict):
                if critical.get('tasks'):
                    st.markdown("**Critical Tasks:**")
                    for task in critical['tasks']:
                        st.markdown(f"- {task}")
                elif critical.get('description'):
                    st.markdown(critical['description'])
            elif isinstance(critical, list):
                st.markdown("**Critical Tasks:**")
                for task in critical:
                    if isinstance(task, dict):
                        st.markdown(f"- {task.get('task_name', task.get('task_id', 'Unknown'))}")
                    else:
                        st.markdown(f"- {task}")
    
    # Assumptions & Constraints
    col1, col2 = st.columns(2)
    with col1:
        if schedule.get('assumptions'):
            assumptions = schedule['assumptions']
            if isinstance(assumptions, list) and len(assumptions) > 0:
                with st.expander(f"💡 Assumptions ({len(assumptions)})"):
                    for assumption in assumptions:
                        st.markdown(f"- {assumption}")
    
    with col2:
        if schedule.get('constraints'):
            constraints = schedule['constraints']
            if isinstance(constraints, list) and len(constraints) > 0:
                with st.expander(f"⚠️ Constraints ({len(constraints)})"):
                    for constraint in constraints:
                        st.markdown(f"- {constraint}")

