# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

Machine-wide scanner for vulnerable packages across Python, npm, and Homebrew ecosystems. Given a package name and version spec, it locates all installations on the local machine and flags affected ones.

## Architecture

Python package (`check_supplychain`) with three ecosystem scanners and a CLI entry point:

```
check_supplychain/
├── __main__.py          # CLI (argparse): parses args, runs scanners, prints results
├── version_spec.py      # VersionSpec class: parses version specs, evaluates matches
└── scanners/
    ├── __init__.py      # SCANNERS registry (name → scan function)
    ├── python_scanner.py  # Walks .dist-info dirs, reads METADATA
    ├── npm_scanner.py     # Walks node_modules, reads package.json
    └── brew_scanner.py    # Scans Homebrew Cellar directories
```

**Scanner interface:** Each scanner exposes `scan(package_name, optional_paths) -> Iterator[tuple[str, str]]` yielding `(version, install_path)`. The optional paths parameter overrides default system paths (used for testing).

**Adding a new scanner:** Create a new file in `scanners/`, implement the `scan()` function, register it in `scanners/__init__.py`.

## Running

```bash
# Scan all ecosystems for a vulnerable package
uv run python -m check_supplychain litellm ">=1.82.7"

# Scan only Python installations
uv run python -m check_supplychain litellm ">=1.80.0,<1.82.7" --scanner python

# Scan only Homebrew
uv run python -m check_supplychain node "20.11.0,21.6.1" --scanner brew
```

Exit code: 1 if any AFFECTED, 0 otherwise.

## Development

```bash
# Install dependencies
uv sync

# Run all tests
uv run pytest tests/ -v

# Run a single test file
uv run pytest tests/test_version_spec.py -v

# Run a single test
uv run pytest tests/test_version_spec.py::test_range_and_logic -v
```

## Conventions

- Use `uv` for all package management (never pip directly)
- Output format: `AFFECTED  <version>  <path>` or `ok        <version>  <path>`
- Version comparison uses `packaging.version.Version` (PEP 440 compliant)
- Package name normalization follows PEP 503 (hyphens/underscores/dots equivalent)
