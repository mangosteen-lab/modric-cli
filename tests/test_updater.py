from modric_cli import updater


def test_is_newer_semver():
    assert updater.is_newer("0.0.2", "0.0.1")
    assert updater.is_newer("1.0.0", "0.9.9")
    assert not updater.is_newer("0.0.1", "0.0.1")
    assert not updater.is_newer("0.0.1", "0.1.0")


def test_expected_hash_parse():
    sums = ("abc123  modric_cli-0.0.2-py3-none-any.whl\n"
            "def456  modric_cli-0.0.2.tar.gz\n")
    assert updater._expected_hash(sums, "modric_cli-0.0.2-py3-none-any.whl") == "abc123"
    assert updater._expected_hash(sums, "nope.whl") is None
