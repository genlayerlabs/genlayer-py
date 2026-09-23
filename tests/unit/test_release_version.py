import importlib.util
from pathlib import Path
import sys

import pytest


MODULE_PATH = Path(__file__).parents[2] / "scripts" / "release_version.py"
SPEC = importlib.util.spec_from_file_location("release_version", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
release_version = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = release_version
SPEC.loader.exec_module(release_version)


@pytest.mark.parametrize(
    ("raw", "normalized", "branch", "is_prerelease"),
    [
        ("0.19.0", "0.19.0", "v0.19", False),
        ("v0.19.0-rc.1", "0.19.0-rc.1", "v0.19-dev", True),
        ("0.19.0rc2", "0.19.0-rc.2", "v0.19-dev", True),
    ],
)
def test_release_version_normalizes_pep440_rc_spellings(
    raw, normalized, branch, is_prerelease
):
    version = release_version.parse_release_version(raw)

    assert version.normalized == normalized
    assert version.release_branch == branch
    assert version.is_prerelease is is_prerelease


@pytest.mark.parametrize(
    ("branch", "version", "message"),
    [
        ("main", "0.19.0", "not a release branch"),
        ("v0.18-dev", "0.19.0-rc.1", "belongs to v0.19"),
        ("v0.19", "0.19.0-rc.1", "must be cut from v0.19-dev"),
        ("v0.19-dev", "0.19.0", "must be cut from v0.19"),
    ],
)
def test_release_version_rejects_wrong_release_route(branch, version, message):
    with pytest.raises(ValueError, match=message):
        release_version.validate_branch_version(branch, version)


def test_release_version_accepts_rc_only_on_owning_dev_line():
    version = release_version.validate_branch_version("v0.19-dev", "0.19.0rc1")

    assert version.normalized == "0.19.0-rc.1"


@pytest.mark.parametrize("version", ["0.19.0-alpha.1", "0.19.0-rc.0", "00.19.0"])
def test_release_version_rejects_non_rc_or_noncanonical_versions(version):
    with pytest.raises(ValueError, match="not a supported release version"):
        release_version.parse_release_version(version)


def test_release_tag_and_package_version_compare_after_normalization():
    assert release_version.main(
        ["release_version.py", "verify-tag", "v0.19.0-rc.1", "0.19.0rc1"]
    ) == 0
