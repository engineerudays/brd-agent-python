# 🔌 BRD Agent Python - API Reference

**Technical Documentation for Developers**

Version: 1.0  
Last Updated: December 2025

---

## 📋 Table of Contents

1. [System Architecture](#system-architecture)
2. [API Endpoints](#api-endpoints)
3. [Data Schemas](#data-schemas)
4. [LangGraph Workflow](#langgraph-workflow)
5. [Error Handling](#error-handling)
6. [Performance & Scalability](#performance--scalability)
7. [Security](#security)
8. [Extension Guide](#extension-guide)

---

## 🏗️ System Architecture

### Overview

The BRD Agent uses a **multi-agent architecture** orchestrated by LangGraph with a FastAPI backend and Streamlit frontend.

```
┌─────────────────┐
│  Streamlit UI   │ (Port 8501)
│  (Frontend)     │
└────────┬────────┘
         │ HTTP POST
         ↓
┌─────────────────┐
│ FastAPI Backend │ (Port 8000)
│  Orchestrator   │
└────────┬────────┘
         │
         ↓
┌─────────────────────────────────────────┐
│           LangGraph Workflow            │
├─────────────┬─────────────┬─────────────┤
│   Parser    │   Planner   │  Scheduler  │
│   Agent     │   Agent     │   Agent     │
└─────────────┴──────┬──────┴─────────────┘
                     │
               ┌─────┴─────┐
               │ Anthropic │
               │  Claude   │
               └───────────┘
```

### Components

| Component | Technology | Port | Purpose |
|-----------|-----------|------|---------|
| Frontend UI | Streamlit (Python) | 8501 | User interface |
| Backend API | FastAPI (Python) | 8000 | Pipeline orchestration |
| Parser Agent | LangGraph Node | - | Input normalization |
| Planner Agent | LangGraph Node | - | Engineering plan generation |
| Scheduler Agent | LangGraph Node | - | Project schedule creation |
| AI Engine | Anthropic Claude | External | Content generation |

### Data Flow

1. **Input**: User uploads BRD (PDF/JSON) via Streamlit UI
2. **Orchestration**: FastAPI receives request, invokes LangGraph
3. **Parsing**: Parser Agent normalizes BRD format
4. **Engineering Plan**: Planner Agent generates implementation plan via Claude
5. **Project Schedule**: Scheduler Agent creates timeline via Claude
6. **Response**: Artifacts returned to UI and saved to disk
7. **Display**: UI renders human-readable results + Gantt chart

---

## 🔗 API Endpoints

### 1. Health Check

**Endpoint**: `/health`

**Method**: `GET`

**Description**: Check backend health and LLM configuration status.

**Response**:
```json
{
  "status": "healthy",
  "llm_configured": true
}
```

---

### 2. Root

**Endpoint**: `/`

**Method**: `GET`

**Description**: API liveness check.

**Response**:
```json
{
  "message": "BRD Agent Python API",
  "version": "1.0.0",
  "docs": "/docs"
}
```

---

### 3. Process BRD (JSON)

**Endpoint**: `/api/process-brd`

**Method**: `POST`

**Description**: Main entry point for BRD processing. Orchestrates the entire LangGraph pipeline.

**Request**:
```json
{
  "project": {
    "name": "Project Name",
    "description": "Description"
  },
  "features": [
    {
      "id": "F001",
      "name": "Feature Name",
      "priority": "High"
    }
  ],
  "technical_requirements": {
    "platforms": ["Web"],
    "integrations": []
  }
}
```

**Response**:
```json
{
  "status": "success",
  "message": "BRD processed successfully through entire pipeline",
  "stages_completed": [
    "brd_parsing",
    "engineering_plan",
    "project_schedule"
  ],
  "timestamp": "2025-12-12T10:43:39.878Z",
  "note": "Generated files saved to sample_inputs/outputs/",
  "engineering_plan": {
    "project_overview": {...},
    "feature_breakdown": [...],
    "technical_architecture": {...},
    "implementation_phases": [...],
    "risk_analysis": [...],
    "resource_requirements": {...},
    "success_metrics": [...]
  },
  "project_schedule": {
    "project_info": {...},
    "phases": [...],
    "resource_allocation": [...],
    "critical_path": {...},
    "assumptions": [...],
    "constraints": [...]
  }
}
```

**Error Response**:
```json
{
  "status": "error",
  "message": "Error description",
  "timestamp": "2025-12-12T10:43:39.878Z"
}
```

**Status Codes**:
- `200`: Success
- `400`: Invalid request (bad BRD format)
- `500`: Server error (workflow failure)
- `504`: Timeout

---

### 4. Process BRD (File Upload)

**Endpoint**: `/api/process-brd/upload`

**Method**: `POST`

**Content-Type**: `multipart/form-data`

**Description**: Upload PDF or JSON file for processing.

**Request**:
```
file: <binary file data>
```

**Response**: Same as `/api/process-brd`

---

### 5. PDF Parser - Extract Text

**Endpoint**: `/api/pdf/extract-text`

**Method**: `POST`

**Content-Type**: `multipart/form-data`

**Description**: Extract raw text from PDF file.

**Request**:
```
file: <PDF binary>
```

**Response**:
```json
{
  "status": "success",
  "text": "Extracted text content...",
  "page_count": 10
}
```

---

### 6. PDF Parser - Parse to JSON

**Endpoint**: `/api/pdf/parse`

**Method**: `POST`

**Content-Type**: `multipart/form-data`

**Description**: Extract and parse PDF into structured BRD JSON using Claude.

**Request**:
```
file: <PDF binary>
```

**Response**:
```json
{
  "status": "success",
  "parsed_brd": {
    "document_info": {...},
    "executive_summary": "...",
    "business_objectives": [...],
    "project_scope": {...},
    "stakeholders": [...],
    "requirements": {
      "functional": [...],
      "non_functional": [...]
    },
    "constraints_assumptions_dependencies": {...}
  },
  "metadata": {
    "parsing_method": "pdf",
    "timestamp": "2025-12-12T10:43:39.878Z"
  }
}
```

---

## 🔍 Ingestion API Endpoints

The ingestion API provides endpoints for managing documentation in the vector store for RAG functionality.

### 7. Ingest Single Document

**Endpoint**: `/api/ingest/document`

**Method**: `POST`

**Description**: Ingest a single markdown document from a GitHub repository into the vector store.

**Request**:
```json
{
  "repo_url": "https://github.com/owner/repo",
  "file_path": "docs/architecture.md",
  "content": "Optional: Direct content (if not fetching from GitHub)"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Successfully ingested docs/architecture.md",
  "repo_url": "https://github.com/owner/repo",
  "collection_name": "repo_abc123",
  "files_processed": 1,
  "chunks_created": 15,
  "timestamp": "2025-12-12T10:43:39.878Z"
}
```

**Error Response**:
```json
{
  "success": false,
  "message": "Failed to ingest docs/architecture.md",
  "repo_url": "https://github.com/owner/repo",
  "errors": ["File not found"],
  "timestamp": "2025-12-12T10:43:39.878Z"
}
```

---

### 8. Ingest Repository Path

**Endpoint**: `/api/ingest/repo-path`

**Method**: `POST`

**Description**: Ingest all markdown files from a specific path in a GitHub repository.

**Request**:
```json
{
  "repo_url": "https://github.com/owner/repo",
  "path": "docs/"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Processed 5/5 files from docs/",
  "repo_url": "https://github.com/owner/repo",
  "collection_name": "repo_abc123",
  "files_processed": 5,
  "chunks_created": 87,
  "errors": null,
  "timestamp": "2025-12-12T10:43:39.878Z"
}
```

**Partial Success Response**:
```json
{
  "success": true,
  "message": "Processed 4/5 files from docs/",
  "repo_url": "https://github.com/owner/repo",
  "collection_name": "repo_abc123",
  "files_processed": 4,
  "chunks_created": 72,
  "errors": ["docs/old.md: File not found"],
  "timestamp": "2025-12-12T10:43:39.878Z"
}
```

---

### 9. Get Ingestion Status

**Endpoint**: `/api/ingest/status`

**Method**: `GET`

**Description**: Check ingestion status for a specific repository.

**Query Parameters**:
- `repo_url` (required): GitHub repository URL

**Example**:
```
GET /api/ingest/status?repo_url=https://github.com/owner/repo
```

**Response**:
```json
{
  "repo_url": "https://github.com/owner/repo",
  "collection_name": "repo_abc123",
  "document_count": 150,
  "last_updated": "2025-12-12T10:43:39.878Z",
  "exists": true
}
```

**Not Found Response**:
```json
{
  "repo_url": "https://github.com/owner/repo",
  "collection_name": "repo_abc123",
  "document_count": 0,
  "last_updated": null,
  "exists": false
}
```

---

### 10. List Ingested Repositories

**Endpoint**: `/api/ingest/repos`

**Method**: `GET`

**Description**: List all repositories that have been ingested.

**Response**:
```json
{
  "repos": [
    {
      "repo_url": "https://github.com/owner/repo1",
      "collection_name": "repo_abc123",
      "document_count": 150
    },
    {
      "repo_url": "https://github.com/owner/repo2",
      "collection_name": "repo_def456",
      "document_count": 87
    }
  ],
  "total": 2
}
```

---

### 11. Delete Document

**Endpoint**: `/api/ingest/document`

**Method**: `DELETE`

**Description**: Remove a specific document from a repository's collection.

**Query Parameters**:
- `repo_url` (required): GitHub repository URL
- `file_path` (required): Path to document file to remove

**Example**:
```
DELETE /api/ingest/document?repo_url=https://github.com/owner/repo&file_path=docs/old.md
```

**Response**:
```json
{
  "success": true,
  "message": "Deleted 12 chunk(s) from docs/old.md",
  "repo_url": "https://github.com/owner/repo",
  "file_path": "docs/old.md",
  "chunks_deleted": 12
}
```

**Error Response** (404):
```json
{
  "detail": "Document not found: docs/old.md"
}
```

---

### 12. Delete Repository Collection

**Endpoint**: `/api/ingest/repo`

**Method**: `DELETE`

**Description**: Remove an entire repository collection from the vector store.

**Query Parameters**:
- `repo_url` (required): GitHub repository URL

**Example**:
```
DELETE /api/ingest/repo?repo_url=https://github.com/owner/repo
```

**Response**:
```json
{
  "success": true,
  "message": "Deleted repository collection: repo_abc123",
  "repo_url": "https://github.com/owner/repo",
  "collection_name": "repo_abc123"
}
```

**Error Response** (404):
```json
{
  "detail": "Repository collection not found: https://github.com/owner/repo"
}
```

---

## 📦 Data Schemas

### BRD Input Schema

```python
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class Project(BaseModel):
    name: str
    description: Optional[str] = None
    objectives: Optional[List[str]] = None
    constraints: Optional[List[str]] = None

class Feature(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    priority: str  # "Critical", "High", "Medium", "Low"
    requirements: Optional[List[str]] = None

class BRDInput(BaseModel):
    # Option 1: PDF Upload (handled separately)
    pdf_file: Optional[str] = None  # base64 encoded
    filename: Optional[str] = None
    
    # Option 2: Structured JSON
    project: Optional[Project] = None
    features: Optional[List[Feature]] = None
    stakeholders: Optional[List[Dict]] = None
    technical_requirements: Optional[Dict] = None
    success_criteria: Optional[List[str]] = None
    
    # Option 3: Raw Text
    raw_brd_text: Optional[str] = None
```

### Engineering Plan Schema

```python
class ProjectOverview(BaseModel):
    name: str
    description: str
    objectives: List[str]

class FeatureBreakdown(BaseModel):
    feature_id: str
    feature_name: str
    description: str
    priority: str  # "Critical", "High", "Medium", "Low"
    complexity: str  # "High", "Medium", "Low"
    estimated_effort: str
    dependencies: List[str]
    technical_requirements: List[str]
    acceptance_criteria: List[str]

class TechnicalArchitecture(BaseModel):
    system_components: List[str]
    integration_points: List[str]
    data_flow: str
    security_considerations: List[str]

class ImplementationPhase(BaseModel):
    phase_number: int
    phase_name: str
    description: str
    features_included: List[str]
    estimated_duration: str
    deliverables: List[str]

class Risk(BaseModel):
    risk_id: str
    description: str
    impact: str  # "High", "Medium", "Low"
    probability: str  # "High", "Medium", "Low"
    mitigation_strategy: str

class ResourceRequirements(BaseModel):
    team_composition: List[str]
    tools_and_technologies: List[str]
    infrastructure_needs: List[str]

class SuccessMetric(BaseModel):
    metric_name: str
    target_value: str
    measurement_method: str

class EngineeringPlan(BaseModel):
    project_overview: ProjectOverview
    feature_breakdown: List[FeatureBreakdown]
    technical_architecture: TechnicalArchitecture
    implementation_phases: List[ImplementationPhase]
    risk_analysis: List[Risk]
    resource_requirements: ResourceRequirements
    success_metrics: List[SuccessMetric]
```

### Project Schedule Schema

```python
class ProjectInfo(BaseModel):
    start_date: str  # YYYY-MM-DD
    end_date: str
    total_duration_weeks: int

class Milestone(BaseModel):
    name: str
    target_date: str
    description: Optional[str] = None

class Task(BaseModel):
    task_id: str
    task_name: str
    start_date: str
    end_date: str
    assigned_to: Optional[str] = None
    dependencies: Optional[List[str]] = None

class SchedulePhase(BaseModel):
    phase_id: str
    phase_name: str
    start_date: str
    end_date: str
    duration_weeks: int
    milestones: List[Milestone]
    tasks: Optional[List[Task]] = None

class ResourceAllocation(BaseModel):
    role: str
    allocation_percentage: int
    phase: Optional[str] = None

class CriticalPath(BaseModel):
    total_duration: str
    critical_tasks: List[str]

class KeyDeliverable(BaseModel):
    deliverable_id: str
    name: str
    target_date: str

class ProjectSchedule(BaseModel):
    project_info: ProjectInfo
    phases: List[SchedulePhase]
    resource_allocation: List[ResourceAllocation]
    critical_path: CriticalPath
    key_deliverables: List[KeyDeliverable]
    assumptions: List[str]
    constraints: List[str]
```

---

## 🔄 LangGraph Workflow

### Workflow Structure

```python
from langgraph.graph import StateGraph, END
from src.brd_agent.graph.state import AgentState

# Create the graph
workflow = StateGraph(AgentState)

# Add nodes (agents)
workflow.add_node("parser", parser_agent.process)
workflow.add_node("planner", planner_agent.process)
workflow.add_node("scheduler", scheduler_agent.process)

# Define edges (flow)
workflow.set_entry_point("parser")
workflow.add_edge("parser", "planner")
workflow.add_edge("planner", "scheduler")
workflow.add_edge("scheduler", END)

# Compile
app = workflow.compile()
```

### Agent State

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class AgentState(BaseModel):
    """State passed between agents in the workflow."""
    
    # Input
    raw_input: Dict[str, Any] = Field(default_factory=dict)
    
    # Parser output
    parsed_brd: Optional[Dict[str, Any]] = None
    
    # Planner output
    engineering_plan: Optional[Dict[str, Any]] = None
    engineering_plan_raw: Optional[str] = None
    
    # Scheduler output
    project_schedule: Optional[Dict[str, Any]] = None
    project_schedule_raw: Optional[str] = None
    
    # Metadata
    errors: List[str] = Field(default_factory=list)
    stages_completed: List[str] = Field(default_factory=list)
```

### Agent Interface

Each agent follows this pattern:

```python
from abc import ABC, abstractmethod
from src.brd_agent.graph.state import AgentState

class BaseAgent(ABC):
    """Abstract base class for all agents."""
    
    def __init__(self, llm_service=None):
        self.llm = llm_service
    
    @abstractmethod
    def process(self, state: AgentState) -> AgentState:
        """Process the state and return updated state."""
        pass
    
    def _load_prompt(self, prompt_name: str) -> str:
        """Load prompt from prompts directory."""
        pass
```

### Adding a New Agent

1. **Create Agent Class**:

```python
# src/brd_agent/agents/new_agent.py
from src.brd_agent.agents.base import BaseAgent
from src.brd_agent.graph.state import AgentState

class NewAgent(BaseAgent):
    """A new agent for specific functionality."""
    
    def process(self, state: AgentState) -> AgentState:
        # Get input from previous agent
        input_data = state.engineering_plan
        
        # Generate output using LLM
        prompt = self._build_prompt(input_data)
        response = self.llm.generate(prompt)
        
        # Update state
        state.new_output = response
        state.stages_completed.append("new_stage")
        
        return state
```

2. **Register in Workflow**:

```python
# src/brd_agent/graph/workflow.py
from src.brd_agent.agents.new_agent import NewAgent

new_agent = NewAgent(llm_service)

workflow.add_node("new_agent", new_agent.process)
workflow.add_edge("scheduler", "new_agent")
workflow.add_edge("new_agent", END)
```

---

## ⚠️ Error Handling

### Error Types

| Error Type | Code | Retry? | Description |
|------------|------|--------|-------------|
| Validation Error | 400 | No | Invalid BRD format |
| Timeout | 504 | Yes | Request exceeded timeout |
| Connection Error | 0 | Yes | Network issue |
| Server Error | 500+ | Yes | Backend failure |
| Rate Limit | 429 | Yes | Too many requests |
| JSON Parse Error | 400 | No | Invalid JSON response |

### Retry Strategy (Frontend)

**Exponential Backoff**:
```python
attempt = 0
wait_time = 0

while attempt < max_retries:
    try:
        response = make_request()
        return response
    except RetryableError:
        attempt += 1
        wait_time = (2 ** attempt) * 2  # 2s, 4s, 8s
        sleep(wait_time)
```

**Configuration**:
- Max attempts: 3
- Wait times: 2s, 4s, 8s
- Total max wait: 14 seconds
- Retryable: Timeout, Connection, 5xx errors
- Non-retryable: 4xx errors, JSON errors

### Backend Error Handling

```python
from fastapi import HTTPException
from pydantic import ValidationError

@app.post("/api/process-brd")
async def process_brd(brd_data: dict):
    try:
        # Process BRD
        result = await workflow.ainvoke(brd_data)
        return result
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

## 📈 Performance & Scalability

### Performance Metrics

| Operation | Time | Bottleneck |
|-----------|------|------------|
| PDF Upload | 0.5-2s | Network, file size |
| PDF Parsing | 5-15s | Claude API, PDF complexity |
| Engineering Plan | 20-40s | Claude API tokens |
| Project Schedule | 15-30s | Claude API tokens |
| Total (PDF) | 60-90s | Sequential processing |
| Total (JSON) | 35-70s | Sequential processing |

### Optimization Strategies

1. **Parallel Processing** (Future):
   ```
   BRD Parser
       ↓
   ┌───────┬────────┐
   │ Plan  │ Design │ (Parallel)
   └───┬───┴────┬───┘
       ↓        ↓
   Schedule  Architecture
   ```

2. **Caching**:
   - Cache parsed BRDs (Redis)
   - Cache AI responses for identical inputs
   - Session-based caching in UI

3. **Streaming**:
   - Stream LLM responses
   - Progressive UI updates

### Scaling Considerations

For production deployment:

```python
# Use async endpoints
@app.post("/api/process-brd")
async def process_brd(brd_data: dict):
    # Use async LLM client
    result = await llm.agenerate(prompt)
    return result

# Configure workers
# uvicorn api.main:app --workers 4
```

---

## 🔒 Security

### Authentication

Currently: **No authentication** (local development)

**Production Recommendations**:

1. **API Key Authentication**:
```python
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != settings.api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

@app.post("/api/process-brd")
async def process_brd(brd_data: dict, api_key: str = Security(verify_api_key)):
    # Process BRD
    pass
```

2. **Streamlit Authentication**:
```python
if 'authenticated' not in st.session_state:
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if authenticate(username, password):
            st.session_state['authenticated'] = True
```

### Data Security

**Sensitive Data**:
- BRD documents (may contain confidential info)
- Generated artifacts (IP protection)

**Best Practices**:
1. **Encryption at Rest**: Encrypt output files
2. **Encryption in Transit**: HTTPS only
3. **Access Control**: Role-based permissions
4. **Audit Logging**: Track who accesses what
5. **Data Retention**: Auto-delete old artifacts

### API Keys

**Required Keys**:
```bash
# .env file
ANTHROPIC_API_KEY=sk-ant-xxx  # Claude AI
```

**Key Management**:
- Rotate quarterly
- Use secrets manager (AWS Secrets Manager, HashiCorp Vault)
- Never commit to git

---

## 🔧 Extension Guide

### Adding a New Agent

#### Step 1: Define Schema

```python
# src/brd_agent/models/new_output.py
from pydantic import BaseModel
from typing import List

class NewOutput(BaseModel):
    items: List[str]
    summary: str
```

#### Step 2: Create Agent

```python
# src/brd_agent/agents/new_agent.py
from src.brd_agent.agents.base import BaseAgent
from src.brd_agent.graph.state import AgentState

class NewAgent(BaseAgent):
    def process(self, state: AgentState) -> AgentState:
        prompt = self._build_prompt(state.engineering_plan)
        response = self.llm.generate(prompt, json_schema=NEW_SCHEMA)
        state.new_output = response
        state.stages_completed.append("new_stage")
        return state
```

#### Step 3: Update State

```python
# src/brd_agent/graph/state.py
class AgentState(BaseModel):
    # ... existing fields ...
    new_output: Optional[Dict[str, Any]] = None
```

#### Step 4: Register in Workflow

```python
# src/brd_agent/graph/workflow.py
from src.brd_agent.agents.new_agent import NewAgent

new_agent = NewAgent(llm_service)
workflow.add_node("new_agent", new_agent.process)
workflow.add_edge("scheduler", "new_agent")
workflow.add_edge("new_agent", END)
```

#### Step 5: Update API Response

```python
# api/main.py
@app.post("/api/process-brd")
async def process_brd(brd_data: dict):
    result = workflow.invoke({"raw_input": brd_data})
    return {
        "engineering_plan": result.get("engineering_plan"),
        "project_schedule": result.get("project_schedule"),
        "new_output": result.get("new_output"),  # Add new field
    }
```

#### Step 6: Update UI

```python
# frontend/utils.py
def display_new_output(data: Dict[str, Any]) -> None:
    import streamlit as st
    
    if not data:
        st.warning("No data available.")
        return
    
    with st.expander("🎯 New Output"):
        st.json(data)

# frontend/app.py
if result.get('new_output'):
    st.header("🎯 New Output")
    utils.display_new_output(result['new_output'])
```

---

## 📚 API Client Examples

### Python

```python
import requests
import json

# Load BRD
with open('brd.json', 'r') as f:
    brd_data = json.load(f)

# Call orchestrator
response = requests.post(
    'http://localhost:8000/api/process-brd',
    json=brd_data,
    headers={'Content-Type': 'application/json'},
    timeout=180
)

result = response.json()

# Save artifacts
with open('engineering_plan.json', 'w') as f:
    json.dump(result['engineering_plan'], f, indent=2)

with open('project_schedule.json', 'w') as f:
    json.dump(result['project_schedule'], f, indent=2)
```

### JavaScript/Node.js

```javascript
const axios = require('axios');
const fs = require('fs');

async function processBRD(brdData) {
  try {
    const response = await axios.post(
      'http://localhost:8000/api/process-brd',
      brdData,
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 180000
      }
    );
    
    const result = response.data;
    
    // Save artifacts
    fs.writeFileSync(
      'engineering_plan.json',
      JSON.stringify(result.engineering_plan, null, 2)
    );
    
    return result;
  } catch (error) {
    console.error('Error:', error.message);
    throw error;
  }
}

// Usage
const brd = require('./brd.json');
processBRD(brd).then(result => {
  console.log('Success:', result.status);
});
```

### cURL

```bash
# JSON BRD
curl -X POST http://localhost:8000/api/process-brd \
  -H "Content-Type: application/json" \
  -d @brd.json \
  -o result.json

# PDF Upload
curl -X POST http://localhost:8000/api/process-brd/upload \
  -F "file=@brd.pdf" \
  -o result.json
```

---

## 📞 Support & Resources

### Code Locations
```
├── api/                # FastAPI backend
│   ├── main.py        # Orchestrator API
│   └── pdf_parser.py  # PDF parsing endpoints
├── frontend/          # Streamlit UI
│   ├── app.py         # Main application
│   ├── utils.py       # Helper functions
│   └── config.py      # Configuration
├── src/brd_agent/     # Core library
│   ├── agents/        # Agent implementations
│   ├── graph/         # LangGraph workflow
│   ├── models/        # Pydantic schemas
│   └── services/      # LLM abstraction
└── tests/             # Test suite
```

### Documentation
- **Main README**: `README.md`
- **Setup Guide**: `SETUP.md`
- **User Guide**: `USER_GUIDE.md`
- **This Document**: `API_REFERENCE.md`
- **Architecture**: `ARCHITECTURE.md`

### Getting Help
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions

---

**Last Updated**: December 2025

*For the latest updates, check the GitHub repository.*

