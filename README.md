# HalluCheck

![CI](https://github.com/UA9-TA/hallucheck/actions/workflows/ci.yml/badge.svg)

**Your linter catches syntax errors. HalluCheck catches code that doesn't exist.**

LLMs confidently generate code that calls `user.get_permissions()` when no such method exists, imports `from utils.crypto import sign_payload` when that module was never written, or types a response as `AuthResponse` when only `LoginResponse` exists. These hallucinations pass syntax checks and linters — they only fail at runtime, often in production.

HalluCheck builds a semantic index of your codebase, then validates every AI-generated diff against it. Zero false positives. No network calls for the index — it runs entirely locally until it needs Claude to explain the finding.

<!-- Add demo.gif here -->

## Installation

```bash
pip install hallucheck
```

## Quick Start

```bash
# Build the index for the current directory
hallucheck index

# Check the last commit
hallucheck check

# Install pre-commit hook
hallucheck install-hook
```

## Sample Output

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

## How It Works

HalluCheck uses the Python `ast` module to build a local symbol index of your repository. It then uses the `ast` module on the modified/added lines in your diff to extract the names of functions, imports, and type references. It checks every referenced name against the index to catch AI-hallucinated calls. It fuzzy-matches any missing names to your real codebase names, providing immediate "did you mean" fixes.

## CI Integration

Add to `.github/workflows/ci.yml`:

```yaml
name: Check Hallucinations
on: [pull_request]
jobs:
  hallucheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install hallucheck
      - run: hallucheck index
      - run: hallucheck check --pr ${{ github.event.pull_request.number }}
```

## Why Not Just Run the Tests?

Hallucinations often slip past unit tests when the new code path containing the hallucination is not covered by a test. This happens frequently with AI-generated error handling, fallback logic, or edge-case conditions. HalluCheck analyzes the syntax tree of your *changes*, ensuring that *every* reference exists, regardless of test coverage.

## False Positive Rate

Because HalluCheck relies on the Python AST instead of regex, its false-positive rate is practically zero. If a function isn't found in your project index (or standard library/installed packages — via heuristics), it will be flagged.

## The Developer Toolkit Ecosystem

This tool is part of a suite of open-source AI-powered developer tools:

| Tool | What it does |
|---|---|
| **[RootCause](https://github.com/UA9-TA/rootcause)** | Auto-diagnose failing tests — AI root cause + fix |
| **[ErrorMentor](https://github.com/UA9-TA/errormentor)** | Auto-diagnose production errors — correlate logs with git commits |
| **[TestGap](https://github.com/UA9-TA/testgap)** | Find untested code paths after every commit |
| **[HalluCheck](https://github.com/UA9-TA/hallucheck)** | Catch AI hallucinations in code diffs |
| **[IntentDiff](https://github.com/UA9-TA/intentdiff)** | Understand what a diff *actually* does semantically |
| **[DepSecure](https://github.com/UA9-TA/depsecure)** | Block vulnerable dependencies at commit time |
| **[ArchGuard](https://github.com/UA9-TA/archguard)** | Enforce microservice architecture rules across repos |
| **[SpendSentry](https://github.com/UA9-TA/spendsentry)** | Monitor cloud spend in real time — alert before costs spiral |
| **[ContextKit](https://github.com/UA9-TA/contextkit)** | Build minimal AI context bundles — 88% fewer tokens |

## License

MIT
