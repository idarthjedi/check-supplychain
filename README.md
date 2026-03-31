# check-supplychain

Machine-wide scanner for vulnerable packages across Python, npm, and Homebrew ecosystems. Given a package name and version spec, it locates all installations on your machine and flags affected ones.

## Quick Start

Requires [uv](https://docs.astral.sh/uv/) and Python 3.12+.

```bash
git clone git@github.com:idarthjedi/check-supplychain.git
cd check-supplychain
uv sync
```

## Usage

```bash
uv run python -m check_supplychain <package-name> <version-spec> [--scanner python|npm|brew|all]
```

### Version spec formats

| Format | Example | Meaning |
|--------|---------|---------|
| Exact version | `1.82.7` | Matches only 1.82.7 |
| Multiple exact | `1.80.0,1.81.0,1.82.7` | Matches any listed version |
| Comparison | `>=1.82.7` | Matches versions >= 1.82.7 |
| Range | `>=1.80.0,<1.82.7` | Matches versions in range |

### Examples

```bash
# Find all installations of litellm >= 1.82.7 across your machine
uv run python -m check_supplychain litellm ">=1.82.7"

# Check only Python environments for a specific vulnerable range
uv run python -m check_supplychain litellm ">=1.80.0,<1.82.7" --scanner python

# Check Homebrew for specific node versions
uv run python -m check_supplychain node "20.11.0,21.6.1" --scanner brew

# Check npm for a vulnerable lodash version range
uv run python -m check_supplychain lodash ">=4.17.0,<4.17.21" --scanner npm
```

### Output

```
AFFECTED  python  1.82.7  /Users/you/.venv/lib/python3.12/site-packages/litellm-1.82.7.dist-info
ok        python  1.83.0  /Users/you/other-project/.venv/lib/python3.12/site-packages/litellm-1.83.0.dist-info
ok        brew    3.12.11 /opt/homebrew/Cellar/python@3.12/3.12.11
```

Exit code is **1** if any installation is AFFECTED, **0** otherwise. This makes it composable in scripts:

```bash
if uv run python -m check_supplychain litellm ">=1.82.7"; then
    echo "No vulnerable versions found"
else
    echo "Vulnerable installations detected!"
fi
```

## Scanners

| Scanner | What it scans | Default search paths |
|---------|--------------|---------------------|
| `python` | `.dist-info` directories with METADATA | `$HOME`, `/usr/local/lib`, `/opt/homebrew/lib` |
| `npm` | `node_modules/*/package.json` | `$HOME`, `/usr/local/lib` |
| `brew` | Homebrew Cellar directories | `/opt/homebrew/Cellar`, `/usr/local/Cellar` |

Use `--scanner all` (default) to run all scanners, or pick a specific one.

## Development

```bash
# Run all tests
uv run pytest tests/ -v

# Run tests for a specific component
uv run pytest tests/test_version_spec.py -v
uv run pytest tests/test_python_scanner.py -v

# Run a single test
uv run pytest tests/test_version_spec.py::test_range_and_logic -v
```

### Adding a new scanner

1. Create `check_supplychain/scanners/<name>_scanner.py`
2. Implement `scan(package_name: str, ...) -> Iterator[tuple[str, str]]` yielding `(version, path)`
3. Register it in `check_supplychain/scanners/__init__.py`
4. Add tests in `tests/test_<name>_scanner.py`
