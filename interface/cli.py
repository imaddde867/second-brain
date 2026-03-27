import typer
from rich.console import Console
from rich.panel import Panel
from pathlib import Path
from ingestion.parser import parse_markdown
from graph.store import BrainStore
from query.engine import QueryEngine

app = typer.Typer()
console = Console()
store = BrainStore()
engine = QueryEngine(store)

@app.command()
def index(vault: str = typer.Argument("~/Documents/imad-brain")):
    vault_path = Path(vault).expanduser()
    files = list(vault_path.rglob("*.md"))
    console.print(f"[bold]Indexing {len(files)} notes...[/bold]")
    for f in files:
        if any(skip in str(f) for skip in ["00-inbox", "06-templates"]):
            continue
        note = parse_markdown(f)
        embedding = engine.embed(note.content[:1000])
        store.upsert_note(note, embedding)
        console.print(f"  [green]✓[/green] {note.title}")
    console.print("[bold green]Done.[/bold green]")

@app.command()
def ask(question: str):
    console.print(Panel(f"[bold]{question}[/bold]", title="Question"))
    answer = engine.ask(question)
    console.print(Panel(answer, title="Answer", border_style="green"))

@app.command()
def search(query: str):
    results = engine.search(query, top_k=5)
    for r in results:
        console.print(f"[bold]{r['title']}[/bold]")
        console.print(f"  [dim]{r['path']}[/dim]")
        console.print(f"  {r['content'][:120]}...\n")

if __name__ == "__main__":
    app()
