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
