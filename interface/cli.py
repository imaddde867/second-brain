import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from pathlib import Path
from ingestion.parser import parse_markdown
from graph.store import BrainStore
from query.engine import QueryEngine

app = typer.Typer(help="Local AI second brain — query your Obsidian vault.")
console = Console()


def _get_store_and_engine():
    store = BrainStore()
    engine = QueryEngine(store)
    return store, engine


@app.command()
def index(vault: str = typer.Argument("~/Documents/imad-brain")):
    """Index all markdown files in your Obsidian vault."""
    store, engine = _get_store_and_engine()
    vault_path = Path(vault).expanduser()
    if not vault_path.exists():
        console.print(f"[red]Vault not found:[/red] {vault_path}")
        raise typer.Exit(1)

    skip_dirs = {"00-inbox", "06-templates", ".obsidian", ".trash"}
    files = [
        f for f in vault_path.rglob("*.md")
        if not any(s in f.parts for s in skip_dirs)
    ]

    console.print(f"[bold]Indexing {len(files)} notes...[/bold]")
    indexed, errors = 0, 0
    for f in files:
        try:
            note = parse_markdown(f)
            if not note.content.strip():
                continue
            embedding = engine.embed(note.content[:1000])
            store.upsert_note(note, embedding)
            console.print(f"  [green]✓[/green] {note.title}")
            indexed += 1
        except Exception as e:
            console.print(f"  [red]✗[/red] {f.name}: {e}")
            errors += 1

    console.print(f"\n[bold green]Done.[/bold green] {indexed} indexed, {errors} errors.")


@app.command()
def ask(
    question: str,
    model: str | None = typer.Option(
        None,
        "--model",
        help="Override the chat model for this request (e.g., qwen2.5:7b).",
    ),
):
    """Ask a question about your notes."""
    _, engine = _get_store_and_engine()
    console.print(Panel(f"[bold]{question}[/bold]", title="Question"))
    answer, model_used = engine.ask_with_model(question, model=model)
    console.print(Panel(answer, title="Answer", border_style="green"))
    console.print(f"[dim]Model used: {model_used}[/dim]")


@app.command()
def search(query: str, top_k: int = 5):
    """Semantic search across your notes."""
    _, engine = _get_store_and_engine()
    results = engine.search(query, top_k=top_k)
    if not results:
        console.print("[yellow]No results found.[/yellow]")
        return
    for r in results:
        console.print(f"[bold]{r['title']}[/bold]")
        console.print(f"  [dim]{r['path']}[/dim]")
        console.print(f"  {r['content'][:120]}...\n")


@app.command()
def stats():
    """Show vault statistics from the graph."""
    store, _ = _get_store_and_engine()
    table = Table(title="Vault Graph Stats")
    table.add_column("Metric", style="bold")
    table.add_column("Count", justify="right")

    try:
        for label, query in [
            ("Notes", "MATCH (n:Note) RETURN count(n)"),
            ("Tags", "MATCH (t:Tag) RETURN count(t)"),
            ("Entities", "MATCH (e:Entity) RETURN count(e)"),
            ("Tag links", "MATCH ()-[r:TAGGED]->() RETURN count(r)"),
            ("Entity links", "MATCH ()-[r:LINKS_TO]->() RETURN count(r)"),
        ]:
            result = store.conn.execute(query)
            count = result.get_next()[0]
            table.add_row(label, str(count))
    except Exception as e:
        console.print(f"[red]Error reading graph:[/red] {e}")
        return

    console.print(table)


@app.command()
def watch(vault: str = typer.Argument("~/Documents/imad-brain")):
    """Watch vault for changes and re-index automatically."""
    store, engine = _get_store_and_engine()
    vault_path = Path(vault).expanduser()

    def on_change(path: Path, event_type: str):
        try:
            note = parse_markdown(path)
            if not note.content.strip():
                return
            embedding = engine.embed(note.content[:1000])
            store.upsert_note(note, embedding)
            console.print(f"  [green]↻[/green] {event_type}: {note.title}")
        except Exception as e:
            console.print(f"  [red]✗[/red] {path.name}: {e}")

    from ingestion.watcher import watch_vault
    console.print(f"[bold]Watching[/bold] {vault_path} for changes... (Ctrl+C to stop)")
    watch_vault(str(vault_path), on_change)


if __name__ == "__main__":
    app()
