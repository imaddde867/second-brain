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
        return [
            {"title": m["title"], "path": m["path"],
             "content": d, "tags": m["tags"]}
            for m, d in zip(
                results["metadatas"][0], results["documents"][0]
            )
        ]

    def ask(self, question: str) -> str:
        context_notes = self.search(question, top_k=5)
        context = "\n\n---\n\n".join(
            f"# {n['title']}\n{n['content'][:800]}"
            for n in context_notes
        )
        prompt = f"""You are a personal knowledge assistant.
Answer the question using ONLY the notes below.
If the answer isn't in the notes, say so.

NOTES:
{context}

QUESTION: {question}

ANSWER:"""
        response = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response["message"]["content"]
