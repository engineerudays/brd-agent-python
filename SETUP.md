# 🚀 Setup & Execution Guide
## BRD Agent Python - Multi-Agent System

Complete guide to set up and run the BRD to Engineering Artifacts pipeline.

---

## 📋 Prerequisites

### Required Software
- **Python 3.11+** - Core runtime
- **pip** - Package manager
- **Git** - Version control (optional)
- **Ollama** - For RAG embeddings (required for RAG features)
  ```bash
  # macOS
  brew install ollama
  brew services start ollama
  
  # Pull embedding model
  ollama pull nomic-embed-text
  
  # Verify Ollama is running
  curl http://localhost:11434/api/tags
  ```

### Optional Tools
- **curl** - API testing (usually pre-installed)
- **jq** - JSON processor (for pretty-printing responses)
  ```bash
  # macOS
  brew install jq
  
  # Ubuntu/Debian
  sudo apt-get install jq
  ```

### Required API Keys
- **Anthropic API Key** - Get from: https://console.anthropic.com/

### System Requirements
- **OS**: macOS, Linux, or Windows
- **RAM**: 4GB minimum (8GB recommended)
- **Disk**: 1GB free space
- **Network**: Internet access for AI API calls

---

## 🏗️ Architecture Quick Reference

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit UI (Port 8501)                 │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP POST
                             ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Orchestrator (Port 8000)               │
