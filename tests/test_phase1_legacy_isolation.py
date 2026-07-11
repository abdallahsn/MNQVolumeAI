from __future__ import annotations

from pathlib import Path


def test_no_phase1_source_imports_or_depends_on_legacy_project() -> None:
    root = Path(__file__).resolve().parents[1]
    forbidden = ["QuantSystemFinal", "sys.path.append", "sys.path.insert"]
    files = list((root / "src").rglob("*.py")) + [root / "pyproject.toml"]

    offenders: list[str] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                offenders.append(f"{path.relative_to(root)} contains {token}")

    assert offenders == []
