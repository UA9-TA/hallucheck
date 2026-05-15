from typing import Dict, List

from rich.console import Console
from rich.panel import Panel

from .validator import Hallucination

console = Console()


def display_report(
    hallucinations: List[Hallucination], files_checked: int, total_symbols: int, total_files: int
):
    console.print("\n[bold]HalluCheck — Hallucination Report[/bold]")
    console.print("──────────────────────────────────────────────────")

    console.print(f"✦ Files checked       {files_checked} files in last commit")
    console.print(f"✦ Index size          {total_symbols} symbols across {total_files} files\n")

    if not hallucinations:
        console.print("[green]✓ No hallucinations found![/green]")
        console.print("──────────────────────────────────────────────────")
        return

    # Group by file
    by_file: Dict[str, List[Hallucination]] = {}
    for h in hallucinations:
        if h.file not in by_file:
            by_file[h.file] = []
        by_file[h.file].append(h)

    for file, items in by_file.items():
        console.print(f"  [bold]{file}[/bold]")
        for h in items:
            console.print(f"  [red]✗[/red] Line {h.line:<4}   [white]{h.reference}[/white]")
            console.print(f"              → {h.message}")
            if h.suggestions:
                suggestions_str = " or ".join(h.suggestions)
                console.print(f"              → Did you mean: [cyan]{suggestions_str}[/cyan]?")
            console.print()

    files_with_hallucinations = len(by_file)
    console.print(
        f"✦ {len(hallucinations)} hallucinations found in {files_with_hallucinations} files"
    )
    console.print("✦ Run `hallucheck explain` for AI-powered fix suggestions")
    console.print("──────────────────────────────────────────────────")


def display_explanation(explanation: str):
    console.print(Panel(explanation, title="Claude Explanation", border_style="blue"))
