import json
import re
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
        self.assertEqual(
            [
                "## Who it is for",
                "## Install",
                "## Start an interview",
                "## What the interview produces",
                "## Commercialization validator",
                "## Compatibility and verification",
                "## Evidence boundaries",
                "## Develop and release",
                "## License",
            ],
            re.findall(r"^## .+$", english, re.MULTILINE),
        )
        self.assertEqual(
            [
                "## 适合谁",
                "## 安装",
                "## 开始访谈",
                "## 访谈会产出什么",
                "## 商业化验证器",
                "## 兼容性与验证边界",
                "## 证据边界",
                "## 开发与发布",
                "## 许可证",
            ],
            re.findall(r"^## .+$", chinese, re.MULTILINE),
        )
        self.assertIn("solo-business-validation-skill", english)
        self.assertIn("solo-business-validation-skill", chinese)

    def test_examples_are_explicitly_fictional_and_public_safe(self) -> None:
        complete = (ROOT / "examples/complete-positioning.md").read_text(
            encoding="utf-8"
        )
        insufficient = (
            ROOT / "examples/insufficient-evidence.zh-CN.md"
        ).read_text(encoding="utf-8")
        self.assertIn("fictional", complete.lower())
        self.assertIn("public-safe", complete.lower())
        self.assertIn("虚构", insufficient)
        self.assertIn("公开安全", insufficient)
        self.assertIn("待验证假设", insufficient)
        self.assertIn("不等于市场已验证", complete + insufficient)

    def test_insufficient_evidence_example_preserves_turn_boundaries(self) -> None:
        insufficient = (
            ROOT / "examples/insufficient-evidence.zh-CN.md"
        ).read_text(encoding="utf-8")
        first_turn = re.search(
            r"\*\*Skill 合规回复：\*\*\s*(.*?)\n\n这是首轮",
            insufficient,
            re.DOTALL,
        )
        self.assertIsNotNone(first_turn)
        self.assertEqual(
            "你现在是完全没有方向，还是方向太多难以选择？",
            first_turn.group(1).strip(),
        )
        for phrase in (
            "阶段性定位假设",
            "现有依据",
            "最大缺口",
            "最值得补充的一项信息",
            "不生成候选比较、使用者选择、完整定位组合或商业验证交接卡",
        ):
            self.assertIn(phrase, insufficient)

    def test_complete_example_has_choice_seven_sections_and_handoff(self) -> None:
        complete = (ROOT / "examples/complete-positioning.md").read_text(
            encoding="utf-8"
        )
        candidates = complete.split("After one question per turn", 1)[1].split(
            "The participant explicitly chooses", 1
        )[0]
        candidate_rows = [
            line for line in candidates.splitlines()
            if line.startswith("| ")
            and not line.startswith("| Candidate |")
            and not line.startswith("|---")
        ]
        self.assertGreaterEqual(len(candidate_rows), 2)
        self.assertLessEqual(len(candidate_rows), 3)
        self.assertIn("The participant explicitly chooses", complete)
        self.assertEqual(
            [
                "### 当前访谈结论",
                "### 创始人底盘",
                "### 机会线索",
                "### 候选定位比较",
                "### 使用者选择",
                "### 完整定位组合",
                "### 商业验证交接卡",
            ],
            re.findall(r"^### .+$", complete, re.MULTILINE),
        )
        self.assertIn("solo-business-validation-skill", complete)
        self.assertIn("does not equal market validation", complete)

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

    def test_eval_method_requires_fresh_manual_dated_review(self) -> None:
        evaluation = (ROOT / "evals/README.md").read_text(encoding="utf-8")
        for phrase in (
            "fresh contexts",
            "without the Skill",
            "with the Skill",
            "five repetitions per case",
            "manual review",
            "date, model, host",
            "model-host combination",
            "do not generalize",
        ):
            self.assertIn(phrase, evaluation)

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
