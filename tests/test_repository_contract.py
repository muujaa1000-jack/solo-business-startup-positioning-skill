import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RepositoryContractTests(unittest.TestCase):
    def test_public_project_files_exist(self) -> None:
        required = {
            "README.md", "README.zh-CN.md", "CHANGELOG.md",
            "CONTRIBUTING.md", "SECURITY.md", "VERSION",
            "examples/complete-positioning.md",
            "examples/insufficient-evidence.zh-CN.md",
            "evals/README.md", "evals/cases.json",
        }
        actual = {
            path.relative_to(ROOT).as_posix()
            for path in ROOT.rglob("*")
            if path.is_file()
        }
        self.assertTrue(required.issubset(actual), sorted(required - actual))

    def test_version_is_initial_release(self) -> None:
        self.assertEqual(
            "0.1.0", (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        )

    def test_readmes_cover_same_public_contract(self) -> None:
        english = (ROOT / "README.md").read_text(encoding="utf-8")
        chinese = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        for phrase in (
            "## Install", "## Compatibility and verification",
            "## Develop and release", "solo-business-validation-skill",
        ):
            self.assertIn(phrase, english)
        for phrase in (
            "## 安装", "## 兼容性与验证边界",
            "## 开发与发布", "solo-business-validation-skill",
        ):
            self.assertIn(phrase, chinese)

    def test_examples_are_bounded_and_fictional(self) -> None:
        complete = (ROOT / "examples/complete-positioning.md").read_text(
            encoding="utf-8"
        )
        insufficient = (
            ROOT / "examples/insufficient-evidence.zh-CN.md"
        ).read_text(encoding="utf-8")
        self.assertIn("fictional", complete.lower())
        self.assertIn("待验证假设", insufficient)
        self.assertIn("不等于市场已验证", complete + insufficient)

    def test_eval_schema_and_cases(self) -> None:
        cases = json.loads((ROOT / "evals/cases.json").read_text(encoding="utf-8"))
        self.assertEqual(
            [
                "no-direction", "too-many-direct-choice-pressure",
                "ai-core-advantage-pressure", "reject-all", "retain-multiple",
            ],
            [case["id"] for case in cases],
        )
        for case in cases:
            self.assertEqual(
                {"id", "prompt", "stage", "expected_behaviors"}, set(case)
            )
            self.assertGreaterEqual(len(case["expected_behaviors"]), 3)

    def test_maintenance_docs_are_project_specific(self) -> None:
        contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
        security = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
        changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn("positioning", contributing.lower())
        self.assertIn(
            "solo-business-startup-positioning-skill/security/advisories/new",
            security,
        )
        self.assertIn("## [0.1.0] - 2026-08-10", changelog)
