# RAG Integration Exploration

## Extending BRD Agent for Incremental Feature Planning

> **Date:** December 21, 2025  
> **Status:** Exploration Phase  
> **Goal:** Extend BRD Agent as a Design & Planning Agent for incremental features on existing systems

---

## 📋 Problem Statement

### Current State
- Working BRD Agent with Parser → Planner → Scheduler pipeline
- Generates engineering plans and project schedules from BRDs

### Goal
- Extend to a Design & Planning Agent for **incremental features** on an **existing system**
- Generate plans that **fit** the existing architecture, tech stack, and conventions

### The Core Problem

When planning a **new feature** for an **existing system**, a generic LLM:

- ❌ Doesn't know your current tech stack
- ❌ Suggests patterns that conflict with your architecture
- ❌ Recommends technologies you don't use
- ❌ Ignores existing services you should integrate with

**RAG solves this** by retrieving relevant context from your existing documentation before generating plans.

---

## 🏗️ Design Patterns for RAG

### Pattern 1: Naive RAG (Simple)

```
Query → Embed → Search → Top-K Chunks → LLM Prompt
```

**How it works:**
1. Embed the user's query (BRD content)
2. Find similar chunks in vector store
3. Stuff chunks into LLM prompt
4. Generate response

| Pros | Cons |
|------|------|
| Simple | Retrieval quality can be poor |
| Fast to implement | No query understanding |

---

### Pattern 2: Query Expansion RAG (Better)

```
BRD → LLM generates queries → Multiple searches → Merge results → LLM Prompt
```

**How it works:**
1. LLM analyzes BRD and generates targeted queries
   - "authentication patterns in system"
   - "user management API endpoints"
   - "database schema for users"
2. Run multiple searches
3. Deduplicate and rank results
4. Include in prompt

| Pros | Cons |
|------|------|
| Better recall | More LLM calls |
| Semantic understanding | Higher latency |

---

### Pattern 3: Agentic RAG (Advanced)

```
BRD → Retriever Agent → Decides what to search → Iterative retrieval → Synthesize → Planner
```

**How it works:**
1. Retriever Agent analyzes BRD
2. Decides what context is needed (APIs? Architecture? Conventions?)
3. Iteratively retrieves until satisfied
4. Synthesizes a "system context summary"
5. Passes to Planner Agent

| Pros | Cons |
|------|------|
| Highest quality | Complex |
| Adaptive | More latency |
| | Higher cost |

---

### 🎯 Recommendation

**Start with Pattern 2 (Query Expansion)**, then evolve to Pattern 3 if needed.

**Rationale:**
- Pattern 1 is too naive for complex BRDs
- Pattern 3 is overkill initially
- Pattern 2 gives 80% of the benefit with 40% of the complexity

---

## 🧰 Tool & Service Options

### 1. Vector Databases

| Option | Type | Pros | Cons | Best For |
|--------|------|------|------|----------|
| **ChromaDB** | Embedded | Zero setup, Python native, persistent | Limited scale | This project ✅ |
| **Qdrant** | Self-hosted/Cloud | Fast, rich filtering, Rust-based | More setup | Production |
| **Pinecone** | Managed | Fully managed, scales infinitely | Cost, vendor lock-in | Enterprise |
| **Weaviate** | Self-hosted/Cloud | GraphQL API, multi-modal | Complexity | Complex use cases |
| **LanceDB** | Embedded | Columnar, fast, serverless | Newer, less mature | Large datasets |
| **pgvector** | Postgres extension | Use existing DB, SQL familiar | Performance limits | Postgres shops |

**Suggestion:** **ChromaDB**
- Perfect for a local-first development project
- No external dependencies
- Easy to swap out later if needed
- Persistent storage included

---

### 2. Embedding Models

| Option | Type | Dimensions | Quality | Cost | Latency |
|--------|------|-----------|---------|------|---------|
| **Voyage AI** | API | 1024 | Excellent | $0.02/1M tokens | Low |
| **OpenAI ada-002** | API | 1536 | Good | $0.10/1M tokens | Low |
| **Cohere Embed v3** | API | 1024 | Very Good | $0.10/1M tokens | Low |
| **sentence-transformers** | Local | 384-768 | Good | Free | Medium |
| **Ollama (nomic-embed-text)** | Local | 768 | Good | Free | Medium |
| **BGE models (HuggingFace)** | Local | 1024 | Very Good | Free | Medium |

**Suggestion:** **Dual approach**
- **Development:** Ollama `nomic-embed-text` (free, local, good quality)
- **Production:** Voyage AI (best quality, reasonable cost)

This aligns with the Phase 2 goal of local LLM support via Ollama.

---

### 3. Document Loaders

| Document Type | Tool Options | Notes |
|---------------|--------------|-------|
| **Markdown** | Built-in, LangChain | Split by headers |
| **OpenAPI/Swagger** | `openapi-spec-validator`, custom parser | Extract endpoints, schemas |
| **Python code** | `ast` module, tree-sitter | Extract docstrings, signatures |
| **TypeScript/JS** | tree-sitter | Extract JSDoc, interfaces |
| **PDF** | pypdf (already have), unstructured | Architecture diagrams |
| **GitHub repos** | GitLoader (LangChain) | Clone and process |

**Suggestion:** Start with **Markdown + OpenAPI** - these give highest value for effort.

---

### 4. Chunking Strategies

