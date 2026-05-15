# HalluCheck

Your linter catches syntax errors. HalluCheck catches code that doesn't exist.

HalluCheck is an open-source CLI tool that detects hallucinated code in AI-generated diffs — functions, classes, API endpoints, and types that the AI referenced but don't actually exist in your codebase.

## The Problem
LLMs confidently generate code that calls `user.get_permissions()` when no such method exists, imports `from utils.crypto import sign_payload` when that module was never written, or types a response as `AuthResponse` when only `LoginResponse` exists. These hallucinations pass syntax checks and linters — they only fail at runtime, often in production.

HalluCheck builds a semantic index of your codebase, then validates every AI-generated diff against it. Zero false positives. No network calls for the index — it runs entirely locally until it needs Claude to explain the finding.

## Install

```bash
pip install hallucheck
```

## Quick Start

```bash
# Check the last AI-generated commit
hallucheck check

# Check a specific diff or file
hallucheck check --diff path/to/file.py
hallucheck check --staged          # check staged changes before commit
hallucheck check --pr 42           # check a GitHub PR diff

# Install as a pre-commit hook
hallucheck install-hook

# Build/rebuild the codebase index
hallucheck index

# Explain a specific hallucination
hallucheck explain auth/validators.py:147
```

## How It Works

HalluCheck builds a semantic local index of all symbols in your Python codebase (using the `ast` module, not regular expressions). It then parses Git diffs and checks all inserted symbol references (functions called, types used, modules imported) against your codebase.

## Pre-commit Integration

```bash
hallucheck install-hook
```

This will automatically check your staged files before committing, keeping hallucinated code out of your repository.

## CI Integration

Add this step to your GitHub Actions:

```yaml
steps:
  - uses: actions/checkout@v4
    with:
      fetch-depth: 0
  - name: Run HalluCheck
    run: |
      pip install hallucheck
      hallucheck index
      hallucheck check --staged
```

## Why not just run the tests?

Hallucinations often pass unit tests if the hallucinated method is never exercised in the test coverage, lying dormant until invoked in production.

## False positive rate

HalluCheck uses AST-based parsing, not regular expressions. This ensures very low false positive rates.

## License

MIT
