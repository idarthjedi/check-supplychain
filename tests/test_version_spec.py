from check_supplychain.version_spec import VersionSpec


def test_exact_single_version_matches():
    spec = VersionSpec("1.82.7")
    assert spec.matches("1.82.7") is True


def test_exact_single_version_no_match():
    spec = VersionSpec("1.82.7")
    assert spec.matches("1.82.6") is False


def test_multiple_exact_versions_match_first():
    spec = VersionSpec("1.80.0,1.81.0,1.82.7")
    assert spec.matches("1.80.0") is True


def test_multiple_exact_versions_match_last():
    spec = VersionSpec("1.80.0,1.81.0,1.82.7")
    assert spec.matches("1.82.7") is True


def test_multiple_exact_versions_no_match():
    spec = VersionSpec("1.80.0,1.81.0,1.82.7")
    assert spec.matches("1.83.0") is False


def test_gte_operator_matches():
    spec = VersionSpec(">=1.82.7")
    assert spec.matches("1.82.7") is True
    assert spec.matches("1.83.0") is True


def test_gte_operator_no_match():
    spec = VersionSpec(">=1.82.7")
    assert spec.matches("1.82.6") is False


def test_lt_operator():
    spec = VersionSpec("<2.0.0")
    assert spec.matches("1.99.9") is True
    assert spec.matches("2.0.0") is False


def test_range_and_logic():
    spec = VersionSpec(">=1.80.0,<1.82.7")
    assert spec.matches("1.80.0") is True
    assert spec.matches("1.81.5") is True
    assert spec.matches("1.82.7") is False
    assert spec.matches("1.79.9") is False


def test_not_equal_operator():
    spec = VersionSpec("!=1.82.7")
    assert spec.matches("1.82.6") is True
    assert spec.matches("1.82.7") is False


def test_bare_version_in_operator_context():
    # "1.80.0,>=1.82.7" — 1.80.0 treated as ==1.80.0, AND'd with >=1.82.7
    # Nothing can satisfy both ==1.80.0 AND >=1.82.7
    spec = VersionSpec("1.80.0,>=1.82.7")
    assert spec.matches("1.80.0") is False
    assert spec.matches("1.82.7") is False
