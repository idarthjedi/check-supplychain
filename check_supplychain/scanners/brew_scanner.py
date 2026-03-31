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