│         /api/process-brd  |  /api/ingest/*                  │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph Workflow                       │
├─────────────────────────────────────────────────────────────┤
│  ParserAgent → RetrieverAgent → PlannerAgent → SchedulerAgent │
│       ↓              ↓              ↓              ↓         │
│  Normalized    Retrieved    Engineering    Project          │
│     BRD        Context        Plan         Schedule         │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
                    ┌─────────────┐
                    │  Anthropic  │
                    │   Claude    │
                    └─────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    RAG Infrastructure                       │
├─────────────────────────────────────────────────────────────┤
│  ChromaDB ← Embeddings (Ollama) ← Chunking ← GitHub API     │
│  Vector Store    (nomic-embed)    Strategies   Client       │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/engineerudays/brd-agent-python.git
cd brd-agent-python
```

Or if you already have the repository:
```bash
cd /path/to/brd_agent_python
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

You should see `(.venv)` prefix in your terminal.

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- **langgraph** - Workflow orchestration
- **anthropic** - Claude AI SDK
- **fastapi** - API framework
- **uvicorn** - ASGI server
- **streamlit** - Web UI
- **plotly** - Gantt charts
- **pandas** - Data processing
- **pydantic** - Data validation
- **pypdf** - PDF parsing
- **python-multipart** - File uploads
- **chromadb** - Vector database for RAG
- **httpx** - HTTP client for GitHub API
- **ollama** - Ollama client for embeddings
- **typer** - CLI framework
- **rich** - Terminal formatting

### Step 4: Configure Environment

```bash
# Copy template to .env
cp env.template .env

# Edit .env with your API key
nano .env  # or use your preferred editor
```

**Required Configuration:**
```bash
# .env file
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**Optional RAG Configuration:**
```bash
# RAG Feature Flag
RAG_ENABLED=false  # Set to true to enable RAG

# Default Repository (used if repo_url not specified in BRD)
DEFAULT_REPO_URL=https://github.com/paperless-ngx/paperless-ngx

# Retrieval Settings
RAG_TOP_K=15                    # Number of chunks to retrieve per query
RAG_QUERY_COUNT=7               # Number of expanded queries (query expansion)

# ChromaDB Settings
CHROMADB_PATH=./.chromadb       # Path for vector store persistence

# Ollama Settings
OLLAMA_EMBEDDING_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

**⚠️ Important:** 
- Replace `sk-ant-your-key-here` with your actual Anthropic API key
- Never commit `.env` to git (it's in `.gitignore`)
- For RAG features, ensure Ollama is running before starting the backend

### Step 5: Verify Installation

```bash
# Test Python imports
python -c "from src.brd_agent.agents import PlannerAgent; print('✓ Agents OK')"
python -c "from src.brd_agent.graph.workflow import create_workflow; print('✓ Workflow OK')"
python -c "import anthropic; print('✓ Anthropic SDK OK')"
```

### Step 6: Setup RAG (Optional but Recommended)

RAG (Retrieval-Augmented Generation) enables context-aware planning by retrieving relevant documentation from your codebase.

**Prerequisites:**
1. Ollama must be installed and running (see Prerequisites above)
2. Embedding model must be pulled: `ollama pull nomic-embed-text`

**Quick Setup:**
```bash
# 1. Verify Ollama is running
curl http://localhost:11434/api/tags

# 2. Enable RAG in .env
echo "RAG_ENABLED=true" >> .env

# 3. Ingest documentation from a repository
python -m cli.ingest https://github.com/your-org/your-repo

# 4. Restart backend to load RAG configuration
# (Press Ctrl+C in backend terminal, then restart)
uvicorn api.main:app --reload --port 8000
```

**Collection Naming Convention**:
- Each repository gets its own ChromaDB collection
- Collection names are derived from repository URLs (normalized: `owner_repo`)
- Example: `https://github.com/paperless-ngx/paperless-ngx` → collection name: `paperless-ngx_paperless-ngx`
- Collections are stored persistently in `.chromadb/` directory (configurable via `CHROMADB_PATH`)

**For detailed RAG usage, see [USER_GUIDE.md](USER_GUIDE.md#rag-setup-and-usage)**

---

## 🚀 Running the Application

### Start Backend (FastAPI)

**Terminal 1:**
```bash
# Ensure virtual environment is active
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Start the backend server
uvicorn api.main:app --reload --port 8000
```

**Expected Output:**
```
INFO:     Will watch for changes in these directories: ['/path/to/brd_agent_python']
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Started reloader process
```

### Start Frontend (Streamlit)

**Terminal 2:**
```bash
# Navigate to project and activate venv
cd /path/to/brd_agent_python
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Start the frontend
streamlit run frontend/app.py --server.port 8501
```

**Expected Output:**
```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

### Verify Services

```bash
# Check backend health
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","llm_configured":true}
```

Open in browser: **http://localhost:8501**

---

## 🧪 Testing the Pipeline

### Quick Test - End-to-End

**Option 1: Using the UI**
1. Open http://localhost:8501
2. Select "Load Sample" radio button
3. Click "🚀 Process BRD"
4. Wait 30-60 seconds
5. View results in "Results" and "Timeline" tabs

**Option 2: Using curl**
```bash
# Send a test BRD to the API
curl -X POST http://localhost:8000/api/process-brd \
  -H "Content-Type: application/json" \
  -d '{
    "project": {
      "name": "Test Project",
      "description": "A simple test project"
    },
    "features": [
      {
        "id": "F001",
        "name": "User Login",
        "priority": "High"
      }
    ]
  }' | jq
```

### Check Generated Outputs

```bash
# Engineering plans
ls -lh sample_inputs/outputs/engineering_plans/

# Project schedules
ls -lh sample_inputs/outputs/project_schedules/
```

### RAG Test (Optional)

**Prerequisites**: RAG enabled, documentation ingested

```bash
# 1. Ingest test repository
python -m cli.ingest https://github.com/paperless-ngx/paperless-ngx

# 2. Process BRD with RAG (via API)
curl -X POST http://localhost:8000/api/process-brd \
  -H "Content-Type: application/json" \
  -d @sample_inputs/brds/step-16-e2e-test-paperless_ngx_feature.json

# 3. Check ingestion status
curl "http://localhost:8000/api/ingest/status?repo_url=https://github.com/paperless-ngx/paperless-ngx"
```

**See [scripts/test_step16_end_to_end.py](scripts/test_step16_end_to_end.py) for complete end-to-end test**

---

## 🔧 Configuration Options

### Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Yes | Your Anthropic API key | - |
| `DEFAULT_MODEL` | No | Claude model to use | `claude-sonnet-4-20250514` |
| `OUTPUT_DIR` | No | Directory for artifacts | `sample_inputs/outputs` |
| `RAG_ENABLED` | No | Enable/disable RAG feature | `false` |
| `DEFAULT_REPO_URL` | No | Default repository for RAG | `https://github.com/paperless-ngx/paperless-ngx` |
| `RAG_TOP_K` | No | Chunks to retrieve per query | `15` |
| `RAG_QUERY_COUNT` | No | Number of expanded queries | `7` |
| `CHROMADB_PATH` | No | Vector store persistence path | `./.chromadb` |
| `OLLAMA_EMBEDDING_URL` | No | Ollama API URL | `http://localhost:11434` |
| `OLLAMA_EMBEDDING_MODEL` | No | Embedding model name | `nomic-embed-text` |

### Frontend Configuration

Edit `frontend/config.py`:

```python
# API endpoint (change if backend runs on different port)
ORCHESTRATOR_URL = "http://localhost:8000/api/process-brd"

# Request timeout (seconds)
TIMEOUT = 180

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 2.0
```

---

## 📁 Project Structure

```
brd_agent_python/
├── api/                      # FastAPI services
│   ├── __init__.py
│   ├── main.py              # Orchestrator API
│   ├── pdf_parser.py        # PDF parsing endpoints
│   └── ingest.py           # Ingestion API endpoints (NEW)
├── frontend/                 # Streamlit UI
│   ├── __init__.py
│   ├── app.py               # Main application
│   ├── utils.py             # Helper functions
│   ├── config.py            # Configuration
│   └── requirements.txt     # Frontend deps (subset)
├── cli/                     # CLI tools (NEW)
│   ├── __init__.py
│   ├── __main__.py          # CLI entry point
│   └── ingest.py           # Bulk ingestion CLI (NEW)
├── src/brd_agent/           # Core library
│   ├── __init__.py
│   ├── agents/              # Agent implementations
│   │   ├── __init__.py
│   │   ├── base.py          # Abstract base agent
│   │   ├── parser.py        # Input normalizer
│   │   ├── retriever.py     # RAG context retrieval (NEW)
│   │   ├── planner.py       # Engineering plan agent (RAG-enhanced)
│   │   └── scheduler.py     # Project schedule agent
│   ├── graph/               # LangGraph workflow
│   │   ├── __init__.py
│   │   ├── state.py         # Pipeline state
│   │   └── workflow.py      # Workflow definition
│   ├── models/              # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── brd.py           # BRD models
│   │   ├── plan.py          # Engineering plan models
│   │   └── schedule.py      # Schedule models
│   ├── prompts/             # AI prompts (future)
│   ├── services/            # External services
│   │   ├── __init__.py
│   │   ├── llm.py           # LLM abstraction
│   │   ├── vector_store.py  # ChromaDB vector store (NEW)
│   │   ├── embeddings.py    # Ollama embedding service (NEW)
│   │   ├── chunking.py      # Document chunking strategies (NEW)
│   │   ├── github_client.py # GitHub API client (NEW)
│   │   ├── document_loaders/ # Document loaders (NEW)
│   │   │   └── markdown_loader.py
│   │   └── repository_analyzer.py # Repository analysis (NEW)
│   └── config.py            # App configuration
├── sample_inputs/           # Test data
│   ├── brds/                # Sample BRD files
│   └── outputs/             # Generated artifacts
├── scripts/                 # Test scripts (NEW)
│   ├── test_step*.py        # Step-by-step test scripts
│   └── demo_step*.py        # Demo scripts
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── integration/
│   └── unit/
├── .env                     # Environment variables (create this)
├── env.template             # Environment template
├── requirements.txt         # Python dependencies
├── README.md                # Project overview
├── SETUP.md                 # This file
├── USER_GUIDE.md            # End-user documentation
├── API_REFERENCE.md         # API documentation
└── ARCHITECTURE.md          # System design
```

---

## 🛠️ Common Commands

### Service Management

```bash
# Start backend (development mode with auto-reload)
uvicorn api.main:app --reload --port 8000

# Start frontend
streamlit run frontend/app.py --server.port 8501

# Stop services
# Press Ctrl+C in each terminal
```

### Package Management

```bash
# Activate virtual environment
source .venv/bin/activate

# Install new package
pip install <package-name>

# Update requirements.txt
pip freeze > requirements.txt

# Install from requirements
pip install -r requirements.txt
```

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Liveness check
curl http://localhost:8000/
```

### CLI Tools

```bash
# Bulk ingestion CLI
python -m cli.ingest https://github.com/owner/repo
python -m cli.ingest https://github.com/owner/repo --path docs/
python -m cli.ingest  # Uses default repo from config

# Check ingestion status via API
curl "http://localhost:8000/api/ingest/status?repo_url=https://github.com/owner/repo"

# List ingested repositories
curl http://localhost:8000/api/ingest/repos
```

---

## 🐛 Troubleshooting

### "ModuleNotFoundError: No module named 'brd_agent'"

**Cause**: Virtual environment not activated or package not installed

**Solution**:
```bash
# Activate venv
source .venv/bin/activate

# Reinstall
pip install -r requirements.txt
```

### "Error: ANTHROPIC_API_KEY not set"

**Cause**: Missing or invalid API key

**Solution**:
```bash
# Check .env file exists
cat .env

# Verify key format (starts with sk-ant-)
# If missing, create it:
echo "ANTHROPIC_API_KEY=sk-ant-your-key-here" > .env
```

### "Port 8000 already in use"

**Cause**: Another process using the port

**Solution**:
```bash
# Find and kill the process
lsof -i :8000
kill -9 <PID>

# Or use a different port
uvicorn api.main:app --port 8001
```

### "Connection refused" from Streamlit

**Cause**: Backend not running or wrong URL

**Solution**:
1. Verify backend is running: `curl http://localhost:8000/health`
2. Check `frontend/config.py` for correct URL
3. Update Orchestrator URL in sidebar if needed

### "Processing failed: Validation errors"

**Cause**: LLM output doesn't match schema

**Solution**:
1. Check backend logs for specific errors
2. Try with a simpler BRD
3. Open an issue if persistent

### "Ollama connection error" or "RAG not working"

**Causes**:
- Ollama not running
- Embedding model not pulled
- RAG_ENABLED=false in .env

**Solutions**:
```bash
# 1. Check Ollama is running
curl http://localhost:11434/api/tags

# 2. Start Ollama if not running
brew services start ollama  # macOS

# 3. Pull embedding model
ollama pull nomic-embed-text

# 4. Verify RAG is enabled in .env
grep RAG_ENABLED .env  # Should show RAG_ENABLED=true

# 5. Restart backend after changing .env
```

### "No context retrieved" or "Collection not found"

**Causes**:
- Documentation not ingested
- Wrong repository URL
- ChromaDB collection doesn't exist

**Solutions**:
```bash
# 1. Check ingestion status
curl "http://localhost:8000/api/ingest/status?repo_url=https://github.com/owner/repo"

# 2. Ingest documentation if needed
python -m cli.ingest https://github.com/owner/repo

# 3. Verify collection exists
ls -la .chromadb/
```

---

## 🔒 Security Notes

1. **API Key Protection**:
   - Never commit `.env` to git
   - Don't share your API key
   - Rotate keys periodically

2. **Local Development Only**:
   - This setup is for local development
   - Don't expose ports to public internet without authentication

3. **Data Privacy**:
   - BRDs may contain confidential information
   - Generated artifacts are stored locally
   - Clear outputs directory when done

---

## 🎯 Next Steps

After successful setup:

1. **Test with Sample BRD**: Use "Load Sample" in UI
2. **Try PDF Upload**: Upload your own BRD PDF
3. **Explore Results**: Check all sections in Results tab
4. **View Timeline**: Interact with Gantt chart
5. **Download Artifacts**: Export plans as JSON

---

## 📚 Additional Resources

- **LangGraph Documentation**: https://langchain-ai.github.io/langgraph/
- **Anthropic API**: https://docs.anthropic.com/
- **FastAPI**: https://fastapi.tiangolo.com/
- **Streamlit**: https://docs.streamlit.io/

---

## 🆘 Getting Help

1. Check troubleshooting section above
2. Review logs in terminal
3. Open GitHub issue with:
   - Error message
   - Steps to reproduce
   - Environment details

---

**🎉 You're all set!** Open the Streamlit UI and start processing BRDs.

