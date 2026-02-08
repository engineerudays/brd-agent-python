# 🐍 BRD Agent Python

A Python implementation of the BRD Agent - Multi-Agent Engineering Manager.

Transform Business Requirements Documents (BRDs) into Engineering Artifacts using LangGraph, FastAPI, and Anthropic Claude.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🎯 What Does It Do?

BRD Agent automates the conversion of business requirements into actionable engineering deliverables:

**Input:** Business Requirements Document (BRD) in **PDF** or **JSON** format

**Output:**
- 📋 **Engineering Plan** - Detailed feature breakdown, technical architecture, implementation phases
- 📅 **Project Schedule** - Timeline, milestones, task assignments, resource allocation
- 📊 **Interactive Gantt Chart** - Visual project timeline (via Streamlit UI)
- ⚠️ **Risk Analysis** - Identified risks with mitigation strategies
- 👥 **Resource Requirements** - Team composition and technology stack

---

## ✨ Features

### ✅ Currently Implemented

- **🐍 Pure Python** - No n8n dependency, uses LangGraph for orchestration
- **🔄 LangGraph Workflow** - Parser → Planner → Scheduler pipeline
- **🎨 Streamlit UI** - Beautiful, interactive web interface
- **📄 PDF Upload Support** - Upload BRDs in PDF format with automatic parsing
- **📋 Engineering Plan Generator** - Creates detailed engineering specifications with AI
- **📅 Project Schedule Generator** - Builds comprehensive project timelines
- **📊 Interactive Gantt Chart** - Visual timeline with phases and milestones
- **🔄 Auto-Retry Logic** - Automatic retry with exponential backoff (3 attempts)
- **💾 Download Artifacts** - Export results as JSON
- **📚 RAG Infrastructure** - Complete RAG system for context-aware planning ✅
  - **🗄️ ChromaDB Vector Store** - Persistent vector database with multi-repository support
  - **🔢 Ollama Embeddings** - Local embedding generation via Ollama (nomic-embed-text)
  - **✂️ Smart Chunking** - Header-based, recursive, and code-aware chunking strategies
  - **🐙 GitHub API Client** - Repository content fetching with rate limit handling
  - **🔍 RetrieverAgent** - Query expansion RAG pattern for enhanced retrieval
  - **🎯 Context-Aware Planning** - PlannerAgent uses retrieved documentation to align with existing architecture
  - **📥 CLI Ingestion Tool** - Bulk ingestion of GitHub repositories
  - **🔌 Ingestion API** - REST endpoints for incremental document management
  - **🔎 Repository Analyzer** - Automatic discovery of documentation and code structure

### 🚧 Coming Soon

- **🏗️ Architecture Design Agent** - Generate system architecture diagrams
- **💡 Tech Stack Agent** - Recommend and justify technology choices
- **💻 PoC Generator** - Create working proof-of-concept code
- **🤖 Gemma2 Support** - Local LLM via Ollama

---

## 📚 Documentation

| Document | Audience | Description |
|----------|----------|-------------|
| **[README.md](README.md)** | Everyone | Project overview, quick start |
| **[SETUP.md](SETUP.md)** | DevOps/Admins | Installation, configuration |
| **[USER_GUIDE.md](USER_GUIDE.md)** | End Users | Usage guide, troubleshooting |
| **[API_REFERENCE.md](API_REFERENCE.md)** | Developers | API endpoints, schemas |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | Architects | System design, data flow |
| **[docs/RAG_EXPLORATION.md](docs/RAG_EXPLORATION.md)** | Architects/Developers | RAG integration design and patterns |

---

## 🏗️ Architecture

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

### Technology Stack

- **Workflow Engine**: LangGraph (Python)
- **Backend**: FastAPI
- **Frontend**: Streamlit
- **AI**: Anthropic Claude (Haiku/Sonnet)
- **Visualization**: Plotly (Gantt charts)
- **Data Validation**: Pydantic
- **Vector Database**: ChromaDB (persistent, embedded)
- **Embeddings**: Ollama (nomic-embed-text, 768 dimensions)
- **Document Processing**: Custom chunking strategies (header-based, recursive)

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Anthropic API Key
- **Ollama** (for RAG embeddings) - Required for RAG features
  ```bash
  # macOS
  brew install ollama
  brew services start ollama
  
  # Pull embedding model
  ollama pull nomic-embed-text
  
  # Verify Ollama is running
  curl http://localhost:11434/api/tags
  ```
  
  **Note**: RAG features require Ollama to be running. Without it, the system will work but won't retrieve context from documentation.

### Installation (5 minutes)

