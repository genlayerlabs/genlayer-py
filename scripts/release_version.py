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
    def release_branch(self) -> str:
        suffix = "-dev" if self.is_prerelease else ""
        return f"v{self.major}.{self.minor}{suffix}"


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

    branch_is_dev = branch_match.group("dev") is not None
    if branch_is_dev and not version.is_prerelease:
        raise ValueError(f"final release {version.normalized} must be cut from v{version.major}.{version.minor}")
    if not branch_is_dev and version.is_prerelease:
        raise ValueError(
            f"release candidate {version.normalized} must be cut from "
            f"v{version.major}.{version.minor}-dev"
        )
    return version


def _usage() -> str:
    return (
        "usage: release_version.py normalize <version> | branch <version> | "
        "is-prerelease <version> | validate <branch> <version> | "
        "verify-tag <tag> <package-version>"
    )


def main(argv: list[str]) -> int:
    try:
        command = argv[1]
        if command == "normalize" and len(argv) == 3:
            print(parse_release_version(argv[2]).normalized)
        elif command == "branch" and len(argv) == 3:
            print(parse_release_version(argv[2]).release_branch)
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
        else:
            raise ValueError(_usage())
    except (IndexError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
