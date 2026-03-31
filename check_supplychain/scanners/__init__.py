from check_supplychain.scanners.python_scanner import scan as python_scan
from check_supplychain.scanners.npm_scanner import scan as npm_scan
from check_supplychain.scanners.brew_scanner import scan as brew_scan

SCANNERS = {
    "python": python_scan,
    "npm": npm_scan,
    "brew": brew_scan,
}
