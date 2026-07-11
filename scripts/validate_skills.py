#!/usr/bin/env python3
"""Validate repository-scoped Codex Skills for MNQVolumeAI."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


EXPECTED_PROJECT_SKILLS = {
    "dependency-governor",
    "quant-research-scout",
    "mbo-data-causality",
    "auction-feature-engineering",
    "quant-model-validation",
    "out-of-core-data-engineering",
    "execution-backtest-gate",
}

NAME_RE = re.compile(r"^[a-z][a-z0-9-]{2,63}$")
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{16,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
]
LEGACY_PATTERNS = [
    "/Users/abdallah/Desktop/Trading/QuantSystemFinal",
    "QuantSystemFinal",
    "legacy Python project",
]
MANDATORY_SECTIONS = [
    "## Trigger",
    "## Do Not Trigger",
    "## Required Workflow",
]


@dataclass(frozen=True)
class SkillDoc:
    path: Path
    name: str
    description: str
    body: str


def parse_front_matter(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError("missing opening YAML front matter delimiter")
    try:
        end = next(i for i, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration as exc:
        raise ValueError("missing closing YAML front matter delimiter") from exc

    meta: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            raise ValueError(f"invalid metadata line: {line!r}")
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip().strip("\"'")
        if not key:
            raise ValueError("empty metadata key")
        meta[key] = value
    body = "\n".join(lines[end + 1 :])
    return meta, body


def load_skill(path: Path) -> SkillDoc:
    meta, body = parse_front_matter(path)
    name = meta.get("name", "")
    description = meta.get("description", "")
    if not name:
        raise ValueError("missing name")
    if not description:
        raise ValueError("missing description")
    return SkillDoc(path=path, name=name, description=description, body=body)


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    agents_skill_root = root / ".agents" / "skills"
    codex_skill_root = root / ".codex" / "skills"
    if not agents_skill_root.is_dir():
        return [f"missing skills directory: {agents_skill_root}"]

    skill_files = sorted(agents_skill_root.glob("*/SKILL.md"))
    if codex_skill_root.is_dir():
        skill_files.extend(sorted(codex_skill_root.glob("*/SKILL.md")))
    project_skill_dirs = {p.parent.name for p in skill_files if p.parent.name in EXPECTED_PROJECT_SKILLS}
    missing = sorted(EXPECTED_PROJECT_SKILLS - project_skill_dirs)
    for name in missing:
        errors.append(f"missing required project skill: {name}")

    names: dict[str, Path] = {}
    for path in skill_files:
        rel = path.relative_to(root)
        try:
            skill = load_skill(path)
        except ValueError as exc:
            errors.append(f"{rel}: {exc}")
            continue

        if not NAME_RE.match(skill.name):
            errors.append(f"{rel}: invalid skill name {skill.name!r}")
        if skill.name in names:
            errors.append(f"{rel}: duplicate skill name {skill.name!r}; first seen at {names[skill.name]}")
        names[skill.name] = rel

        if skill.name in EXPECTED_PROJECT_SKILLS:
            if len(skill.description) < 40 or len(skill.description) > 260:
                errors.append(f"{rel}: description length must be 40-260 characters")
            if "Use " not in skill.description and "use " not in skill.description:
                errors.append(f"{rel}: description should contain a clear trigger")
            if "must not" not in skill.description.lower() and "do not" not in skill.description.lower():
                errors.append(f"{rel}: description should contain a non-trigger boundary")
        elif not skill.description.strip():
            errors.append(f"{rel}: missing non-empty description")

        text = path.read_text(encoding="utf-8")
        for pattern in LEGACY_PATTERNS:
            if pattern in text:
                errors.append(f"{rel}: forbidden legacy reference {pattern!r}")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f"{rel}: possible secret pattern")

        if skill.name in EXPECTED_PROJECT_SKILLS:
            for section in MANDATORY_SECTIONS:
                if section not in skill.body:
                    errors.append(f"{rel}: missing mandatory section {section}")
            if "fail closed" not in skill.body.lower() and skill.name in {
                "mbo-data-causality",
                "execution-backtest-gate",
            }:
                errors.append(f"{rel}: expected fail-closed language")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate repository Codex Skills.")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    errors = validate(args.root.resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Skill validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
