"""
BRD Agent - Streamlit UI
Multi-Agent Engineering Manager Interface

Ported from: brd_agent_em/frontend/app.py
Updated to work with Python FastAPI backend
"""
import streamlit as st
import json
import base64
from pathlib import Path
import sys

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from frontend import config, utils

# Page configuration
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon=config.APP_ICON,
    layout=config.PAGE_LAYOUT,
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #0066cc;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
        border-left: 4px solid #0066cc;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)


def render_header():
    """Render the main header"""
    st.markdown('<div class="main-header">🤖 BRD Agent - Engineering Manager</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Transform Business Requirements into Engineering Artifacts with AI</div>', unsafe_allow_html=True)
    st.divider()


def render_sidebar():
    """Render the sidebar with configuration and help"""
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Orchestrator URL
        orchestrator_url = st.text_input(
            "Orchestrator URL",
            value=config.ORCHESTRATOR_URL,
            help="Python FastAPI backend endpoint"
        )
        
        st.divider()
        
        # Quick stats
        st.header("📊 Quick Stats")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Agents", "3")
        with col2:
            st.metric("Outputs", "2")
        
        st.caption("✅ Engineering Plan")
        st.caption("✅ Project Schedule")
        st.caption("🚧 Architecture (Coming Soon)")
        
        st.divider()
        
        # Help section
        st.header("❓ Help")
        with st.expander("How to Use"):
            st.markdown("""
            1. **Upload or paste** your BRD in JSON format
            2. **Click Process** to submit to the orchestrator
            3. **View results** with visual timeline
            4. **Download** generated artifacts
            
            **Required BRD Structure:**
            ```json
            {
              "project": {
                "name": "...",
                "description": "...",
                "objectives": [...]
              },
              "features": [...]
            }
            ```
            """)
        
        with st.expander("Sample Templates"):
            st.markdown("""
            Use the **Load Sample** option to load
            pre-configured templates for testing.
            """)
        
        st.divider()
        
        # Backend status indicator
        st.header("🔌 Backend Status")
        st.caption(f"URL: {orchestrator_url}")
        st.info("💡 Make sure the FastAPI backend is running:\n`uvicorn api.main:app --reload`")
        
        return orchestrator_url


def render_input_tab():
    """Render the BRD input tab"""
    st.header("📝 BRD Input")
    
    # Input method selection
    input_method = st.radio(
        "Input Method",
        ["Upload PDF File", "Upload JSON File", "Paste JSON", "Load Sample"],
        horizontal=True,
        help="Choose how to provide your Business Requirements Document"
    )
    
    brd_text = None
    brd_data = None
    is_pdf = False
    
    if input_method == "Upload PDF File":
        uploaded_file = st.file_uploader(
            "Upload BRD PDF file",
            type=["pdf"],
            help="Upload a Business Requirements Document in PDF format - it will be parsed automatically"
        )
        
        if uploaded_file:
            # Read PDF and convert to base64
            pdf_bytes = uploaded_file.read()
            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
            
            # Store as BRD data with pdf_file field
            brd_data = {
                "pdf_file": pdf_base64,
                "filename": uploaded_file.name
            }
            is_pdf = True
            
            st.success(f"✅ PDF Loaded: {uploaded_file.name} ({len(pdf_bytes) / 1024:.1f} KB)")
            st.info("📄 PDF will be parsed automatically by the backend")
            st.toast(f"✅ PDF loaded: {uploaded_file.name}", icon="📄")
            
    elif input_method == "Upload JSON File":
        uploaded_file = st.file_uploader(
            "Upload BRD JSON file",
            type=["json"],
            help="Upload a Business Requirements Document in JSON format"
        )
        
        if uploaded_file:
            brd_text = uploaded_file.read().decode("utf-8")
            st.success(f"✅ Loaded: {uploaded_file.name}")
            
    elif input_method == "Paste JSON":
        brd_text = st.text_area(
            "Paste BRD JSON",
            height=300,
            placeholder='{\n  "project": {\n    "name": "Your Project",\n    ...\n  }\n}',
            help="Paste your BRD in JSON format"
        )
        
    else:  # Load Sample
        # Try to load sample from project's sample_inputs
        sample_path = project_root / "sample_inputs" / "brds" / "brd_input_cleaner.json"
        
        if sample_path.exists():
            with open(sample_path, 'r') as f:
                sample_data = json.load(f)
                brd_text = json.dumps(sample_data, indent=2)
                
            st.info("📋 Sample BRD loaded from sample_inputs/brds/")
        else:
            st.warning("Sample BRD not found at sample_inputs/brds/brd_input_cleaner.json. Please use Upload or Paste method.")
    
    # Handle PDF upload (already validated)
    if is_pdf and brd_data:
        st.session_state['brd_data'] = brd_data
        st.session_state['is_pdf'] = True
        return True
    
    # Display and validate JSON BRD
    if brd_text:
        st.subheader("BRD Preview")
        
        # Validate
        is_valid, parsed_data, error = utils.validate_brd_json(brd_text)
        
        if is_valid:
            st.success("✅ Valid BRD JSON")
            st.toast("✅ BRD validated successfully", icon="✅")
            
            # Show preview
            with st.expander("View BRD Details", expanded=False):
                st.json(parsed_data)
            
            # Store in session state
            st.session_state['brd_data'] = parsed_data
            st.session_state['brd_text'] = brd_text
            st.session_state['is_pdf'] = False
            
            return True
        else:
            st.error(f"❌ Invalid BRD: {error}")
            st.code(brd_text, language="json")
            return False
    
    return False


