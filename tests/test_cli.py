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
