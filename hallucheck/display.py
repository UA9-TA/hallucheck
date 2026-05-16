from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


def print_report(hallucinations, files_checked, index_size_symbols, index_size_files):
    console.print()
    console.print(Text("HalluCheck — Hallucination Report", style="bold cyan"))
    console.print("─" * 50)

    console.print(f"✦ Files checked       {files_checked} files")
    console.print(
        f"✦ Index size          {index_size_symbols} symbols across {index_size_files} files"
    )
    console.print()

    if not hallucinations:
        console.print(Text("✦ No hallucinations found! 🎉", style="bold green"))
        console.print("─" * 50)
        return

    # Group by file
    by_file = {}
    for h in hallucinations:
        if h.file not in by_file:
            by_file[h.file] = []
        by_file[h.file].append(h)

    for file, items in by_file.items():
        console.print(f"  [bold]{file}[/bold]")
        for item in items:
            sugg_str = ", ".join(item.suggestions)
            console.print(f"  [red]✗ Line {item.line}[/red]   {item.reference}")
            console.print(f"              → {item.message}")
            if item.suggestions:
                console.print(f"              → Did you mean: [cyan]{sugg_str}[/cyan]?")
            console.print()

    num_files = len(by_file)
    num_hallucinations = len(hallucinations)

    console.print(
        f"✦ {num_hallucinations} hallucinations found in {num_files} files", style="bold yellow"
    )
    console.print("✦ Run `hallucheck explain <file:line>` for AI-powered fix suggestions")
    console.print("─" * 50)
    console.print()


def print_explanation(text):
    panel = Panel(text, title="Claude's Explanation", border_style="cyan")
    console.print(panel)