```bash
# 1. Clone repository
git clone https://github.com/engineerudays/brd-agent-python.git
cd brd-agent-python

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp env.template .env
# Edit .env and add your ANTHROPIC_API_KEY
# Optional: Configure RAG settings (see RAG Setup below)

# 5. Start the backend
uvicorn api.main:app --reload --port 8000

# 6. Start the frontend (new terminal)
streamlit run frontend/app.py
```

Open: **http://localhost:8501**

📖 **For detailed setup instructions, see [SETUP.md](SETUP.md)**

---

## 🔍 RAG Setup (Context-Aware Planning)

The BRD Agent now supports **Retrieval-Augmented Generation (RAG)** to generate plans aligned with your existing system architecture.

### Quick Setup

1. **Ensure Ollama is running** (see Prerequisites above)

2. **Ingest documentation** from your repository:
   ```bash
   # Using CLI (recommended)
   python -m cli.ingest https://github.com/your-org/your-repo
   
   # Or ingest specific path
   python -m cli.ingest https://github.com/your-org/your-repo --path docs/
   ```

3. **Enable RAG** in `.env`:
   ```bash
   RAG_ENABLED=true
   DEFAULT_REPO_URL=https://github.com/your-org/your-repo
   ```

4. **Process BRD** - The system will automatically retrieve relevant context and generate aligned plans!

### RAG Configuration Options

Add to your `.env` file:

```bash
# RAG Feature Flag
RAG_ENABLED=true

# Default Repository (used if repo_url not specified in BRD)
DEFAULT_REPO_URL=https://github.com/your-org/your-repo

# Retrieval Settings
RAG_TOP_K=15                    # Number of chunks to retrieve per query
RAG_QUERY_COUNT=7               # Number of expanded queries (query expansion)

# ChromaDB Settings
CHROMADB_PATH=./.chromadb       # Path for vector store persistence

# Ollama Settings
OLLAMA_EMBEDDING_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

### CLI Ingestion Commands

```bash
# Ingest entire repository (uses default from config if not specified)
python -m cli.ingest

# Ingest specific repository
python -m cli.ingest https://github.com/paperless-ngx/paperless-ngx

# Ingest specific path within repository
python -m cli.ingest https://github.com/owner/repo --path docs/

# Check ingestion status
curl http://localhost:8000/api/ingest/status?repo_url=https://github.com/owner/repo

# List all ingested repositories
curl http://localhost:8000/api/ingest/repos
```

📖 **For detailed RAG usage, see [USER_GUIDE.md](USER_GUIDE.md#rag-setup-and-usage)**

---

## 📝 Usage Examples

### Example 1: Basic BRD Processing (Without RAG)

**Input BRD (JSON)**:

```json
{
  "project": {
    "name": "Customer Onboarding Portal",
    "description": "A portal to streamline customer onboarding",
    "objectives": ["Reduce churn", "Improve TTV"]
  },
  "features": [
    {
      "id": "F001",
      "name": "Single Sign-On",
      "priority": "Critical"
    }
  ]
}
```

**Generated Output**:
1. **Engineering Plan** - Features, phases, risks, resources
2. **Project Schedule** - Timeline with dates, tasks, milestones
3. **Gantt Chart** - Visual representation

---

### Example 2: Context-Aware Planning with RAG

**Step 1: Ingest your repository documentation**
```bash
python -m cli.ingest https://github.com/your-org/your-repo
```

**Step 2: Process BRD with RAG enabled**
```json
{
  "project": {
    "name": "Enhanced Document Search",
    "description": "Add advanced filters to document search"
  },
  "features": [
    {
      "id": "F001",
      "name": "Advanced Filters",
      "priority": "High"
    }
  ],
  "repo_url": "https://github.com/your-org/your-repo"
}
```

**What happens**:
1. **RetrieverAgent** extracts BRD summary and generates expanded queries
2. **ChromaDB** retrieves relevant documentation chunks (architecture, patterns, conventions)
3. **PlannerAgent** receives context and generates plan aligned with existing system:
   - Uses existing tech stack (e.g., Django, React)
   - Follows architectural patterns from docs
   - References existing services and integrations
   - Cites source documentation in plan

**Generated Output** (Enhanced):
- **Engineering Plan** - Aligned with existing architecture, cites sources
- **Project Schedule** - Accounts for existing codebase structure
- **Technical Architecture** - Integrates with existing components

📖 **See [sample_inputs/outputs/step-16-e2e-test-engineering_plan.json](sample_inputs/outputs/step-16-e2e-test-engineering_plan.json) for a real example**

---

## 📁 Project Structure

```
brd_agent_python/
├── api/                      # FastAPI services
│   ├── main.py              # Orchestrator API
│   └── pdf_parser.py        # PDF parsing service
├── frontend/                 # Streamlit UI
│   ├── app.py               # Main application
│   ├── utils.py             # Helper functions
│   └── config.py            # UI configuration
├── src/brd_agent/           # Core library
│   ├── agents/              # Agent implementations
│   │   ├── parser.py        # BRD normalizer
│   │   ├── retriever.py      # RAG context retrieval (query expansion)
│   │   ├── planner.py       # Engineering plan generator (RAG-enhanced)
│   │   └── scheduler.py     # Project schedule generator
│   ├── graph/               # LangGraph workflow
│   │   ├── state.py         # Pipeline state definition
│   │   └── workflow.py      # Workflow orchestration
│   ├── models/              # Pydantic schemas
│   │   ├── brd.py           # BRD input models
│   │   ├── plan.py          # Engineering plan models
│   │   └── schedule.py      # Project schedule models
│   └── services/            # External services
│       ├── llm.py           # LLM abstraction
│       ├── vector_store.py  # ChromaDB vector store
│       ├── embeddings.py   # Ollama embedding service
│       ├── chunking.py      # Document chunking strategies
│       ├── github_client.py # GitHub API client
│       └── repository_analyzer.py # Repository analysis
├── api/                     # FastAPI services
│   ├── main.py             # Orchestrator API
│   ├── pdf_parser.py       # PDF parsing service
│   └── ingest.py           # Ingestion API endpoints
├── cli/                     # CLI tools
│   └── ingest.py           # Bulk ingestion CLI
├── sample_inputs/           # Test data
│   ├── brds/                # Sample BRD files
│   └── outputs/             # Generated artifacts
├── tests/                   # Test suite
├── requirements.txt         # Python dependencies
└── .env                     # Environment configuration
```

---

## 🧪 Testing

### Quick Test - API

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test full pipeline
curl -X POST http://localhost:8000/api/process-brd \
  -H "Content-Type: application/json" \
  -d '{"project": {"name": "Test"}, "features": []}'
```

