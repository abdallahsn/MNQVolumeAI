from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.validate_skills import EXPECTED_PROJECT_SKILLS, validate


class ValidateSkillsTests(unittest.TestCase):
    def test_repository_skills_are_valid(self) -> None:
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(validate(root), [])

    def test_missing_required_skill_is_reported(self) -> None:
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            shutil.copytree(root / ".agents", tmp_root / ".agents")
            missing = sorted(EXPECTED_PROJECT_SKILLS)[0]
            shutil.rmtree(tmp_root / ".agents" / "skills" / missing)
            errors = validate(tmp_root)
        self.assertTrue(any(f"missing required project skill: {missing}" in error for error in errors))

    def test_secret_pattern_is_reported(self) -> None:
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            shutil.copytree(root / ".agents", tmp_root / ".agents")
            skill = tmp_root / ".agents" / "skills" / "dependency-governor" / "SKILL.md"
            fixture_line = "api_" + "key = '" + "dummyvalue1234567890" + "'"
            skill.write_text(skill.read_text(encoding="utf-8") + f"\n{fixture_line}\n", encoding="utf-8")
            errors = validate(tmp_root)
        self.assertTrue(any("possible secret pattern" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
