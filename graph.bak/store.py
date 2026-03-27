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
        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS Note (
                id STRING, title STRING, path STRING,
                checksum STRING, tags STRING,
                PRIMARY KEY (id)
            )
        """)
        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS Tag (
                name STRING, PRIMARY KEY (name)
            )
        """)
        self.conn.execute("""
            CREATE NODE TABLE IF NOT EXISTS Entity (
                name STRING, PRIMARY KEY (name)
            )
        """)
        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS TAGGED (FROM Note TO Tag)
        """)
        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS LINKS_TO (FROM Note TO Entity)
        """)
        self.conn.execute("""
            CREATE REL TABLE IF NOT EXISTS RELATED_TO (FROM Note TO Note, weight DOUBLE)
        """)

    def upsert_note(self, note: ParsedNote, embedding: list[float]):
        note_id = note.checksum
        self.conn.execute("""
            MERGE (n:Note {id: $id})
            SET n.title = $title, n.path = $path,
                n.checksum = $checksum, n.tags = $tags
        """, {"id": note_id, "title": note.title, "path": note.path,
              "checksum": note.checksum, "tags": ",".join(note.tags)})

        for tag in note.tags:
            self.conn.execute("MERGE (t:Tag {name: $name})", {"name": tag})
            self.conn.execute("""
                MERGE (n:Note {id: $nid})-[:TAGGED]->(t:Tag {name: $tname})
            """, {"nid": note_id, "tname": tag})

        for link in note.links:
            self.conn.execute("MERGE (e:Entity {name: $name})", {"name": link})
            self.conn.execute("""
                MERGE (n:Note {id: $nid})-[:LINKS_TO]->(e:Entity {name: $ename})
            """, {"nid": note_id, "ename": link})

        self.collection.upsert(
            ids=[note_id],
            embeddings=[embedding],
            documents=[note.content[:2000]],
            metadatas=[{"title": note.title, "path": note.path,
                       "tags": ",".join(note.tags)}]
        )