def render_processing_section(orchestrator_url: str):
    """Render the processing section with submit button"""
    if 'brd_data' not in st.session_state:
        st.info("👆 Please provide a BRD in the input section above")
        return
    
    st.header("🚀 Process BRD")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.write("Ready to generate engineering artifacts from your BRD")
    
    with col2:
        if st.button("🚀 Process BRD", type="primary", use_container_width=True):
            process_brd(orchestrator_url)
    
    with col3:
        if st.button("🗑️ Clear", use_container_width=True):
            clear_session()


def process_brd(orchestrator_url: str):
    """Process the BRD through the orchestrator"""
    # Prevent duplicate processing
    if st.session_state.get('is_processing', False):
        st.warning("⏳ Processing already in progress...")
        st.toast("⏳ Already processing...", icon="⚠️")
        return
    
    st.session_state['is_processing'] = True
    st.toast("🚀 Starting BRD processing...", icon="⚙️")
    
    with st.spinner("⏳ Processing BRD through multi-agent pipeline..."):
        result = utils.submit_brd_to_orchestrator(
            st.session_state['brd_data'],
            orchestrator_url
        )
        
        st.session_state['is_processing'] = False
        
        if result['success']:
            st.session_state['result'] = result['data']
            st.session_state['processing_complete'] = True
            
            # Show success message with retry info if applicable
            success_msg = "✅ BRD processed successfully! Check the 'Results' and 'Timeline' tabs."
            toast_msg = "✅ Processing complete!"
            if result.get('attempts', 1) > 1:
                success_msg += f" (Completed after {result['attempts']} attempts)"
                toast_msg += f" ({result['attempts']} attempts)"
            
            st.success(success_msg)
            st.toast(toast_msg, icon="🎉")
        else:
            error_msg = result.get('error', 'Unknown error')
            st.error(f"❌ Processing failed: {error_msg}")
            st.toast(f"❌ Processing failed: {error_msg[:50]}...", icon="🚨")
            
            if result.get('attempts'):
                st.caption(f"Attempts made: {result['attempts']}")
            if result.get('status_code'):
                st.caption(f"HTTP Status Code: {result['status_code']}")
            if result.get('debug_info'):
                with st.expander("🔍 Debug Information"):
                    st.text(result['debug_info'])


def render_results_tab():
    """Render the results tab with outputs"""
    if 'result' not in st.session_state:
        st.info("No results yet. Process a BRD to see outputs here.")
        return
    
    result = st.session_state['result']
    
    # Summary
    st.header("📊 Processing Summary")
    summary = utils.extract_project_summary(result)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        status = summary['status']
        status_icon = "✅" if status == "success" else "❌"
        st.metric("Status", f"{status_icon} {status.title()}")
    
    with col2:
        stages = len(summary.get('stages_completed', []))
        st.metric("Stages Completed", stages)
    
    with col3:
        if summary.get('timestamp'):
            st.metric("Completed At", summary['timestamp'][:19])
    
    # Stages completed
    if summary.get('stages_completed'):
        st.write("**Completed Stages:**")
        cols = st.columns(len(summary['stages_completed']))
        for idx, stage in enumerate(summary['stages_completed']):
            with cols[idx]:
                st.success(f"✓ {stage.replace('_', ' ').title()}")
    
    st.divider()
    
    # Engineering Plan Section
    if result.get('engineering_plan'):
        st.header("🎯 Engineering Plan")
        utils.display_engineering_plan(result['engineering_plan'])
        
        # Download button for engineering plan
        st.download_button(
            label="💾 Download Engineering Plan",
            data=json.dumps(result['engineering_plan'], indent=2),
            file_name=f"engineering_plan_{summary.get('timestamp', 'unknown')[:10]}.json",
            mime="application/json"
        )
        st.divider()
    
    # Project Schedule Section
    if result.get('project_schedule'):
        st.header("📅 Project Schedule")
        utils.display_project_schedule(result['project_schedule'])
        
        # Download button for project schedule
        st.download_button(
            label="💾 Download Project Schedule",
            data=json.dumps(result['project_schedule'], indent=2),
            file_name=f"project_schedule_{summary.get('timestamp', 'unknown')[:10]}.json",
            mime="application/json"
        )
        st.divider()
    
    # Show full response (collapsed by default)
    with st.expander("📄 View Full JSON Response"):
        st.json(result)
    
    # Download button for full response
    st.download_button(
        label="💾 Download Full Response (JSON)",
        data=json.dumps(result, indent=2),
        file_name=f"brd_processing_result_{summary.get('timestamp', 'unknown')[:10]}.json",
        mime="application/json"
    )


