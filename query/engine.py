import re
import ollama
from graph.store import BrainStore


class QueryEngine:
    def __init__(self, store: BrainStore, model: str = "llama3.2"):
        self.store = store
        self.model = model
        self.embed_model = "nomic-embed-text"

    def embed(self, text: str) -> list[float]:
        response = ollama.embeddings(model=self.embed_model, prompt=text)
        return response["embedding"]

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        embedding = self.embed(query)
        results = self.store.collection.query(
            query_embeddings=[embedding], n_results=top_k
        )
        if not results["metadatas"] or not results["metadatas"][0]:
            return []
        return [
            {
                "title": m["title"],
                "path": m["path"],
                "content": d,
                "tags": m.get("tags", ""),
            }
            for m, d in zip(results["metadatas"][0], results["documents"][0])
        ]

    def ask(self, question: str) -> str:
        # Vector search for semantic matches
        context_notes = self.search(question, top_k=5)

        # Extract [[entities]] or keywords to pull graph context
        entities = re.findall(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b", question)
        graph_notes = []
        for entity in entities[:3]:
            graph_notes.extend(self.store.get_graph_context(entity))

        # Combine and deduplicate
        seen_titles = {n["title"] for n in context_notes}
        for gn in graph_notes:
            if gn["title"] not in seen_titles:
                context_notes.append({
                    "title": gn["title"],
                    "path": gn["path"],
                    "content": f"[graph-linked via entity, tags: {gn.get('tags', '')}]",
                    "tags": gn.get("tags", ""),
                })
                seen_titles.add(gn["title"])

        if not context_notes:
            return "No relevant notes found in your vault."

        context = "\n\n---\n\n".join(
            f"# {n['title']}\nPath: {n['path']}\nTags: {n.get('tags', '')}\n\n{n['content'][:800]}"
            for n in context_notes
        )

        prompt = f"""You are a personal knowledge assistant for Imad's local vault.
Answer the question using ONLY the notes below.
Be specific — cite note titles when possible.
If the answer isn't in the notes, say so honestly.

NOTES:
{context}

QUESTION: {question}

ANSWER:"""

        response = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response["message"]["content"]
