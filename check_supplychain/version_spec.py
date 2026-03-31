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
