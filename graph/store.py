import kuzu
import chromadb
from pathlib import Path
from ingestion.parser import ParsedNote


class BrainStore:
    def __init__(self, data_dir: str = "./data"):
        Path(data_dir).mkdir(exist_ok=True)
        self.db = kuzu.Database(f"{data_dir}/graph.kuzu")
        self.conn = kuzu.Connection(self.db)
        self.chroma = chromadb.PersistentClient(path=f"{data_dir}/chroma")
        self.collection = self.chroma.get_or_create_collection("notes")
        self._init_schema()

    def _init_schema(self):
        tables = [
            """CREATE NODE TABLE IF NOT EXISTS Note (
                id STRING, title STRING, path STRING,
                checksum STRING, tags STRING,
                PRIMARY KEY (id)
            )""",
            """CREATE NODE TABLE IF NOT EXISTS Tag (
                name STRING, PRIMARY KEY (name)
            )""",
            """CREATE NODE TABLE IF NOT EXISTS Entity (
                name STRING, PRIMARY KEY (name)
            )""",
            """CREATE REL TABLE IF NOT EXISTS TAGGED (FROM Note TO Tag)""",
            """CREATE REL TABLE IF NOT EXISTS LINKS_TO (FROM Note TO Entity)""",
            """CREATE REL TABLE IF NOT EXISTS RELATED_TO (FROM Note TO Note, weight DOUBLE)""",
        ]
        for ddl in tables:
            self.conn.execute(ddl)

    def upsert_note(self, note: ParsedNote, embedding: list[float]):
        note_id = note.checksum

        # Upsert the note node
        self.conn.execute("""
            MERGE (n:Note {id: $id})
            SET n.title = $title, n.path = $path,
                n.checksum = $checksum, n.tags = $tags
        """, {
            "id": note_id, "title": note.title, "path": note.path,
            "checksum": note.checksum, "tags": ",".join(note.tags),
        })

        # Clear old relationships for this note so re-indexing is clean
        self.conn.execute(
            "MATCH (n:Note {id: $id})-[r:TAGGED]->() DELETE r",
            {"id": note_id},
        )
        self.conn.execute(
            "MATCH (n:Note {id: $id})-[r:LINKS_TO]->() DELETE r",
            {"id": note_id},
        )

        # Create tag nodes + relationships
        for tag in note.tags:
            self.conn.execute(
                "MERGE (t:Tag {name: $name})", {"name": tag}
            )
            self.conn.execute("""
                MATCH (n:Note {id: $nid}), (t:Tag {name: $tname})
                CREATE (n)-[:TAGGED]->(t)
            """, {"nid": note_id, "tname": tag})

        # Create entity nodes + relationships
        for link in note.links:
            self.conn.execute(
                "MERGE (e:Entity {name: $name})", {"name": link}
            )
            self.conn.execute("""
                MATCH (n:Note {id: $nid}), (e:Entity {name: $ename})
                CREATE (n)-[:LINKS_TO]->(e)
            """, {"nid": note_id, "ename": link})

        # Upsert into ChromaDB for vector search
        self.collection.upsert(
            ids=[note_id],
            embeddings=[embedding],
            documents=[note.content[:2000]],
            metadatas=[{
                "title": note.title,
                "path": note.path,
                "tags": ",".join(note.tags),
            }],
        )

    def get_graph_context(self, entity_name: str) -> list[dict]:
        """Find notes connected to a given entity via the graph."""
        try:
            result = self.conn.execute("""
                MATCH (n:Note)-[:LINKS_TO]->(e:Entity {name: $name})
                RETURN n.title, n.path, n.tags
            """, {"name": entity_name})
            return [
                {"title": row[0], "path": row[1], "tags": row[2]}
                for row in result.get_as_df().itertuples(index=False)
            ]
        except Exception:
            return []

    def get_related_by_tag(self, tag: str) -> list[dict]:
        """Find all notes with a given tag via the graph."""
        try:
            result = self.conn.execute("""
                MATCH (n:Note)-[:TAGGED]->(t:Tag {name: $name})
                RETURN n.title, n.path, n.id
            """, {"name": tag})
            return [
                {"title": row[0], "path": row[1], "id": row[2]}
                for row in result.get_as_df().itertuples(index=False)
            ]
        except Exception:
            return []
