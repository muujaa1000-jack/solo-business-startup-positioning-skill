import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RepositoryContractTests(unittest.TestCase):
    def run_validator(self, root: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-X", "utf8", "scripts/validate.py"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )

    def copied_repository(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        copied_root = Path(temporary.name) / "repository"
        shutil.copytree(
            ROOT,
            copied_root,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
        )
        return temporary, copied_root

    def assert_validator_rejects(self, root: Path, expected: str) -> None:
        result = self.run_validator(root)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(expected, result.stdout + result.stderr)

    def test_validator_cli_passes(self) -> None:
        result = self.run_validator(ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("[OK] repository validation passed", result.stdout)

    def test_validator_rejects_invalid_version_and_eval_schema(self) -> None:
        cases: list[tuple[str, object, str]] = [
            ("invalid semver", lambda root: (root / "VERSION").write_text("0.1\n", encoding="utf-8"), "VERSION"),
            ("fewer than five evals", lambda root: (root / "evals/cases.json").write_text("[]\n", encoding="utf-8"), "at least five"),
            ("missing eval field", self.remove_eval_field, "exactly"),
        ]
        for name, mutate, expected in cases:
            with self.subTest(name=name):
                temporary, copied_root = self.copied_repository()
                with temporary:
                    mutate(copied_root)
                    self.assert_validator_rejects(copied_root, expected)

    def remove_eval_field(self, root: Path) -> None:
        cases = json.loads((root / "evals/cases.json").read_text(encoding="utf-8"))
        del cases[0]["stage"]
        (root / "evals/cases.json").write_text(
            json.dumps(cases), encoding="utf-8"
        )

    def test_validator_rejects_contract_and_encoding_defects(self) -> None:
        cases: list[tuple[str, object, str]] = [
            (
                "wrong frontmatter",
                lambda root: (root / "SKILL.md").write_text(
                    (root / "SKILL.md").read_text(encoding="utf-8").replace(
                        "name: interview-solo-business-startup-positioning",
                        "name: incorrect-skill-name",
                        1,
                    ),
                    encoding="utf-8",
                ),
                "frontmatter",
            ),
            (
                "missing interview guide link",
                lambda root: (root / "SKILL.md").write_text(
                    (root / "SKILL.md").read_text(encoding="utf-8").replace(
                        "`references/interview-guide.md`", "interview guide"
                    ),
                    encoding="utf-8",
                ),
                "interview-guide",
            ),
            (
                "missing output contract link",
                lambda root: (root / "SKILL.md").write_text(
                    (root / "SKILL.md").read_text(encoding="utf-8").replace(
                        "`references/output-contract.md`", "output contract"
                    ),
                    encoding="utf-8",
                ),
                "output-contract",
            ),
            (
                "invalid utf8",
                lambda root: (root / "README.md").write_bytes(b"\xff\xfe"),
                "UTF-8",
            ),
        ]
        for name, mutate, expected in cases:
            with self.subTest(name=name):
                temporary, copied_root = self.copied_repository()
                with temporary:
                    mutate(copied_root)
                    self.assert_validator_rejects(copied_root, expected)

    def test_validator_rejects_remaining_frontmatter_and_skill_defects(self) -> None:
        cases = [
            (
                "extra frontmatter key",
                lambda root: (root / "SKILL.md").write_text(
                    (root / "SKILL.md").read_text(encoding="utf-8").replace(
                        "description:", "extra: value\ndescription:", 1
                    ),
                    encoding="utf-8",
                ),
                "frontmatter keys",
            ),
            (
                "description does not use trigger wording",
                lambda root: (root / "SKILL.md").write_text(
                    (root / "SKILL.md").read_text(encoding="utf-8").replace(
                        "description: Use when", "description: Apply when", 1
                    ),
                    encoding="utf-8",
                ),
                "description must start",
            ),
            (
                "skill is too long",
                lambda root: (root / "SKILL.md").write_text(
                    (root / "SKILL.md").read_text(encoding="utf-8")
                    + ("extra line\n" * 500),
                    encoding="utf-8",
                ),
                "under 500 lines",
            ),
        ]
        for name, mutate, expected in cases:
            with self.subTest(name=name):
                temporary, copied_root = self.copied_repository()
                with temporary:
                    mutate(copied_root)
                    self.assert_validator_rejects(copied_root, expected)

    def test_validator_requires_metadata_default_prompt_invocation(self) -> None:
        cases = [
            (
                "invocation only in comment",
                lambda root: (root / "agents/openai.yaml").write_text(
                    "# $interview-solo-business-startup-positioning\n"
                    "interface:\n"
                    "  default_prompt: \"Start the interview.\"\n",
                    encoding="utf-8",
                ),
            ),
            (
                "invocation only in unrelated field",
                lambda root: (root / "agents/openai.yaml").write_text(
                    "interface:\n"
                    "  note: \"$interview-solo-business-startup-positioning\"\n"
                    "  default_prompt: \"Start the interview.\"\n",
                    encoding="utf-8",
                ),
            ),
            (
                "missing invocation",
                lambda root: (root / "agents/openai.yaml").write_text(
                    "interface:\n  default_prompt: \"Start the interview.\"\n",
                    encoding="utf-8",
                ),
            ),
        ]
        for name, mutate in cases:
            with self.subTest(name=name):
                temporary, copied_root = self.copied_repository()
                with temporary:
                    mutate(copied_root)
                    self.assert_validator_rejects(copied_root, "default_prompt")

    def test_validator_rejects_nested_metadata_default_prompt_decoy(self) -> None:
        temporary, copied_root = self.copied_repository()
        with temporary:
            (copied_root / "agents/openai.yaml").write_text(
                "interface:\n"
                "  other:\n"
                "    default_prompt: \"$interview-solo-business-startup-positioning\"\n"
                "  default_prompt: \"Start the interview.\"\n",
                encoding="utf-8",
            )
            self.assert_validator_rejects(copied_root, "default_prompt")

    def test_validator_rejects_remaining_eval_defects(self) -> None:
        cases = [
            ("duplicate id", self.duplicate_eval_id, "ids must be unique"),
            ("too few behaviors", self.shorten_behaviors, "at least three"),
            ("non-string behavior", self.make_behavior_non_string, "nonempty behaviors"),
            ("blank behavior", self.make_behavior_blank, "nonempty behaviors"),
            (
                "malformed json",
                lambda root: (root / "evals/cases.json").write_text("[", encoding="utf-8"),
                "invalid JSON",
            ),
        ]
        for name, mutate, expected in cases:
            with self.subTest(name=name):
                temporary, copied_root = self.copied_repository()
                with temporary:
                    mutate(copied_root)
                    self.assert_validator_rejects(copied_root, expected)

    def duplicate_eval_id(self, root: Path) -> None:
        cases = json.loads((root / "evals/cases.json").read_text(encoding="utf-8"))
        cases[1]["id"] = cases[0]["id"]
        (root / "evals/cases.json").write_text(json.dumps(cases), encoding="utf-8")

    def shorten_behaviors(self, root: Path) -> None:
        cases = json.loads((root / "evals/cases.json").read_text(encoding="utf-8"))
        cases[0]["expected_behaviors"] = cases[0]["expected_behaviors"][:2]
        (root / "evals/cases.json").write_text(json.dumps(cases), encoding="utf-8")

    def make_behavior_non_string(self, root: Path) -> None:
        cases = json.loads((root / "evals/cases.json").read_text(encoding="utf-8"))
        cases[0]["expected_behaviors"][0] = 7
        (root / "evals/cases.json").write_text(json.dumps(cases), encoding="utf-8")

    def make_behavior_blank(self, root: Path) -> None:
        cases = json.loads((root / "evals/cases.json").read_text(encoding="utf-8"))
        cases[0]["expected_behaviors"][0] = "   "
        (root / "evals/cases.json").write_text(json.dumps(cases), encoding="utf-8")

    def test_validator_requires_official_compatibility_links(self) -> None:
        links = [
            "https://developers.openai.com/codex/skills/",
            "https://docs.anthropic.com/en/docs/claude-code",
            "https://agentskills.io/specification",
        ]
        for link in links:
            with self.subTest(link=link):
                temporary, copied_root = self.copied_repository()
                with temporary:
                    readme = copied_root / "README.md"
                    readme.write_text(
                        readme.read_text(encoding="utf-8").replace(link, ""),
                        encoding="utf-8",
                    )
                    self.assert_validator_rejects(copied_root, "official compatibility")

    def test_validator_detects_windows_slash_paths_and_documentation(self) -> None:
        cases = [
            ("windows home with slash", "C:" + "/" + "Users/Ada/secret.txt", "Windows home path"),
            ("workspace with slash", "D:" + "/codex/project/private.txt", "local project path"),
            ("documentation path", "D:" + "/codex/project/private.txt", "local project path"),
        ]
        for name, private_text, expected in cases:
            with self.subTest(name=name):
                temporary, copied_root = self.copied_repository()
                with temporary:
                    target = (
                        copied_root / "docs/validation.md"
                        if name == "documentation path"
                        else copied_root / "README.md"
                    )
                    target.write_text(
                        target.read_text(encoding="utf-8") + "\n" + private_text,
                        encoding="utf-8",
                    )
                    self.assert_validator_rejects(copied_root, expected)

    def test_validator_ignores_generated_and_local_tool_directories(self) -> None:
        ignored_directories = [
            ".git", "dist", "work", "output", "outputs", "cache", "caches",
            "__pycache__", ".pytest_cache", ".venv", "venv", ".idea", ".vscode",
        ]
        private_text = "D:" + "/codex/project/private.txt"
        for directory in ignored_directories:
            with self.subTest(directory=directory):
                temporary, copied_root = self.copied_repository()
                with temporary:
                    target = copied_root / directory / "generated.txt"
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(private_text, encoding="utf-8")
                    result = self.run_validator(copied_root)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_validator_handles_unreadable_required_path_gracefully(self) -> None:
        temporary, copied_root = self.copied_repository()
        with temporary:
            readme = copied_root / "README.md"
            readme.unlink()
            readme.mkdir()
            self.assert_validator_rejects(copied_root, "required file is missing")

    def test_validator_detects_private_paths_and_tokens(self) -> None:
        cases = [
            ("windows home", "C:" + r"\Users\Ada\secret.txt", "Windows home path"),
            ("unix home", "/" + "home/ada/secret.txt", "Unix home path"),
            ("project path", "D:" + r"\codex\project\private.txt", "local project path"),
            ("private key", "-----BEGIN " + "PRIVATE KEY-----", "private-key header"),
            ("github token", "gh" + "p_abcdefghijklmnopqrstuvwxyz1234567890ABCD", "GitHub token"),
            ("embedded secret", "api_" + "key = 'super-secret-value'", "embedded secret"),
        ]
        for name, secret, expected in cases:
            with self.subTest(name=name):
                temporary, copied_root = self.copied_repository()
                with temporary:
                    (copied_root / "README.md").write_text(
                        (copied_root / "README.md").read_text(encoding="utf-8")
                        + "\n"
                        + secret
                        + "\n",
                        encoding="utf-8",
                    )
                    self.assert_validator_rejects(copied_root, expected)

    def test_validator_detects_fine_grained_github_token(self) -> None:
        temporary, copied_root = self.copied_repository()
        with temporary:
            readme = copied_root / "README.md"
            token = "github" + "_pat_" + ("A" * 40)
            readme.write_text(
                readme.read_text(encoding="utf-8") + "\n" + token,
                encoding="utf-8",
            )
            self.assert_validator_rejects(copied_root, "GitHub token")

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
