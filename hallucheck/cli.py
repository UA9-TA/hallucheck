import os
import sys
from pathlib import Path
from typing import Optional

import typer

from .config import save_config
from .diff_parser import get_added_lines
from .display import console, display_explanation, display_report
from .explainer import explain_hallucination
from .indexer import build_index, get_or_build_index, save_index
from .reference_extractor import extract_references_from_lines
from .validator import validate_references

app = typer.Typer(name="hallucheck", help="Detect hallucinated code in AI-generated diffs")


@app.command()
def check(diff: Optional[str] = None, staged: bool = False, pr: Optional[int] = None):
    """Check AI-generated diff for hallucinated references."""

    index = get_or_build_index()

    diff_lines = get_added_lines(diff_path=diff, staged=staged, pr=pr)

    if not diff_lines:
        console.print("[yellow]No added lines found in diff.[/yellow]")
        return

    references = extract_references_from_lines(diff_lines)
    hallucinations = validate_references(references, index)

    files_checked = len(set(dl.file for dl in diff_lines))
    total_symbols = sum(len(entries) for entries in index.values())
    total_files = len(set(entry["file"] for entries in index.values() for entry in entries))

    display_report(hallucinations, files_checked, total_symbols, total_files)

    if hallucinations:
        sys.exit(1)


@app.command()
def index(path: str = typer.Argument(".", help="Path to index")):
    """Build or rebuild the codebase symbol index."""
    console.print(f"Building index for {path}...")
    idx = build_index(path)
    save_index(idx, path)

    total_symbols = sum(len(entries) for entries in idx.values())
    total_files = len(set(entry["file"] for entries in idx.values() for entry in entries))
    console.print(
        f"[green]Successfully indexed {total_symbols} symbols across {total_files} files.[/green]"
    )


@app.command()
def explain(location: str):
    """Use Claude to explain a hallucination and suggest the fix. (location format: file:line)"""
    # For a real implementation, we would look up the specific hallucination from the last run
    # For now, we'll re-run check and find the one matching the location

    parts = location.split(":")
    if len(parts) != 2:
        console.print(
            "[red]Invalid location format. Use file:line (e.g. auth/validators.py:147)[/red]"
        )
        return

    target_file, target_line = parts[0], int(parts[1])

    index = get_or_build_index()
    diff_lines = get_added_lines()
    references = extract_references_from_lines(diff_lines)
    hallucinations = validate_references(references, index)

    target_h = None
    target_context = ""
    for h in hallucinations:
        if h.file == target_file and h.line == target_line:
            target_h = h
            # Find the context from diff_lines
            for dl in diff_lines:
                if dl.file == target_file and dl.line_number == target_line:
                    target_context = dl.content
                    break
            break

    if not target_h:
        console.print(f"[red]No hallucination found at {location}[/red]")
        return

    console.print("[cyan]Contacting Claude for explanation...[/cyan]")
    explanation = explain_hallucination(target_h, index, target_context)
    display_explanation(explanation)


@app.command()
def install_hook():
    """Install as a git pre-commit hook."""
    hook_path = Path(".git/hooks/pre-commit")
    if not Path(".git").exists():
        console.print(
            "[red]Error: .git directory not found. Are you in the root of a git repository?[/red]"
        )
        return

    hook_content = """#!/bin/sh
# HalluCheck pre-commit hook
echo "Running HalluCheck..."
hallucheck check --staged
if [ $? -ne 0 ]; then
    echo "HalluCheck found potential hallucinations. Commit aborted."
    exit 1
fi
"""
    with open(hook_path, "w") as f:
        f.write(hook_content)

    os.chmod(hook_path, 0o755)
    console.print("[green]Successfully installed HalluCheck pre-commit hook![/green]")


@app.command()
def config(api_key: str):
    """Set Anthropic API key (only needed for explain command)."""
    save_config({"api_key": api_key})
    console.print("[green]Configuration saved successfully.[/green]")


if __name__ == "__main__":
    app()
