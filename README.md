# Second Brain

Local AI second brain — your notes, code, and knowledge in a private, queryable knowledge graph powered by LLMs.

> Obsidian + Kuzu + Ollama, stitched together so you don't have to.

## What it does

- **Indexes** your Obsidian vault (markdown, tags, `[[wiki-links]]`, frontmatter)
- **Embeds** content locally via `nomic-embed-text` through Ollama
- **Builds a knowledge graph** in Kuzu (notes → tags → entities → relationships)
- **Semantic search** across your entire vault via ChromaDB
- **Ask questions** in natural language, answered by a local LLM using your notes as context
- **Watches** your vault for changes and re-indexes automatically

Everything runs locally. No cloud. No API keys. No one reads your stuff.

## Quick start

```bash
# Clone and setup
git clone https://github.com/yourusername/second-brain.git
cd second-brain
python3 -m venv .venv && source .venv/bin/activate
pip install -e .

# Pull required Ollama models
ollama pull llama3.2
ollama pull nomic-embed-text

# Index your vault
brain index ~/Documents/imad-brain

# Ask questions
brain ask "What was I working on last week?"
brain search "NATS messaging architecture"
brain stats

# Watch for live changes
brain watch ~/Documents/imad-brain
```

## Architecture

```
Obsidian vault (markdown files)
       │
       ▼
   [Parser] ── extracts tags, [[links]], frontmatter, content
       │
       ├──▶ [ChromaDB] ── vector embeddings (nomic-embed-text via Ollama)
       │
       └──▶ [Kuzu Graph] ── Note → Tag, Note → Entity relationships
                │
                ▼
         [Query Engine] ── combines vector search + graph traversal
                │
                ▼
           [Local LLM] ── answers questions using your notes as context
```

## Commands

| Command | Description |
|---------|-------------|
| `brain index <vault>` | Index all markdown files |
| `brain ask "<question>"` | Ask a question about your notes |
| `brain search "<query>"` | Semantic search across notes |
| `brain stats` | Show graph statistics |
| `brain watch <vault>` | Watch vault and re-index on changes |

## Tech stack

- **Kuzu** — embedded graph database (like SQLite for graphs)
- **ChromaDB** — local vector store
- **Ollama** — local LLM inference (`llama3.2` + `nomic-embed-text`)
- **Python** — ingestion, parsing, query engine
- **Typer + Rich** — CLI interface

## Roadmap

- [ ] Phase 1: Obsidian markdown indexing (✅ current)
- [ ] Phase 2: Git repos, PDFs, calendar (ICS), email
- [ ] Phase 3: Web UI (React or Textual TUI)
- [ ] Phase 4: One-command install, demo video, launch

## License

MIT
