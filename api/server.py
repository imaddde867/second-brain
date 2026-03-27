"""Cortex API — FastAPI server exposing search, ask, and stats endpoints."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from graph.store import BrainStore
from query.engine import QueryEngine

app = FastAPI(title="Cortex", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

store = BrainStore()
engine = QueryEngine(store)


class AskRequest(BaseModel):
    question: str


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


@app.post("/api/ask")
def ask(req: AskRequest):
    answer = engine.ask(req.question)
    sources = engine.search(req.question, top_k=3)
    return {
        "answer": answer,
        "sources": [
            {"title": s["title"], "path": s["path"], "tags": s.get("tags", "")}
            for s in sources
        ],
    }


@app.post("/api/search")
def search(req: SearchRequest):
    results = engine.search(req.query, top_k=req.top_k)
    return {
        "results": [
            {
                "title": r["title"],
                "path": r["path"],
                "tags": r.get("tags", ""),
                "snippet": r["content"][:200],
            }
            for r in results
        ]
    }


@app.get("/api/stats")
def stats():
    counts = {}
    for label, query in [
        ("notes", "MATCH (n:Note) RETURN count(n)"),
        ("tags", "MATCH (t:Tag) RETURN count(t)"),
        ("entities", "MATCH (e:Entity) RETURN count(e)"),
        ("tag_links", "MATCH ()-[r:TAGGED]->() RETURN count(r)"),
        ("entity_links", "MATCH ()-[r:LINKS_TO]->() RETURN count(r)"),
    ]:
        try:
            result = store.conn.execute(query)
            counts[label] = result.get_next()[0]
        except Exception:
            counts[label] = 0
    return counts


@app.get("/api/graph/entities")
def list_entities():
    """Return all entities in the graph for visualization."""
    try:
        result = store.conn.execute(
            "MATCH (e:Entity) RETURN e.name ORDER BY e.name"
        )
        return {"entities": [row[0] for row in result.get_as_df().itertuples(index=False)]}
    except Exception:
        return {"entities": []}


@app.get("/api/graph/tags")
def list_tags():
    """Return all tags with note counts."""
    try:
        result = store.conn.execute("""
            MATCH (t:Tag)<-[:TAGGED]-(n:Note)
            RETURN t.name, count(n) AS cnt
            ORDER BY cnt DESC
        """)
        return {
            "tags": [
                {"name": row[0], "count": row[1]}
                for row in result.get_as_df().itertuples(index=False)
            ]
        }
    except Exception:
        return {"tags": []}
