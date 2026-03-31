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
