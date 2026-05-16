import os
from pathlib import Path
from typing import Optional

import typer

from .config import get_config, save_config
from .diff_parser import get_git_diff, parse_diff
from .display import print_explanation, print_report
from .explainer import explain_hallucination
from .indexer import build_index, load_index
from .validator import validate_diff

app = typer.Typer(name="hallucheck", help="Detect hallucinated code in AI-generated diffs")


@app.command()
def check(diff: Optional[str] = None, staged: bool = False, pr: Optional[int] = None):
    """Check AI-generated diff for hallucinated references."""
    index = load_index()
    if not index:
        typer.echo("Index not found. Building index first...")
        index = build_index()

    if diff:
        try:
            with open(diff, "r") as f:
                diff_content = f.read()
        except FileNotFoundError:
            typer.echo(f"Error: Diff file '{diff}' not found.", err=True)
            raise typer.Exit(1)
    else:
        diff_content = get_git_diff(staged=staged, pr=pr)

    if not diff_content:
        typer.echo("No diff found.")
        raise typer.Exit(0)

    diff_lines = parse_diff(diff_content)

    if not diff_lines:
        typer.echo("No Python additions found in diff.")
        raise typer.Exit(0)

    hallucinations = validate_diff(diff_lines, index)

    # Calculate stats
    files_checked = len(set(item["file"] for item in diff_lines))
    index_size_symbols = len(index)

    # Count unique files in index
    index_files = set()
    for occurrences in index.values():
        for occ in occurrences:
            index_files.add(occ["file"])
    index_size_files = len(index_files)

    print_report(hallucinations, files_checked, index_size_symbols, index_size_files)

    if hallucinations:
        # We save the last hallucinations for the explain command
        import json

        with open(".hallucheck-last-run.json", "w") as f:
            data = [
                {
                    "file": h.file,
                    "line": h.line,
                    "reference": h.reference,
                    "message": h.message,
                    "suggestions": h.suggestions,
                }
                for h in hallucinations
            ]
            json.dump(data, f)

        raise typer.Exit(1)


@app.command()
def index(path: str = "."):
    """Build or rebuild the codebase symbol index."""
    typer.echo(f"Building index for {path}...")
    idx = build_index(path)
    typer.echo(f"Index built with {len(idx)} symbols.")


@app.command()
def explain(location: str):
    """Use Claude to explain a hallucination and suggest the fix."""
    try:
        with open(".hallucheck-last-run.json", "r") as f:
            import json

            last_run = json.load(f)
    except FileNotFoundError:
        typer.echo("No previous run found. Run `hallucheck check` first.", err=True)
        raise typer.Exit(1)

    if ":" in location:
        file, line = location.split(":", 1)
        line = int(line)
        target = next((h for h in last_run if h["file"] == file and h["line"] == line), None)
    else:
        # Explain the first one if no location is specified or location is a file
        target = next((h for h in last_run if h["file"] == location), None)
        if not target and last_run:
            target = last_run[0]

    if not target:
        typer.echo(f"Could not find hallucination at {location}", err=True)
        raise typer.Exit(1)

    hallucination_str = f"File: {target['file']}, Line: {target['line']}\n"
    hallucination_str += f"Reference: {target['reference']}\n"
    hallucination_str += f"Error: {target['message']}\n"
    if target["suggestions"]:
        hallucination_str += f"Suggestions: {', '.join(target['suggestions'])}\n"

    typer.echo("Asking Claude...")
    explanation = explain_hallucination(hallucination_str)
    print_explanation(explanation)


@app.command()
def install_hook():
    """Install as a git pre-commit hook."""
    git_dir = Path(".git")
    if not git_dir.exists():
        typer.echo("Error: .git directory not found. Are you in the project root?", err=True)
        raise typer.Exit(1)

    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)

    pre_commit_path = hooks_dir / "pre-commit"

    hook_script = """#!/bin/sh
# hallucheck pre-commit hook
hallucheck check --staged
"""

    with open(pre_commit_path, "w") as f:
        f.write(hook_script)

    # Make executable
    os.chmod(pre_commit_path, 0o755)

    typer.echo(f"Successfully installed pre-commit hook at {pre_commit_path}")


@app.command()
def config_cmd(api_key: str):
    """Set Anthropic API key (only needed for explain command)."""
    cfg = get_config()
    cfg["api_key"] = api_key
    save_config(cfg)
    typer.echo("API key saved.")


# Typer doesn't let you use the command name 'config' because it conflicts,
# so we register it differently
app.command(name="config")(config_cmd)

if __name__ == "__main__":
    app()
