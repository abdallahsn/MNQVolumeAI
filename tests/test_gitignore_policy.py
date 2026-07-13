"""Repository ignore-policy regressions."""

from __future__ import annotations

import subprocess
from pathlib import Path


def test_source_data_package_is_not_ignored() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        ["git", "check-ignore", "--no-index", "-v", "src/mnq_ai/data/trade_extractor.py"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1, result.stdout or result.stderr
