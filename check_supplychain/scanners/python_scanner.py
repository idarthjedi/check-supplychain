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
