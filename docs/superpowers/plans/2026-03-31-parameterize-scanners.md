# Parameterize Supply Chain Scanners — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite the hardcoded shell scripts into a Python CLI tool that accepts any package name and flexible version specs, scanning across Python, npm, and Homebrew ecosystems.

**Architecture:** A Python package (`check_supplychain`) with a `VersionSpec` class for version matching, a scanner-per-ecosystem pattern with a shared registry, and an argparse-based CLI entry point. TDD throughout — each component is tested before the next is built.

**Tech Stack:** Python 3.10+, `uv` for package management, `packaging` library, `pytest` for testing, stdlib `pathlib`/`os`/`json` for filesystem scanning.

---

## File Structure

| File | Responsibility |
|------|---------------|
| `check_supplychain/__init__.py` | Package marker |
| `check_supplychain/version_spec.py` | Parse version specs, evaluate matches |
| `check_supplychain/scanners/__init__.py` | Scanner registry (name → function) |
| `check_supplychain/scanners/python_scanner.py` | Find Python packages via .dist-info |
| `check_supplychain/scanners/npm_scanner.py` | Find npm packages via package.json |
| `check_supplychain/scanners/brew_scanner.py` | Find Homebrew packages via Cellar |
| `check_supplychain/__main__.py` | CLI entry point, output formatting |
| `tests/test_version_spec.py` | Tests for VersionSpec |
| `tests/test_python_scanner.py` | Tests for Python scanner |
| `tests/test_npm_scanner.py` | Tests for npm scanner |
| `tests/test_brew_scanner.py` | Tests for Homebrew scanner |
| `tests/test_cli.py` | Integration tests for CLI |

---

### Task 1: Project scaffolding with uv

**Files:**
- Create: `pyproject.toml`
- Create: `check_supplychain/__init__.py`
- Create: `check_supplychain/scanners/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Initialize project with uv and add dependencies**

```bash
uv init --lib --name check-supplychain
uv add packaging
uv add --dev pytest
```

Then create the package directories:
```bash
mkdir -p check_supplychain/scanners tests
```

`check_supplychain/__init__.py`:
```python
```

`check_supplychain/scanners/__init__.py`:
```python
SCANNERS = {}
```

`tests/__init__.py`:
```python
```

- [ ] **Step 2: Verify pytest discovers the package**

Run: `uv run pytest tests/ -v --collect-only`
Expected: "no tests ran" (but no import errors)

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml uv.lock check_supplychain/ tests/
git commit -m "scaffold: init uv project with check_supplychain package"
```

---

### Task 2: VersionSpec — exact version matching

**Files:**
- Create: `check_supplychain/version_spec.py`
- Create: `tests/test_version_spec.py`

- [ ] **Step 1: Write failing tests for exact version matching**

