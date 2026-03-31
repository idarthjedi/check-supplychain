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
