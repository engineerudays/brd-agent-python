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

### 🚧 Coming Soon

- **🏗️ Architecture Design Agent** - Generate system architecture diagrams
- **💡 Tech Stack Agent** - Recommend and justify technology choices
- **💻 PoC Generator** - Create working proof-of-concept code
- **🤖 Gemma2 Support** - Local LLM via Ollama
- **📚 RAG Integration** - Query existing system documentation

---

## 📚 Documentation

| Document | Audience | Description |
|----------|----------|-------------|
| **[README.md](README.md)** | Everyone | Project overview, quick start |
| **[SETUP.md](SETUP.md)** | DevOps/Admins | Installation, configuration |
| **[USER_GUIDE.md](USER_GUIDE.md)** | End Users | Usage guide, troubleshooting |
| **[API_REFERENCE.md](API_REFERENCE.md)** | Developers | API endpoints, schemas |
| **[ARCHITECTURE.md](ARCHITECTURE.md)** | Architects | System design, data flow |

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
│                    /api/process-brd                         │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph Workflow                       │
├─────────────────────────────────────────────────────────────┤
│  ParserAgent → PlannerAgent → SchedulerAgent               │
│       ↓              ↓              ↓                       │
│  Normalized      Engineering    Project                     │
│     BRD            Plan         Schedule                    │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
                    ┌─────────────┐
                    │  Anthropic  │
                    │   Claude    │
                    └─────────────┘
```

### Technology Stack

- **Workflow Engine**: LangGraph (Python)
- **Backend**: FastAPI
- **Frontend**: Streamlit
- **AI**: Anthropic Claude (Haiku/Sonnet)
- **Visualization**: Plotly (Gantt charts)
- **Data Validation**: Pydantic

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Anthropic API Key

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

# 5. Start the backend
uvicorn api.main:app --reload --port 8000

# 6. Start the frontend (new terminal)
streamlit run frontend/app.py
```

Open: **http://localhost:8501**

📖 **For detailed setup instructions, see [SETUP.md](SETUP.md)**

---

## 📝 Usage Example

### Input BRD (JSON)

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

### Generated Output

The system generates:
1. **Engineering Plan** - Features, phases, risks, resources
2. **Project Schedule** - Timeline with dates, tasks, milestones
3. **Gantt Chart** - Visual representation

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
│   │   ├── planner.py       # Engineering plan generator
│   │   └── scheduler.py     # Project schedule generator
│   ├── graph/               # LangGraph workflow
│   │   ├── state.py         # Pipeline state definition
│   │   └── workflow.py      # Workflow orchestration
│   ├── models/              # Pydantic schemas
│   │   ├── brd.py           # BRD input models
│   │   ├── plan.py          # Engineering plan models
│   │   └── schedule.py      # Project schedule models
│   └── services/            # External services
│       └── llm.py           # LLM abstraction
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

---

## 🎯 Roadmap

### Phase 1: Core Pipeline ✅ Complete
- [x] LangGraph workflow
- [x] Engineering Plan Generator
- [x] Project Schedule Generator
- [x] Streamlit UI
- [x] FastAPI backend

### Phase 2: Local LLM 🚧 Planned
- [ ] Ollama integration
- [ ] Gemma2 support
- [ ] Model switching in UI

### Phase 3: RAG Extension 💡 Future
- [ ] Document ingestion
- [ ] Vector database
- [ ] Context-aware planning

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
- **Original n8n Implementation** - [brd_agent_em](../brd_agent_em)

---

## 📧 Contact

**Author**: Uday Ammanagi  
**GitHub**: [@engineerudays](https://github.com/engineerudays)

---

**⭐ If you find this project interesting, please star the repository!**
