<p align="center">
  <img src="https://img.shields.io/badge/status-alpha-c9953c?style=flat-square" />
  <img src="https://img.shields.io/badge/python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" />
  <img src="https://img.shields.io/badge/runs-100%25_local-black?style=flat-square" />
</p>

<h1 align="center">◈ CORTEX</h1>
<p align="center"><strong>Your notes. Your code. Your knowledge. One local AI that reasons across all of it.</strong></p>

<p align="center">
  <em>Obsidian + Kuzu + Ollama, stitched together so you don't have to.</em>
</p>

---

> **Cortex** is a fully local, graph-native AI second brain. It indexes your Obsidian vault into a knowledge graph, embeds everything into a vector store, and lets you query your entire digital life in natural language — without anything ever leaving your machine.

No cloud. No API keys. No subscriptions. No one reads your stuff.

---

## The Problem

Every tool that tries to be your "second brain" makes the same mistake: they treat your knowledge like a flat document collection.

| Tool | What it does | Why it falls short |
|---|---|---|
| Obsidian + plugins | Markdown files + keyword search | No semantic search, no code/email/calendar |
| Notion AI | Cloud docs + GPT | Your data trains their model. No graph. No offline. |
| Mem | Auto-tagging notes | Cloud-only, single data type, no relationships |
| Rewind / Recall | Screen recording + OCR | Privacy nightmare, $20/mo, no reasoning |
| LlamaIndex / LangChain | RAG libraries for devs | No product layer. No graph. No UX. |

None of them combine **local inference + graph structure + multi-source ingestion + conversational query + zero cloud dependency**.

That combination is Cortex.

---

## What It Does Today

Point Cortex at your Obsidian vault. It parses every note — frontmatter, tags, `[[wiki-links]]`, content — and builds two things simultaneously:

1. **A knowledge graph** (Kuzu) — notes become nodes, tags become edges, `[[linked entities]]` become traversable relationships
2. **A vector store** (ChromaDB) — every note gets embedded locally via `nomic-embed-text` through Ollama

Then you ask questions in natural language. Cortex combines **semantic vector search** with **graph traversal** to find relevant notes, feeds them to a local LLM, and gives you a grounded answer with source citations.

```
You: "What projects am I working on?"

Cortex: Based on your notes, you're actively working on several projects:

  - **IAOP** — an Industrial AI Orchestration Platform with a five-layer
    modular architecture, targeting on-premises deployment.
    (source: IAOP Architecture Vision)

  - **ADINO** — a collaborative project between Centria and TUAS.
    (source: ADINO Project Plan Centria TUAS)

  - **Kage** — a fully local personal AI voice assistant for macOS.
    (source: Kage Voice Assistant)
```

Everything happens on your machine. The LLM never sees the internet. Your notes never leave your disk.

---

## Quick Start

```bash
# Clone
git clone https://github.com/imadeddineF/cortex.git
cd cortex

# Setup
python3 -m venv .venv && source .venv/bin/activate
pip install -e .

# Pull the models (one-time, ~2.3GB total)
ollama pull llama3.2
ollama pull nomic-embed-text

# Index your vault
brain index ~/path/to/your/obsidian-vault

# Ask questions
brain ask "What was I working on last week?"
brain search "machine learning architecture"
brain stats
```

### Web UI

```bash
# Start the API server
uvicorn api.server:app --reload --port 8000

# Open the web interface
open http://localhost:5173   # or wherever your frontend dev server runs
```

<!-- TODO: Add screenshot/GIF here -->

---

## Architecture

```
  Obsidian Vault (markdown files)
         │
         ▼
    ┌─────────┐
    │ Parser  │── extracts tags, [[links]], frontmatter, content
    └────┬────┘
         │
    ┌────┴────────────────────────┐
    │                             │
    ▼                             ▼
┌──────────┐              ┌─────────────┐
│ ChromaDB │              │  Kuzu Graph │
│ (vectors)│              │  (nodes +   │
│          │              │   edges)    │
└────┬─────┘              └──────┬──────┘
     │                           │
     └───────────┬───────────────┘
                 │
                 ▼
         ┌──────────────┐
         │ Query Engine │── hybrid: vector similarity + graph traversal
         └──────┬───────┘
                │
                ▼
          ┌───────────┐
          │ Local LLM │── grounded answers with source citations
          └───────────┘
```

---

## Tech Stack

