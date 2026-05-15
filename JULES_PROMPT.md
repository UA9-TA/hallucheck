# Jules Build Prompt — HalluCheck v1.0

## What You Are Building

**HalluCheck** is an open-source CLI tool that detects hallucinated code in AI-generated diffs — functions, classes, API endpoints, and types that the AI referenced but don't actually exist in your codebase.

The core problem: LLMs confidently generate code that calls `user.get_permissions()` when no such method exists, imports `from utils.crypto import sign_payload` when that module was never written, or types a response as `AuthResponse` when only `LoginResponse` exists. These hallucinations pass syntax checks and linters — they only fail at runtime, often in production.

HalluCheck builds a semantic index of your codebase, then validates every AI-generated diff against it. Zero false positives. No network calls for the index — it runs entirely locally until it needs Claude to explain the finding.

**Target:** Top GitHub trending. Every developer using Cursor/Copilot/Claude Code has hit this.

---

## Core User Flow

```bash
# Install
pip install hallucheck

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

**Output:**
```
HalluCheck — Hallucination Report
──────────────────────────────────────────────────
✦ Files checked       3 files in last commit
✦ Index size          2,847 symbols across 94 files

  auth/validators.py
  ✗ Line 34   user.get_permissions()
              → Method does not exist on User model
              → Did you mean: user.permissions (property) or user.fetch_roles()?

  ✗ Line 67   from utils.crypto import sign_payload
              → Module utils.crypto does not exist
              → Closest: utils.signing (has: sign_jwt, sign_request)

  payment/processor.py
  ✗ Line 12   response: AuthResponse
              → Type AuthResponse not defined anywhere in codebase
              → Did you mean: LoginResponse (auth/types.py:8)?

✦ 3 hallucinations found in 2 files
✦ Run `hallucheck explain` for AI-powered fix suggestions
──────────────────────────────────────────────────
```

---

## Tech Stack

- **Language:** Python 3.10+
- **CLI framework:** Typer + Rich
- **AI:** Anthropic Claude API (`claude-sonnet-4-6`) — only for `explain` command
- **Indexing:** Python `ast` module for symbol extraction, stored as JSON
- **Git integration:** `subprocess` + `git diff`
- **Pre-commit:** writes hook to `.git/hooks/pre-commit`
- **Packaging:** `pyproject.toml` (hatchling), entry point `hallucheck`
- **Config:** `.hallucheck.toml` in project root

---

## Project Structure

```
hallucheck/
├── hallucheck/
│   ├── __init__.py
│   ├── cli.py              # Typer app — check, index, explain, install-hook
│   ├── indexer.py          # Walks codebase, extracts all symbols via AST
│   ├── diff_parser.py      # Parses git diff, extracts added lines only
│   ├── reference_extractor.py  # From added lines: extract all function calls, imports, types
│   ├── validator.py        # Checks every extracted reference against the index
│   ├── suggester.py        # Fuzzy-matches non-existent refs to closest real ones
│   ├── explainer.py        # Sends hallucination to Claude for explanation + fix
│   ├── display.py          # Rich terminal output
│   └── config.py           # Config reader/writer
├── tests/
│   ├── test_indexer.py
│   ├── test_diff_parser.py
│   ├── test_reference_extractor.py
│   ├── test_validator.py
│   └── fixtures/
│       ├── sample_codebase/    # Small fake codebase for indexing tests
│       │   ├── auth/
│       │   │   ├── models.py   # User model with specific methods
│       │   │   └── types.py    # LoginResponse type defined
│       │   └── utils/
│       │       └── signing.py  # sign_jwt, sign_request functions
│       └── sample_diff.patch   # AI-generated diff with 3 hallucinations
├── .github/
│   └── workflows/
│       └── ci.yml
├── pyproject.toml
└── README.md
```

---

## Detailed Module Specs

### `cli.py` — Entry point
```python
app = typer.Typer(name="hallucheck", help="Detect hallucinated code in AI-generated diffs")

@app.command()
def check(diff: Optional[str] = None, staged: bool = False, pr: Optional[int] = None):
    """Check AI-generated diff for hallucinated references."""

@app.command()
def index(path: str = "."):
    """Build or rebuild the codebase symbol index."""

@app.command()
def explain(location: str):
    """Use Claude to explain a hallucination and suggest the fix."""

@app.command()
def install_hook():
    """Install as a git pre-commit hook."""

@app.command()
def config(api_key: str):
    """Set Anthropic API key (only needed for explain command)."""