### UI Test

1. Open http://localhost:8501
2. Click "Load Sample" to use demo BRD
3. Click "🚀 Process BRD"
4. View results in Results and Timeline tabs

### RAG Test

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

📖 **See [scripts/test_step16_end_to_end.py](scripts/test_step16_end_to_end.py) for complete end-to-end test**

---

## 🎯 Roadmap

### Phase 1: Core Pipeline ✅ Complete
- [x] LangGraph workflow
- [x] Engineering Plan Generator
- [x] Project Schedule Generator
- [x] Streamlit UI
- [x] FastAPI backend

### Phase 2: Local LLM 🚧 Planned
- [ ] Ollama integration for LLM (Gemma2 support)
- [ ] Model switching in UI
- [x] Ollama integration for embeddings ✅ (nomic-embed-text)

### Phase 3: RAG Extension ✅ Complete
- [x] Configuration & setup ✅
- [x] ChromaDB vector store ✅
- [x] Ollama embedding service ✅
- [x] Chunking strategies (header-based, recursive, code-aware) ✅
- [x] GitHub API client ✅
- [x] Document loaders (Markdown) ✅
- [x] CLI bulk ingestion tool ✅
- [x] Ingestion API endpoints ✅
- [x] Query expansion RAG pattern ✅
- [x] RetrieverAgent integration ✅
- [x] Context-aware planning ✅
- [x] Repository analyzer ✅
- [x] End-to-end testing ✅

### Phase 4: Advanced Features 🚧 Planned
- [ ] Document loaders (OpenAPI, PDF)
- [ ] Architecture Design Agent
- [ ] Tech Stack Agent
- [ ] PoC Generator
- [ ] Gemma2 Support (Local LLM)

---

## 🤝 Contributing

This is a personal project for learning and demonstration. Feel free to:
- Fork and experiment
- Submit issues for bugs
- Suggest improvements

---

## 📜 License

MIT License - Feel free to use this project for learning and inspiration.

---

## 🙏 Acknowledgments

- **LangGraph** - Workflow orchestration
- **Anthropic** - Claude AI models
- **Streamlit** - Beautiful UI framework
- **ChromaDB** - Vector database for RAG
- **Ollama** - Local embedding generation
- **Original n8n Implementation** - [brd_agent_em](../brd_agent_em)

---

## 📧 Contact

**Author**: Uday Ammanagi  
**GitHub**: [@engineerudays](https://github.com/engineerudays)

---

**⭐ If you find this project interesting, please star the repository!**
