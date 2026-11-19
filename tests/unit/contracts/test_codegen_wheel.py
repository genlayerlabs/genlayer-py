"""Exercise generated typing as a wheel consumer, not an editable install."""

from pathlib import Path
import shutil
import subprocess
import sys

import pytest


@pytest.mark.skipif(shutil.which("uv") is None, reason="Wheel check requires uv")
def test_generated_types_from_installed_wheel(tmp_path):
    repository = Path(__file__).resolve().parents[3]
    subprocess.run(
        ["uv", "build", "--out-dir", str(tmp_path)], cwd=repository, check=True
    )
    wheel = next(tmp_path.glob("*.whl"))
    subprocess.run(
        [
            "uv",
            "run",
            "--isolated",
            "--no-project",
            "--python",
            sys.executable,
            "--with",
            str(wheel),
            "--with",
            "mypy==2.4.1",
            "python",
            str(repository / "scripts/check-generated-types.py"),
        ],
        cwd=tmp_path,
        check=True,
    )