| Strategy | How it Works | Best For |
|----------|--------------|----------|
| **Fixed size** | Split every N characters with overlap | General text |
| **Recursive** | Split by paragraphs, then sentences | Documents |
| **Semantic** | Use LLM to identify logical boundaries | High quality needs |
| **Code-aware** | Split by functions/classes | Source code |
| **Header-based** | Split by markdown headers | README/docs |

**Suggestion:** **Header-based for Markdown**, **Code-aware for source**, **Recursive for everything else**

---

## 🔄 Integration Approaches

### Approach A: Separate Ingestion & Query Services

```
┌─────────────────┐        ┌─────────────────┐
│  Ingestion CLI  │        │   BRD Workflow  │
│  (one-time)     │        │   (per request) │
└────────┬────────┘        └────────┬────────┘
         │                          │
         ▼                          ▼
┌─────────────────────────────────────────────┐
│              ChromaDB (shared)              │
└─────────────────────────────────────────────┘
```

| Pros | Cons |
|------|------|
| Clean separation | Manual sync when docs change |
| Ingestion happens once | |

---

### Approach B: On-Demand Ingestion

```
┌─────────────────┐        
│   BRD Workflow  │        
│   + Auto-ingest │        
└────────┬────────┘        
         │ Check if docs changed
         ▼
┌─────────────────────────────────────────────┐
│              ChromaDB (auto-updated)        │
└─────────────────────────────────────────────┘
```

| Pros | Cons |
|------|------|
| Always fresh | Slower first request |
| No manual steps | Complexity |

---

### Approach C: Hybrid (Recommended)

```
┌─────────────────┐        ┌─────────────────┐
│  Ingestion CLI  │        │  API Endpoint   │
│  (bulk/initial) │        │  (incremental)  │
└────────┬────────┘        └────────┬────────┘
         │                          │
         ▼                          ▼
┌─────────────────────────────────────────────┐
│              ChromaDB                        │
└─────────────────────────────────────────────┘
         ▲
         │
┌────────┴────────┐
│  BRD Workflow   │
│  (query only)   │
└─────────────────┘
```

**Suggestion:** **Approach C** - CLI for bulk ingestion, API for incremental updates, workflow for querying.

---

## 📊 Tradeoffs Summary

| Decision | Option A | Option B | Recommendation |
|----------|----------|----------|----------------|
| **Vector DB** | ChromaDB (local) | Qdrant (cloud) | **ChromaDB** - simplicity |
| **Embeddings** | Voyage (API) | Ollama (local) | **Both** - dev/prod split |
| **RAG Pattern** | Naive | Query Expansion | **Query Expansion** |
| **Ingestion** | CLI only | On-demand | **Hybrid** |
| **Chunking** | Fixed size | Semantic | **Header-based + Recursive** |

---

## ⚠️ Risks and Mitigations

### 1. Context Window Limits

**Risk:** Claude 3.5 Sonnet has 200K tokens, but prompts are already large with BRD + schema

**Mitigation:** Smart summarization of retrieved context

---

### 2. Retrieval Quality

**Risk:** Wrong context = wrong plans

**Mitigation:** Query expansion, re-ranking, human feedback loop

---

### 3. Stale Documentation

**Risk:** If docs are outdated, plans will be too

**Mitigation:** Timestamps on chunks, freshness checks

---

### 4. Cold Start Problem

**Risk:** New users have no documentation ingested

**Mitigation:** Graceful degradation (works without RAG), sample docs

---

### 5. Embedding Drift

**Risk:** If you change embedding model, need to re-embed everything

**Mitigation:** Store embedding model version in metadata

---

## 🎯 Recommended Starting Configuration

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Vector DB | ChromaDB | No setup, persistent, Python native |
| Embeddings | Ollama `nomic-embed-text` | Free, local, aligns with Phase 2 |
| RAG Pattern | Query Expansion | Good quality without complexity |
| Doc Types | Markdown + OpenAPI | Highest value, easiest to parse |
| Ingestion | CLI command | Simple, explicit control |
| Workflow | New RetrieverAgent node | Clean integration with existing pipeline |

---

## 🔍 Pre-Implementation Questions

Before implementation, consider:

1. **What documentation do you have?**
   - API specs (OpenAPI/Swagger)?
   - Architecture docs (Markdown, Confluence)?
   - Code with docstrings?
   - ADRs (Architecture Decision Records)?

2. **How often do docs change?**
   - Rarely → CLI ingestion is fine
   - Frequently → Need auto-sync

3. **Local-first or cloud-ok?**
   - If local-first → Ollama embeddings + ChromaDB
   - If cloud-ok → Voyage + optional managed vector DB

4. **Single project or multi-tenant?**
   - Single → One collection
   - Multi → Collection per project

5. **What's the priority?**
   - Speed to MVP → Naive RAG with ChromaDB
   - Quality focus → Query Expansion with good embeddings

---

## 📚 References

- [ChromaDB Documentation](https://docs.trychroma.com/)
- [LangChain RAG Guide](https://python.langchain.com/docs/tutorials/rag/)
- [Voyage AI Embeddings](https://docs.voyageai.com/)
- [Ollama Embedding Models](https://ollama.ai/library)
- [RAG Best Practices](https://www.anthropic.com/news/contextual-retrieval)

---

## Next Steps

1. Answer pre-implementation questions
2. Set up ChromaDB with Ollama embeddings
3. Implement document loaders (Markdown first)
4. Create ingestion CLI
5. Add RetrieverAgent to workflow
6. Update Planner prompt to use retrieved context
7. Test with sample project documentation

