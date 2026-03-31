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
