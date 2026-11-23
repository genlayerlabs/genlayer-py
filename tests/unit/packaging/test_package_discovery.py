import tomllib
from fnmatch import fnmatchcase
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


def _is_excluded(package: str, patterns: list[str]) -> bool:
    # setuptools' packages.find matches `exclude` with fnmatchcase on dotted names
    return any(fnmatchcase(package, pattern) for pattern in patterns)


def test_stale_build_output_is_excluded_from_package_discovery():
    """Leftover build/ and dist/ trees from earlier in-tree builds must not be
    picked up as packages (they made each wheel re-ship the previous one)."""
    with open(ROOT / "pyproject.toml", "rb") as f:
        exclude = tomllib.load(f)["tool"]["setuptools"]["packages"]["find"]["exclude"]

    for stale in ("build", "build.lib", "build.lib.genlayer_py", "dist", "dist.x"):
        assert _is_excluded(stale, exclude), stale
    assert not _is_excluded("genlayer_py", exclude)
    assert not _is_excluded("genlayer_py.client", exclude)
