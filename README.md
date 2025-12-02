# 🐍 BRD Agent Python

A Python implementation of the BRD Agent - Multi-Agent Engineering Manager.

Transform Business Requirements Documents (BRDs) into Engineering Artifacts using LangChain, LangGraph, and Anthropic Claude.

## 🚧 Status: In Development

This is a rebuild of the n8n-based BRD Agent in pure Python.

### Completed
- [x] Project structure
- [x] Configuration module
- [x] Pydantic models (BRD, Engineering Plan, Project Schedule)
- [x] LLM service abstraction (Anthropic + Ollama placeholder)

### In Progress
- [ ] Agent implementations (Parser, Planner, Scheduler)
- [ ] LangGraph workflow
- [ ] CLI interface
- [ ] FastAPI backend

## 📁 Project Structure

```
brd_agent_python/
├── src/
│   └── brd_agent/
│       ├── agents/         # Individual agents
│       ├── graph/          # LangGraph workflows
│       ├── models/         # Pydantic schemas
│       ├── prompts/        # LLM prompts
│       ├── services/       # LLM, PDF parsing, etc.
│       └── config.py       # Settings
├── api/                    # FastAPI REST API
├── cli/                    # CLI interface
├── tests/                  # Unit & integration tests
└── sample_inputs/          # Sample BRDs and outputs
```

## 🚀 Quick Start

```bash
# 1. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp env.template .env
# Edit .env and add your ANTHROPIC_API_KEY

# 4. Run (coming soon)
# python -m cli.main generate --input sample_inputs/brds/brd_input_cleaner.json
```

## 🔧 Configuration

Copy `env.template` to `.env` and configure:

```bash
ANTHROPIC_API_KEY=your-key-here
LLM_MODEL=claude-3-haiku-20240307
```

## 📚 Related

- [brd_agent_em](../brd_agent_em) - Original n8n implementation

