#!/usr/bin/env python3
"""Validate GenLayer Python release versions and their owning branches."""

from __future__ import annotations

from dataclasses import dataclass
import re
import sys


_VERSION_PATTERN = re.compile(
    r"^v?(?P<major>0|[1-9][0-9]*)\."
    r"(?P<minor>0|[1-9][0-9]*)\."
    r"(?P<patch>0|[1-9][0-9]*)"
    r"(?:(?:-?rc\.?(?P<rc>[1-9][0-9]*)))?$",
    re.IGNORECASE,
)
_BRANCH_PATTERN = re.compile(
    r"^v(?P<major>0|[1-9][0-9]*)\."
    r"(?P<minor>0|[1-9][0-9]*)(?P<dev>-dev)?$"
)


@dataclass(frozen=True)
class ReleaseVersion:
    major: int
    minor: int
    patch: int
    rc: int | None = None

    @property
    def normalized(self) -> str:
        suffix = "" if self.rc is None else f"-rc.{self.rc}"
        return f"{self.major}.{self.minor}.{self.patch}{suffix}"

    @property
    def is_prerelease(self) -> bool:
        return self.rc is not None

    @property
    def sort_key(self) -> tuple[int, int, int, bool, int]:
        # A final sorts after every release candidate of the same X.Y.Z.
        return (self.major, self.minor, self.patch, self.rc is None, self.rc or 0)

    @property
    def stable_branch(self) -> str:
        return f"v{self.major}.{self.minor}"

    @property
    def dev_branch(self) -> str:
        return f"{self.stable_branch}-dev"

    @property
    def release_branch(self) -> str:
        # Branch whose head the tag must be: dev for RCs, stable for finals.
        return self.dev_branch if self.is_prerelease else self.stable_branch


def parse_release_version(value: str) -> ReleaseVersion:
    match = _VERSION_PATTERN.fullmatch(value.strip())
    if match is None:
        raise ValueError(
            f"{value!r} is not a supported release version; use X.Y.Z for a "
            "final release or X.Y.Z-rc.N for a release candidate"
        )
    return ReleaseVersion(
        major=int(match.group("major")),
        minor=int(match.group("minor")),
        patch=int(match.group("patch")),
        rc=int(match.group("rc")) if match.group("rc") is not None else None,
    )


def validate_branch_version(branch: str, value: str) -> ReleaseVersion:
    branch_match = _BRANCH_PATTERN.fullmatch(branch)
    if branch_match is None:
        raise ValueError(
            f"{branch!r} is not a release branch; use vX.Y or vX.Y-dev"
        )

    version = parse_release_version(value)
    branch_line = (int(branch_match.group("major")), int(branch_match.group("minor")))
    if branch_line != (version.major, version.minor):
        raise ValueError(
            f"{version.normalized} belongs to v{version.major}.{version.minor}, "
            f"not {branch}"
        )

    if branch_match.group("dev") is None:
        raise ValueError(
            f"{version.normalized} must be cut from {version.dev_branch}; "
            f"{branch} only moves through release.sh --promote"
        )
    return version


_RED_CONCLUSIONS = frozenset({"failure", "timed_out", "startup_failure", "action_required"})


def assert_newer(value: str, existing: list[str]) -> ReleaseVersion:
    """Refuse a version that does not sort after every version already cut."""
    version = parse_release_version(value)
    for raw in existing:
        other = parse_release_version(raw)
        if other.sort_key >= version.sort_key:
            raise ValueError(
                f"{version.normalized} is not newer than {other.normalized}, "
                "which this line already has"
            )
    return version


def runs_verdict(conclusions: list[str]) -> str:
    """Summarize the workflow runs of one commit: green, red, pending or missing."""
    if any(conclusion in _RED_CONCLUSIONS for conclusion in conclusions):
        return "red"
    if "pending" in conclusions:
        return "pending"
    return "green" if "success" in conclusions else "missing"


def _usage() -> str:
    return (
        "usage: release_version.py normalize <version> | branch <version> | "
        "dev-branch <version> | stable-branch <version> | "
        "is-prerelease <version> | validate <branch> <version> | "
        "verify-tag <tag> <package-version> | "
        "assert-newer <version> [existing-version ...] | "
        "runs-verdict [conclusion ...]"
    )


def main(argv: list[str]) -> int:
    try:
        command = argv[1]
        if command == "normalize" and len(argv) == 3:
            print(parse_release_version(argv[2]).normalized)
        elif command == "branch" and len(argv) == 3:
            print(parse_release_version(argv[2]).release_branch)
        elif command == "dev-branch" and len(argv) == 3:
            print(parse_release_version(argv[2]).dev_branch)
        elif command == "stable-branch" and len(argv) == 3:
            print(parse_release_version(argv[2]).stable_branch)
        elif command == "is-prerelease" and len(argv) == 3:
            print("true" if parse_release_version(argv[2]).is_prerelease else "false")
        elif command == "validate" and len(argv) == 4:
            print(validate_branch_version(argv[2], argv[3]).normalized)
        elif command == "verify-tag" and len(argv) == 4:
            tag_version = parse_release_version(argv[2])
            package_version = parse_release_version(argv[3])
            if tag_version != package_version:
                raise ValueError(
                    f"tag {tag_version.normalized} does not match package "
                    f"version {package_version.normalized}"
                )
            print(tag_version.normalized)
        elif command == "assert-newer" and len(argv) >= 3:
            print(assert_newer(argv[2], argv[3:]).normalized)
        elif command == "runs-verdict":
            print(runs_verdict(argv[2:]))
        else:
            raise ValueError(_usage())
    except (IndexError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