def render_timeline_tab():
    """Render the timeline/Gantt chart tab"""
    if 'result' not in st.session_state:
        st.info("No timeline data yet. Process a BRD to see the project timeline here.")
        return
    
    st.header("📅 Project Timeline")
    
    result = st.session_state['result']
    
    # Check if we have project schedule data
    if not result.get('project_schedule'):
        st.warning("No project schedule data available in the response.")
        with st.expander("ℹ️ Troubleshooting"):
            st.markdown("""
            If you don't see the timeline here:
            1. Check the 'Results' tab for the project schedule data
            2. Ensure the backend processed the BRD successfully
            3. Check the backend logs for any errors
            """)
        return
    
    # Create and display Gantt chart
    gantt_fig = utils.create_gantt_chart(result['project_schedule'])
    
    if gantt_fig:
        st.plotly_chart(gantt_fig, use_container_width=True)
        st.success("✅ Interactive timeline generated successfully")
    else:
        st.warning("Could not generate Gantt chart. The schedule data might be incomplete.")
        
        # Debug info
        with st.expander("🔍 Debug: Schedule Data Structure"):
            schedule = result['project_schedule']
            st.write("**Available keys:**")
            if isinstance(schedule, dict):
                st.json(list(schedule.keys()))
                if 'project_schedule' in schedule:
                    st.write("**Nested project_schedule keys:**")
                    st.json(list(schedule['project_schedule'].keys()) if isinstance(schedule['project_schedule'], dict) else "Not a dict")
                    if isinstance(schedule['project_schedule'], dict) and 'phases' in schedule['project_schedule']:
                        st.write(f"**Number of phases:** {len(schedule['project_schedule']['phases'])}")
            else:
                st.write("Schedule is not a dictionary")
    
    st.divider()
    
    # Show schedule summary
    schedule = result['project_schedule'].get('project_schedule', result['project_schedule'])
    if schedule.get('project_info'):
        st.subheader("📊 Schedule Overview")
        info = schedule['project_info']
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Start Date", info.get('start_date', 'N/A'))
        with col2:
            st.metric("End Date", info.get('estimated_end_date', info.get('end_date', 'N/A')))
        with col3:
            st.metric("Total Duration", f"{info.get('total_duration_weeks', 0)} weeks")
        with col4:
            phases_count = len(schedule.get('phases', []))
            st.metric("Phases", phases_count)
    
    note_message = result.get("note", "")
    if note_message:
        st.caption(f"💡 {note_message}")


def clear_session():
    """Clear session state"""
    keys_to_clear = ['brd_data', 'brd_text', 'result', 'processing_complete', 'is_processing', 'is_pdf']
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    st.toast("🗑️ Workspace cleared", icon="🧹")
    st.rerun()


def main():
    """Main application entry point"""
    # Initialize session state
    if 'processing_complete' not in st.session_state:
        st.session_state['processing_complete'] = False
    if 'is_processing' not in st.session_state:
        st.session_state['is_processing'] = False
    
    # Render header
    render_header()
    
    # Render sidebar and get config
    orchestrator_url = render_sidebar()
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs(["📝 Input & Process", "📊 Results", "📅 Timeline"])
    
    with tab1:
        brd_valid = render_input_tab()
        if brd_valid:
            st.divider()
            render_processing_section(orchestrator_url)
    
    with tab2:
        render_results_tab()
    
    with tab3:
        render_timeline_tab()
    
    # Footer
    st.divider()
    st.caption("🤖 BRD Agent v2.0 (Python) | Built with Streamlit, LangGraph & Anthropic Claude")


if __name__ == "__main__":
    main()