```

### `indexer.py` — Symbol extraction
Walk all `.py` files in the project, use `ast.parse()` to extract:
- All function/method definitions: `{name, file, line, class_context}`
- All class definitions: `{name, file, line}`
- All type aliases and dataclasses
- All module-level constants and variables
- All importable names per module

Store as `{symbol_name: [{file, line, kind, parent_class}]}` in `.hallucheck-index.json`.

Rebuild automatically if any source file is newer than the index file.

### `diff_parser.py` — Git diff parsing
- `git diff HEAD` for last commit
- `git diff --cached` for staged changes
- For PR mode: `gh pr diff <number>`
- Extract only `+` lines (added lines) with their file + line number context

### `reference_extractor.py` — Reference extraction from added lines
From each added line, extract:
- **Function/method calls:** `foo()`, `obj.bar()`, `Class.method()`
- **Imports:** `from module.sub import Name`
- **Type annotations:** `x: TypeName`, `-> ReturnType`
- **Instantiations:** `MyClass()`

Use Python `ast.parse()` on the added lines to get accurate extraction (not regex).

### `validator.py` — Hallucination detection
For each extracted reference:
- Check if it exists in the index
- For method calls `obj.method()`: check if `method` exists on any class named `obj`'s type (use heuristics if type inference isn't available)
- For imports: check if the module path exists as a real file/package
- For types: check if the name is defined anywhere in the index

Return list of `Hallucination` dataclasses:
```python
@dataclass
class Hallucination:
    file: str
    line: int
    reference: str          # The hallucinated symbol
    kind: str               # "method", "import", "type", "function"
    message: str            # "Method does not exist on User model"
    suggestions: list[str]  # Closest real alternatives
```

### `suggester.py` — Fuzzy suggestions
Use `difflib.get_close_matches()` against the full symbol index to suggest the closest real alternative. Show at most 2 suggestions per hallucination.

### `explainer.py` — Claude integration (explain command only)
Send the hallucination + surrounding code context to Claude. Ask it to:
1. Confirm whether it's truly a hallucination or a false positive
2. Explain what the AI was probably trying to do
3. Suggest the correct code using real symbols from the index

---

## README Spec

### Structure:
1. **Hero** — badges + one-liner: *"Your linter catches syntax errors. HalluCheck catches code that doesn't exist."*
2. **The problem** — concrete example: AI generates `user.get_permissions()`, tests pass (method never called in tests), crashes in production
3. **Demo** — `<!-- Add demo.gif here -->`
4. **Install** — `pip install hallucheck`
5. **Quick start** — scan, pre-commit hook install
6. **Sample output** — exact Rich output from above
7. **How it works** — builds a local symbol index, validates diffs against it
8. **Pre-commit integration** — `hallucheck install-hook`
9. **CI integration** — GitHub Actions example
10. **Why not just run the tests?** — hallucinations often pass unit tests if the hallucinated method is never exercised
11. **False positive rate** — explain: AST-based, not regex, very low FPR
12. **Contributing**
13. **License — MIT**

---

## CI (`ci.yml`)

```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - run: pip install -e ".[dev]"
      - run: pytest tests/ -v --cov=hallucheck --cov-fail-under=40
      - run: ruff check hallucheck/
      - run: ruff format --check hallucheck/
```

---

## `pyproject.toml`

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "hallucheck"
version = "0.1.0"
description = "Detect hallucinated API calls, types, and functions in AI-generated code"
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}
authors = [{name = "UA9-TA", email = "vkrmsatsangi@gmail.com"}]
keywords = ["ai", "hallucination", "linter", "developer-tools", "cli", "llm"]
dependencies = [
    "typer>=0.12",
    "rich>=13",
    "anthropic>=0.25",
    "tomli>=2.0; python_version < '3.11'",
]

[project.optional-dependencies]
dev = ["pytest", "ruff", "pytest-mock", "pytest-cov"]

[project.scripts]
hallucheck = "hallucheck.cli:app"

[project.urls]
Homepage = "https://github.com/UA9-TA/hallucheck"
Repository = "https://github.com/UA9-TA/hallucheck"
Changelog = "https://github.com/UA9-TA/hallucheck/blob/main/CHANGELOG.md"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--ignore=tests/fixtures"

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.ruff.lint]
select = ["E", "F", "W", "I"]
ignore = ["E501"]
```

---

## Fixtures (must be real working examples)

### `tests/fixtures/sample_codebase/`
A small fake Python project with:
- `auth/models.py` — a `User` class with `permissions` property and `fetch_roles()` method (NOT `get_permissions()`)
- `auth/types.py` — `LoginResponse` dataclass (NOT `AuthResponse`)
- `utils/signing.py` — `sign_jwt()` and `sign_request()` functions (NOT `sign_payload`)

### `tests/fixtures/sample_diff.patch`
A unified diff (`.patch` file) with exactly 3 hallucinations matching the fixture codebase:
1. Call to `user.get_permissions()` (should be `user.fetch_roles()`)
2. Import of `utils.crypto.sign_payload` (should be `utils.signing.sign_jwt`)
3. Type annotation `AuthResponse` (should be `LoginResponse`)

---

## What NOT to Build in v1

- No JavaScript/TypeScript support (Python only)
- No IDE plugin
- No cloud-based index storage
- No team sharing of index
- No automatic fixing (detect only, explain via Claude)

---

## Definition of Done

- [ ] `hallucheck index` builds symbol index from `tests/fixtures/sample_codebase/`
- [ ] `hallucheck check --diff tests/fixtures/sample_diff.patch` finds all 3 hallucinations
- [ ] `hallucheck install-hook` writes working pre-commit hook
- [ ] `hallucheck explain` successfully calls Claude API with context
- [ ] Suggestions use fuzzy matching to show closest real alternatives
- [ ] All output uses Rich
- [ ] CI passes on Python 3.10, 3.11, 3.12
- [ ] ruff passes

---

## Repo Details

- GitHub: https://github.com/UA9-TA/hallucheck
- Local path: /Users/chitra/Documents/Projects/hallucheck
- Branch: main
- License: MIT
