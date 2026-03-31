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
