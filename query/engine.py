import re
import ollama
from graph.store import BrainStore


# Questions that don't need RAG context
GREETING_PATTERNS = [
    r"^(hi|hello|hey|sup|yo|hola|salut|salam)[\s!?.]*$",
    r"^(who are you|what are you|what is this|what do you do)[\s?]*$",
    r"^(help|how does this work)[\s?]*$",
]

IDENTITY_RESPONSE = (
    "I'm Cortex — your local AI second brain. I index your Obsidian vault "
    "into a knowledge graph and let you query it with natural language. "
    "Everything runs locally on your machine. No cloud, no API keys.\n\n"
    "Try asking me things like:\n"
    "- \"What projects am I working on?\"\n"
    "- \"Find everything about ADINO\"\n"
    "- \"What ideas do I have for side projects?\"\n"
    "- \"Summarize my thesis work\""
)

GREETING_RESPONSE = (
    "Hey! I'm Cortex, your local knowledge assistant. "
    "Ask me anything about your vault — projects, notes, ideas, whatever you've written down."
)


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

    def _is_meta_question(self, question: str) -> str | None:
        """Check if the question is a greeting or identity question."""
        q = question.strip().lower()
        for pattern in GREETING_PATTERNS:
            if re.match(pattern, q):
                if "who" in q or "what" in q:
                    return IDENTITY_RESPONSE
                return GREETING_RESPONSE
        return None

    def ask(self, question: str) -> str:
        # Handle greetings and meta-questions without RAG
        meta = self._is_meta_question(question)
        if meta:
            return meta

        # Vector search for semantic matches
        context_notes = self.search(question, top_k=5)

        # Extract potential entities to pull graph context
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
            return "I couldn't find anything relevant in your vault for that question. Try rephrasing, or check that the relevant notes are indexed."

        context = "\n\n---\n\n".join(
            f"# {n['title']}\nPath: {n['path']}\nTags: {n.get('tags', '')}\n\n{n['content'][:800]}"
            for n in context_notes
        )

        prompt = f"""You are Cortex, a local AI knowledge assistant. You help the user explore and understand THEIR notes and knowledge vault.

CRITICAL RULES:
- You are NOT the user. You are NOT any project mentioned in the notes. You are Cortex.
- The notes below were WRITTEN BY the user. When they ask "what am I working on?", summarize what THEIR notes say.
- Refer to the user as "you" — e.g. "You're working on..." or "Your notes mention..."
- Cite note titles when referencing specific information — e.g. "According to your note 'IAOP Architecture Vision'..."
- If the notes don't contain the answer, say so honestly. Don't make things up.
- Be concise and direct. No filler. No corporate speak.
- NEVER role-play as the user or as any system/project described in the notes.

NOTES FROM THE USER'S VAULT:
{context}

USER'S QUESTION: {question}

ANSWER:"""

        response = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response["message"]["content"]
