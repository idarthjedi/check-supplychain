# Parameterize Supply Chain Scanners

## Problem

The current shell scripts (`check-brew.sh`, `check-python.sh`) hardcode the package name (`litellm`) and version threshold (`1.82.7`). They need to accept arbitrary package names and flexible version specifications, and support multiple ecosystems.

## Decision: Rewrite in Python

Bash is a poor fit for the version comparison logic required (operators, ranges, multiple exact versions). Python provides `packaging.version.Version` for correct semver comparison, and a natural module structure for adding new ecosystem scanners.

## CLI Interface

```
python -m check_supplychain <package-name> <version-spec> [--scanner python|npm|brew|all]
```

### Version spec formats

| Format | Example | Meaning |
|--------|---------|---------|
| Exact version | `1.82.7` | Matches only 1.82.7 |
| Multiple exact | `1.80.0,1.81.0,1.82.7` | Matches any of those versions |
| Comparison | `>=1.82.7` | Matches versions >= 1.82.7 |
| Range | `>=1.80.0,<1.82.7` | Matches versions in that range |

Comma-separated items are AND'd when they contain operators, treated as OR'd exact matches when they don't.

### `--scanner` flag

- `python` — scan Python .dist-info directories
- `npm` — scan node_modules directories
- `brew` — scan Homebrew Cellar
- `all` (default) — run all scanners

### Output format

```
AFFECTED  <version>  <install-path>
ok        <version>  <install-path>
```

One line per found installation. Exit code 1 if any installation is AFFECTED, 0 otherwise.

## Code Architecture

```
check_supplychain/
├── __main__.py          # CLI entry point (argparse), output formatting
├── version_spec.py      # Parses version specs, evaluates matches
└── scanners/
    ├── __init__.py      # Scanner registry (name -> function mapping)
    ├── python_scanner.py
    ├── npm_scanner.py
    └── brew_scanner.py
```

### version_spec.py

Parses the version string argument into a `VersionSpec` object with a `matches(version_string) -> bool` method.

Detection logic:
1. Split on commas
2. If any part starts with an operator (`>=`, `<=`, `>`, `<`, `==`, `!=`), treat ALL parts as conditions (AND logic)
3. Otherwise, treat all parts as exact versions (OR logic)

Uses `packaging.version.Version` for all comparisons.

### Scanner interface

Each scanner is a function:

```python
def scan(package_name: str) -> Iterator[tuple[str, str]]:
    """Yields (version_string, install_path) for each found installation."""
```

Scanners are registered in `scanners/__init__.py` as a dict mapping name to function.

### python_scanner

Searches for `<normalized-package-name>-*.dist-info` directories across:
- `$HOME` (recursive)
- `/usr/local/lib/python*/`
- `/opt/homebrew/lib/python*/`

Extracts version from `METADATA` file (`Version:` field).

Package name normalization: replace hyphens with underscores, lowercase (per PEP 503).

### npm_scanner

Searches for `node_modules/<package-name>/package.json` across:
- `$HOME` (recursive)
- `/usr/local/lib/node_modules/`

Reads `version` field from `package.json`.

### brew_scanner

Scans Homebrew Cellar directories for formula directories matching the package name:
- `/opt/homebrew/Cellar/<package-name>/` (Apple Silicon)
- `/usr/local/Cellar/<package-name>/` (Intel)

Version is the subdirectory name under the formula directory.

### __main__.py

1. Parse args (package name, version spec, --scanner)
2. Build `VersionSpec` from version spec string
3. Run selected scanners, collect `(version, path)` results
4. For each result, evaluate against VersionSpec, print AFFECTED/ok line
5. Exit 1 if any AFFECTED, else exit 0

## Dependency

Only external dependency: `packaging` (pure Python, widely available, often pre-installed).

## Migration

The original shell scripts (`check-brew.sh`, `check-python.sh`) will be removed after the Python tool is functional.