`tests/test_version_spec.py`:
```python
from check_supplychain.version_spec import VersionSpec


def test_exact_single_version_matches():
    spec = VersionSpec("1.82.7")
    assert spec.matches("1.82.7") is True


def test_exact_single_version_no_match():
    spec = VersionSpec("1.82.7")
    assert spec.matches("1.82.6") is False


def test_multiple_exact_versions_match_first():
    spec = VersionSpec("1.80.0,1.81.0,1.82.7")
    assert spec.matches("1.80.0") is True


def test_multiple_exact_versions_match_last():
    spec = VersionSpec("1.80.0,1.81.0,1.82.7")
    assert spec.matches("1.82.7") is True


def test_multiple_exact_versions_no_match():
    spec = VersionSpec("1.80.0,1.81.0,1.82.7")
    assert spec.matches("1.83.0") is False
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_version_spec.py -v`
Expected: FAIL with ImportError (version_spec.py doesn't exist yet)

- [ ] **Step 3: Implement VersionSpec with exact matching**

`check_supplychain/version_spec.py`:
```python
import re
from packaging.version import Version

OPERATORS = (">=", "<=", "!=", "==", ">", "<")


class VersionSpec:
    def __init__(self, spec_string: str):
        self._raw = spec_string
        parts = [p.strip() for p in spec_string.split(",")]
        has_operator = any(p.startswith(OPERATORS) for p in parts)

        if has_operator:
            self._conditions = []
            for part in parts:
                op, ver = self._parse_condition(part)
                self._conditions.append((op, Version(ver)))
            self._exact_versions = None
        else:
            self._exact_versions = [Version(p) for p in parts]
            self._conditions = None

    @staticmethod
    def _parse_condition(part: str) -> tuple[str, str]:
        match = re.match(r"^(>=|<=|!=|==|>|<)(.+)$", part)
        if match:
            return match.group(1), match.group(2)
        # Bare version in operator context treated as ==
        return "==", part

    def matches(self, version_string: str) -> bool:
        v = Version(version_string)
        if self._exact_versions is not None:
            return v in self._exact_versions
        return all(self._compare(v, op, target) for op, target in self._conditions)

    @staticmethod
    def _compare(v: Version, op: str, target: Version) -> bool:
        if op == ">=":
            return v >= target
        if op == "<=":
            return v <= target
        if op == ">":
            return v > target
        if op == "<":
            return v < target
        if op == "==":
            return v == target
        if op == "!=":
            return v != target
        raise ValueError(f"Unknown operator: {op}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_version_spec.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add check_supplychain/version_spec.py tests/test_version_spec.py
git commit -m "feat: add VersionSpec with exact version matching"
```

---

### Task 3: VersionSpec — operator and range matching

**Files:**
- Modify: `tests/test_version_spec.py`

- [ ] **Step 1: Write failing tests for operators and ranges**

Append to `tests/test_version_spec.py`:
```python
def test_gte_operator_matches():
    spec = VersionSpec(">=1.82.7")
    assert spec.matches("1.82.7") is True
    assert spec.matches("1.83.0") is True


def test_gte_operator_no_match():
    spec = VersionSpec(">=1.82.7")
    assert spec.matches("1.82.6") is False


def test_lt_operator():
    spec = VersionSpec("<2.0.0")
    assert spec.matches("1.99.9") is True
    assert spec.matches("2.0.0") is False


def test_range_and_logic():
    spec = VersionSpec(">=1.80.0,<1.82.7")
    assert spec.matches("1.80.0") is True
    assert spec.matches("1.81.5") is True
    assert spec.matches("1.82.7") is False
    assert spec.matches("1.79.9") is False


def test_not_equal_operator():
    spec = VersionSpec("!=1.82.7")
    assert spec.matches("1.82.6") is True
    assert spec.matches("1.82.7") is False


def test_bare_version_in_operator_context():
    # "1.80.0,>=1.82.7" — 1.80.0 treated as ==1.80.0, AND'd with >=1.82.7
    # Nothing can satisfy both ==1.80.0 AND >=1.82.7
    spec = VersionSpec("1.80.0,>=1.82.7")
    assert spec.matches("1.80.0") is False
    assert spec.matches("1.82.7") is False
```

- [ ] **Step 2: Run tests to verify new tests fail (or pass — implementation may already handle this)**

Run: `uv run pytest tests/test_version_spec.py -v`
Expected: All 11 tests PASS (the implementation from Task 2 already handles operators)

- [ ] **Step 3: Commit**

```bash
git add tests/test_version_spec.py
git commit -m "test: add operator and range tests for VersionSpec"
```

---

### Task 4: Python scanner

**Files:**
- Create: `check_supplychain/scanners/python_scanner.py`
- Create: `tests/test_python_scanner.py`
- Modify: `check_supplychain/scanners/__init__.py`

- [ ] **Step 1: Write failing tests using a temporary directory with fake .dist-info**

`tests/test_python_scanner.py`:
```python
import os
from pathlib import Path
from check_supplychain.scanners.python_scanner import scan


def _create_dist_info(base: Path, package_name: str, version: str):
    """Create a fake .dist-info directory with METADATA."""
    dist_dir = base / f"{package_name}-{version}.dist-info"
    dist_dir.mkdir(parents=True)
    metadata = dist_dir / "METADATA"
    metadata.write_text(f"Metadata-Version: 2.1\nName: {package_name}\nVersion: {version}\n")


def test_finds_package_in_dist_info(tmp_path):
    site = tmp_path / "lib" / "python3.11" / "site-packages"
    _create_dist_info(site, "litellm", "1.82.7")

    results = list(scan("litellm", search_paths=[tmp_path]))
    assert len(results) == 1
    assert results[0][0] == "1.82.7"


def test_finds_multiple_versions(tmp_path):
    site1 = tmp_path / "venv1" / "lib" / "python3.11" / "site-packages"
    site2 = tmp_path / "venv2" / "lib" / "python3.11" / "site-packages"
    _create_dist_info(site1, "litellm", "1.80.0")
    _create_dist_info(site2, "litellm", "1.83.0")

    results = list(scan("litellm", search_paths=[tmp_path]))
    versions = {v for v, _ in results}
    assert versions == {"1.80.0", "1.83.0"}


def test_ignores_other_packages(tmp_path):
    site = tmp_path / "lib" / "python3.11" / "site-packages"
    _create_dist_info(site, "requests", "2.31.0")

    results = list(scan("litellm", search_paths=[tmp_path]))
    assert len(results) == 0


def test_normalizes_package_name(tmp_path):
    site = tmp_path / "lib" / "python3.11" / "site-packages"
    _create_dist_info(site, "my_package", "1.0.0")

    results = list(scan("my-package", search_paths=[tmp_path]))
    assert len(results) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_python_scanner.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement python_scanner**

`check_supplychain/scanners/python_scanner.py`:
```python
import os
import re
from pathlib import Path
from typing import Iterator

DEFAULT_SEARCH_PATHS = [
    Path.home(),
    Path("/usr/local/lib"),
    Path("/opt/homebrew/lib"),
]


def _normalize(name: str) -> str:
    """PEP 503 normalization: lowercase, hyphens to underscores."""
    return re.sub(r"[-_.]+", "_", name).lower()


def scan(package_name: str, search_paths: list[Path] | None = None) -> Iterator[tuple[str, str]]:
    """Yield (version, path) for each installed Python package matching package_name."""
    normalized = _normalize(package_name)
    paths = search_paths if search_paths is not None else DEFAULT_SEARCH_PATHS

    for search_root in paths:
        if not search_root.exists():
            continue
        for root, dirs, _files in os.walk(search_root):
            root_path = Path(root)
            # Look for <name>-<version>.dist-info directories
            matching = [d for d in dirs if d.endswith(".dist-info")]
            for dirname in matching:
                # dirname format: <normalized_name>-<version>.dist-info
                name_part = dirname[: -len(".dist-info")]
                # Split on last hyphen to separate name from version
                # But name can contain hyphens, so find version from METADATA
                dist_path = root_path / dirname
                metadata = dist_path / "METADATA"
                if not metadata.exists():
                    continue
                meta_name = None
                meta_version = None
                with open(metadata) as f:
                    for line in f:
                        if line.startswith("Name:"):
                            meta_name = line.split(":", 1)[1].strip()
                        elif line.startswith("Version:"):
                            meta_version = line.split(":", 1)[1].strip()
                        if meta_name and meta_version:
                            break
                if meta_name and _normalize(meta_name) == normalized and meta_version:
                    yield meta_version, str(dist_path)
            # Don't recurse into .dist-info dirs themselves
            dirs[:] = [d for d in dirs if not d.endswith(".dist-info")]
```

- [ ] **Step 4: Register python scanner**

Update `check_supplychain/scanners/__init__.py`:
```python
from check_supplychain.scanners.python_scanner import scan as python_scan
from typing import Iterator
from pathlib import Path

# Scanner signature: (package_name: str) -> Iterator[tuple[str, str]]
SCANNERS = {
    "python": python_scan,
}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_python_scanner.py -v`
Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
git add check_supplychain/scanners/python_scanner.py tests/test_python_scanner.py check_supplychain/scanners/__init__.py
git commit -m "feat: add Python scanner for .dist-info packages"
```

---

### Task 5: npm scanner

**Files:**
- Create: `check_supplychain/scanners/npm_scanner.py`
- Create: `tests/test_npm_scanner.py`
- Modify: `check_supplychain/scanners/__init__.py`

- [ ] **Step 1: Write failing tests using a temporary directory with fake node_modules**

`tests/test_npm_scanner.py`:
```python
import json
from pathlib import Path
from check_supplychain.scanners.npm_scanner import scan


def _create_npm_package(base: Path, package_name: str, version: str):
    """Create a fake node_modules/<name>/package.json."""
    pkg_dir = base / "node_modules" / package_name
    pkg_dir.mkdir(parents=True)
    pkg_json = pkg_dir / "package.json"
    pkg_json.write_text(json.dumps({"name": package_name, "version": version}))


def test_finds_npm_package(tmp_path):
    _create_npm_package(tmp_path / "project1", "lodash", "4.17.20")

    results = list(scan("lodash", search_paths=[tmp_path]))
    assert len(results) == 1
    assert results[0][0] == "4.17.20"


def test_finds_multiple_installations(tmp_path):
    _create_npm_package(tmp_path / "project1", "lodash", "4.17.20")
    _create_npm_package(tmp_path / "project2", "lodash", "4.17.21")

    results = list(scan("lodash", search_paths=[tmp_path]))
    versions = {v for v, _ in results}
    assert versions == {"4.17.20", "4.17.21"}


def test_ignores_other_packages(tmp_path):
    _create_npm_package(tmp_path / "project1", "express", "4.18.0")

    results = list(scan("lodash", search_paths=[tmp_path]))
    assert len(results) == 0


def test_finds_scoped_package(tmp_path):
    pkg_dir = tmp_path / "project1" / "node_modules" / "@angular" / "core"
    pkg_dir.mkdir(parents=True)
    (pkg_dir / "package.json").write_text(json.dumps({"name": "@angular/core", "version": "16.0.0"}))

    results = list(scan("@angular/core", search_paths=[tmp_path]))
    assert len(results) == 1
    assert results[0][0] == "16.0.0"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_npm_scanner.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement npm_scanner**

`check_supplychain/scanners/npm_scanner.py`:
```python
import json
import os
from pathlib import Path
from typing import Iterator

DEFAULT_SEARCH_PATHS = [
    Path.home(),
    Path("/usr/local/lib"),
]


def scan(package_name: str, search_paths: list[Path] | None = None) -> Iterator[tuple[str, str]]:
    """Yield (version, path) for each installed npm package matching package_name."""
    paths = search_paths if search_paths is not None else DEFAULT_SEARCH_PATHS

    # Handle scoped packages like @angular/core
    if package_name.startswith("@"):
        scope, name = package_name.split("/", 1)
        relative_parts = ("node_modules", scope, name)
    else:
        relative_parts = ("node_modules", package_name)

    for search_root in paths:
        if not search_root.exists():
            continue
        for root, dirs, _files in os.walk(search_root):
            if "node_modules" not in dirs:
                continue
            # Check this specific node_modules for our package
            pkg_json_path = Path(root).joinpath(*relative_parts) / "package.json"
            if pkg_json_path.exists():
                try:
                    data = json.loads(pkg_json_path.read_text())
                    version = data.get("version")
                    if version and data.get("name") == package_name:
                        yield version, str(pkg_json_path.parent)
                except (json.JSONDecodeError, KeyError):
                    continue
            # Don't recurse into the node_modules we just checked,
            # but do recurse into other dirs to find more node_modules
            # Also skip nested node_modules (dependencies of dependencies)
            nm_path = Path(root) / "node_modules"
            if nm_path.exists():
                dirs[:] = [d for d in dirs if d != "node_modules"]
```

- [ ] **Step 4: Register npm scanner**

Update `check_supplychain/scanners/__init__.py`:
```python
from check_supplychain.scanners.python_scanner import scan as python_scan
from check_supplychain.scanners.npm_scanner import scan as npm_scan

SCANNERS = {
    "python": python_scan,
    "npm": npm_scan,
}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_npm_scanner.py -v`
Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
git add check_supplychain/scanners/npm_scanner.py tests/test_npm_scanner.py check_supplychain/scanners/__init__.py
git commit -m "feat: add npm scanner for node_modules packages"
```

---

### Task 6: Homebrew scanner

**Files:**
- Create: `check_supplychain/scanners/brew_scanner.py`
- Create: `tests/test_brew_scanner.py`
- Modify: `check_supplychain/scanners/__init__.py`

- [ ] **Step 1: Write failing tests using a temporary directory with fake Cellar structure**

`tests/test_brew_scanner.py`:
```python
from pathlib import Path
from check_supplychain.scanners.brew_scanner import scan


def _create_cellar_entry(cellar: Path, formula: str, version: str):
    """Create a fake Cellar/<formula>/<version>/ directory."""
    (cellar / formula / version).mkdir(parents=True)


def test_finds_brew_package(tmp_path):
    cellar = tmp_path / "Cellar"
    _create_cellar_entry(cellar, "python@3.11", "3.11.8")

    results = list(scan("python@3.11", cellar_paths=[cellar]))
    assert len(results) == 1
    assert results[0][0] == "3.11.8"


def test_finds_multiple_versions(tmp_path):
    cellar = tmp_path / "Cellar"
    _create_cellar_entry(cellar, "node", "20.11.0")
    _create_cellar_entry(cellar, "node", "21.6.1")

    results = list(scan("node", cellar_paths=[cellar]))
    versions = {v for v, _ in results}
    assert versions == {"20.11.0", "21.6.1"}


def test_ignores_other_formulae(tmp_path):
    cellar = tmp_path / "Cellar"
    _create_cellar_entry(cellar, "wget", "1.21.4")

    results = list(scan("curl", cellar_paths=[cellar]))
    assert len(results) == 0


def test_handles_missing_cellar(tmp_path):
    cellar = tmp_path / "nonexistent" / "Cellar"
    results = list(scan("node", cellar_paths=[cellar]))
    assert len(results) == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_brew_scanner.py -v`
Expected: FAIL with ImportError

- [ ] **Step 3: Implement brew_scanner**

`check_supplychain/scanners/brew_scanner.py`:
```python
from pathlib import Path
from typing import Iterator

DEFAULT_CELLAR_PATHS = [
    Path("/opt/homebrew/Cellar"),   # Apple Silicon
    Path("/usr/local/Cellar"),       # Intel
]


def scan(package_name: str, cellar_paths: list[Path] | None = None) -> Iterator[tuple[str, str]]:
    """Yield (version, path) for each Homebrew formula matching package_name."""
    cellars = cellar_paths if cellar_paths is not None else DEFAULT_CELLAR_PATHS

    for cellar in cellars:
        formula_dir = cellar / package_name
        if not formula_dir.is_dir():
            continue
        for version_dir in formula_dir.iterdir():
            if version_dir.is_dir():
                yield version_dir.name, str(version_dir)
```

- [ ] **Step 4: Register brew scanner**

Update `check_supplychain/scanners/__init__.py`:
```python
from check_supplychain.scanners.python_scanner import scan as python_scan
from check_supplychain.scanners.npm_scanner import scan as npm_scan
from check_supplychain.scanners.brew_scanner import scan as brew_scan

SCANNERS = {
    "python": python_scan,
    "npm": npm_scan,
    "brew": brew_scan,
}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `uv run pytest tests/test_brew_scanner.py -v`
Expected: 4 passed

- [ ] **Step 6: Commit**

```bash
git add check_supplychain/scanners/brew_scanner.py tests/test_brew_scanner.py check_supplychain/scanners/__init__.py
git commit -m "feat: add Homebrew scanner for Cellar packages"
```

---

### Task 7: CLI entry point

**Files:**
- Create: `check_supplychain/__main__.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write failing integration tests**

`tests/test_cli.py`:
```python
import subprocess
from pathlib import Path


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["uv", "run", "python", "-m", "check_supplychain", *args],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent),
    )


def test_missing_args_shows_usage():
    result = _run_cli()
    assert result.returncode != 0
    assert "usage" in result.stderr.lower()


def test_help_flag():
    result = _run_cli("--help")
    assert result.returncode == 0
    assert "package_name" in result.stdout


def test_scanner_flag_accepted():
    # Should run without error even if no packages found
    result = _run_cli("nonexistent-pkg-12345", "1.0.0", "--scanner", "brew")
    assert result.returncode == 0


def test_invalid_scanner_rejected():
    result = _run_cli("pkg", "1.0.0", "--scanner", "invalid")
    assert result.returncode != 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_cli.py -v`
Expected: FAIL (no __main__.py yet)

- [ ] **Step 3: Implement __main__.py**

`check_supplychain/__main__.py`:
```python
import argparse
import sys

from check_supplychain.version_spec import VersionSpec
from check_supplychain.scanners import SCANNERS


def main():
    parser = argparse.ArgumentParser(
        prog="check_supplychain",
        description="Scan for vulnerable packages across Python, npm, and Homebrew.",
    )
    parser.add_argument("package_name", help="Name of the package to search for")
    parser.add_argument("version_spec", help="Version spec: exact (1.0.0), multiple (1.0.0,1.1.0), comparison (>=1.0.0), or range (>=1.0.0,<2.0.0)")
    parser.add_argument(
        "--scanner",
        choices=list(SCANNERS.keys()) + ["all"],
        default="all",
        help="Which ecosystem to scan (default: all)",
    )

    args = parser.parse_args()
    spec = VersionSpec(args.version_spec)

    scanners_to_run = SCANNERS if args.scanner == "all" else {args.scanner: SCANNERS[args.scanner]}

    any_affected = False
    for scanner_name, scan_fn in scanners_to_run.items():
        for version, path in scan_fn(args.package_name):
            if spec.matches(version):
                print(f"AFFECTED  {version}  {path}")
                any_affected = True
            else:
                print(f"ok        {version}  {path}")

    sys.exit(1 if any_affected else 0)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_cli.py -v`
Expected: 4 passed

- [ ] **Step 5: Run full test suite**

Run: `uv run pytest tests/ -v`
Expected: All 17 tests pass

- [ ] **Step 6: Commit**

```bash
git add check_supplychain/__main__.py tests/test_cli.py
git commit -m "feat: add CLI entry point for check_supplychain"
```

---

### Task 8: Remove old shell scripts and update CLAUDE.md

**Files:**
- Remove: `check-brew.sh`
- Remove: `check-python.sh`
- Modify: `CLAUDE.md`

- [ ] **Step 1: Remove old shell scripts**

```bash
git rm check-brew.sh check-python.sh
```

- [ ] **Step 2: Update CLAUDE.md to reflect new architecture**

Update `CLAUDE.md` to describe the Python package structure, CLI usage, how to run tests, and how to add new scanners. Remove references to the shell scripts.

- [ ] **Step 3: Run full test suite one final time**

Run: `uv run pytest tests/ -v`
Expected: All 17 tests pass

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: remove old shell scripts, update CLAUDE.md for Python rewrite"
```