| Layer | Tech | Why |
|---|---|---|
| Knowledge graph | **Kuzu** | Embedded graph DB — like SQLite for graphs. No server, no Docker. Runs inside your Python process. |
| Vector store | **ChromaDB** | Local persistent vector store. Zero config. |
| Embeddings | **nomic-embed-text** via Ollama | 768-dim, runs locally in ~5ms/chunk, outperforms ada-002 on retrieval benchmarks. MIT license. |
| LLM | **llama3.2** via Ollama | Fast local inference. Swappable — use any model Ollama supports. |
| Parser | Custom Python | Handles YAML frontmatter, nested tags, `[[wiki-links]]`, inline tags. |
| File watching | **watchdog** | OS-native file events. Zero polling. Live re-indexing as you edit. |
| API | **FastAPI** | REST endpoints for the web UI. |
| CLI | **Typer + Rich** | Beautiful terminal interface. |

---

## CLI Commands

| Command | Description |
|---|---|
| `brain index <vault>` | Index all markdown files in your vault |
| `brain ask "<question>"` | Ask a natural language question |
| `brain search "<query>"` | Semantic vector search |
| `brain stats` | Show graph statistics (nodes, edges, counts) |
| `brain watch <vault>` | Watch vault for changes, re-index live |

---

## Current Status

Cortex is in **alpha**. The core pipeline works end-to-end:

- [x] Obsidian markdown ingestion (frontmatter, tags, wiki-links)
- [x] Local embeddings via Ollama (nomic-embed-text)
- [x] Knowledge graph in Kuzu (Note → Tag, Note → Entity edges)
- [x] Vector store in ChromaDB
- [x] Hybrid query engine (vector search + graph traversal)
- [x] LLM-powered answers with source citations
- [x] CLI interface (index, ask, search, stats, watch)
- [x] FastAPI REST server
- [x] Web chat UI with graph stats sidebar

---

## Roadmap

### Phase 2 — Multi-source ingestion
- [ ] **Code ingestor** — tree-sitter AST parsing for Python/JS/TS (functions, classes, imports as graph nodes)
- [ ] **PDF ingestor** — OCR + structured extraction for papers and docs
- [ ] **Email ingestor** — mbox/maildir/eml parsing, people as Person nodes
- [ ] **Calendar ingestor** — ICS files, events linked to topics and people
- [ ] **Git log ingestor** — commit messages, branches, file change history

### Phase 3 — Intelligence layer
- [ ] **LanceDB migration** — hybrid vector + full-text search in one query
- [ ] **spaCy NER** — automatic entity extraction (people, orgs, dates, locations)
- [ ] **LLM relation extraction** — deep relationship mining on important docs
- [ ] **Smart chunking** — semantic paragraph splitting instead of character truncation
- [ ] **Cross-source reasoning** — traverse edges across source types (note → code → email → meeting)

### Phase 4 — Proactive intelligence
- [ ] **Pre-meeting context** — daemon that surfaces relevant notes before calendar events
- [ ] **Knowledge decay** — surface notes you haven't revisited that might be worth a look
- [ ] **Idea graveyard** — find notes that never evolved into action
- [ ] **Daily briefing** — morning summary of what's relevant today

### Phase 5 — Community + polish
- [ ] **Plugin interface** — abstract `Ingestor` base class for community connectors
- [ ] **Obsidian plugin** — Cortex inside your vault sidebar
- [ ] **VS Code extension** — Cortex inside your editor
- [ ] **One-command install** — `pip install cortex-ai` or `docker-compose up`
- [ ] **Demo video + launch** — r/LocalLLaMA, HackerNews, X

---

## Project Structure

```
cortex/
├── ingestion/
│   ├── parser.py          # markdown parser (frontmatter, tags, links)
│   └── watcher.py         # watchdog-based live file sync
├── graph/
│   └── store.py           # Kuzu graph + ChromaDB vector store
├── query/
│   └── engine.py          # hybrid retrieval + LLM answer generation
├── interface/
│   └── cli.py             # Typer CLI (index, ask, search, stats, watch)
├── api/
│   └── server.py          # FastAPI REST endpoints
├── tests/
├── ui/                    # React web interface
├── pyproject.toml
└── README.md
```

---

## Why "Cortex"

Your brain's cortex is where reasoning happens — where scattered signals become coherent thought. That's what this does for your digital life. Scattered notes, code, papers, and ideas become a single queryable intelligence layer.

---

## Contributing

Cortex is early. If you're interested in local-first AI, knowledge graphs, or building tools that respect user privacy — contributions are welcome.

The biggest impact areas right now:
1. **New ingestors** — PDF, code (tree-sitter), email, calendar
2. **Query quality** — better chunking, re-ranking, prompt engineering
3. **Graph enrichment** — smarter entity extraction, relationship mining
4. **Testing** — the test suite is empty. Help.

---

## License

MIT — do whatever you want with it.

---

<p align="center">
  <em>Built by <a href="https://imadlab.com">Imad Eddine El Mouss</a></em><br/>
  <sub>Because your knowledge deserves better than keyword search.</sub>
</p>
