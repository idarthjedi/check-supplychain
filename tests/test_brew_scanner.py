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
