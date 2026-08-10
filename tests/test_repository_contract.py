import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


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

    def test_validator_rejects_symlinked_required_files_before_reading(self) -> None:
        from scripts.validate import validate_repository

        temporary, copied_root = self.copied_repository()
        with temporary:
            runtime = copied_root / "SKILL.md"
            runtime_copy = copied_root / "SKILL.real.md"
            runtime.rename(runtime_copy)
            try:
                runtime.symlink_to(runtime_copy.name)
            except OSError:
                runtime_copy.rename(runtime)
                original_is_symlink = Path.is_symlink
                with mock.patch.object(
                    Path,
                    "is_symlink",
                    autospec=True,
                    side_effect=lambda path: (
                        True if path == runtime else original_is_symlink(path)
                    ),
                ):
                    self.assertIn(
                        "symbolic link", "\n".join(validate_repository(copied_root))
                    )
            else:
                self.assert_validator_rejects(copied_root, "symbolic link")
                runtime.unlink()
                runtime_copy.rename(runtime)

            if runtime_copy.exists():
                runtime_copy.rename(runtime)
            outside = Path(temporary.name) / "outside-readme.md"
            outside.write_bytes(b"\xff")
            required = copied_root / "README.md"
            required.unlink()
            try:
                required.symlink_to(outside)
            except OSError:
                source = ROOT / "README.md"
                shutil.copyfile(source, required)
                original_resolve = Path.resolve
                with mock.patch.object(
                    Path,
                    "resolve",
                    autospec=True,
                    side_effect=lambda path, *args, **kwargs: (
                        outside
                        if path == required
                        else original_resolve(path, *args, **kwargs)
                    ),
                ):
                    findings = "\n".join(validate_repository(copied_root))
                    self.assertIn("outside repository root", findings)
                    self.assertNotIn("UTF-8", findings)
            else:
                result = self.run_validator(copied_root)
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("outside repository root", result.stdout + result.stderr)
                self.assertNotIn("UTF-8", result.stdout + result.stderr)

    def test_validator_rejects_nonrequired_paths_resolving_outside_root(self) -> None:
        from scripts.validate import validate_repository

        temporary, copied_root = self.copied_repository()
        with temporary:
            outside = Path(temporary.name) / "outside-public.md"
            outside.write_bytes(b"\xff")
            public_path = copied_root / "docs/extra-public.md"
            try:
                public_path.symlink_to(outside)
            except OSError:
                public_path.write_text("safe local stand-in\n", encoding="utf-8")
                original_resolve = Path.resolve
                with mock.patch.object(
                    Path,
                    "resolve",
                    autospec=True,
                    side_effect=lambda path, *args, **kwargs: (
                        outside
                        if path == public_path
                        else original_resolve(path, *args, **kwargs)
                    ),
                ):
                    findings = "\n".join(validate_repository(copied_root))
            else:
                findings = "\n".join(validate_repository(copied_root))
            self.assertIn("docs/extra-public.md", findings)
            self.assertIn("outside repository root", findings)
            self.assertNotIn("UTF-8", findings)

    def test_validator_detects_root_tilde_and_unquoted_secrets(self) -> None:
        cases = [
            ("root home", "/" + "root/private.txt", "Unix home path"),
            ("tilde home", "~" + "/private.txt", "tilde home path"),
            (
                "unquoted secret",
                "api_" + "key=live-secret-value-12345",
                "embedded secret",
            ),
        ]
        for name, unsafe_text, expected in cases:
            with self.subTest(name=name):
                temporary, copied_root = self.copied_repository()
                with temporary:
                    readme = copied_root / "README.md"
                    readme.write_text(
                        readme.read_text(encoding="utf-8") + "\n" + unsafe_text,
                        encoding="utf-8",
                    )
                    self.assert_validator_rejects(copied_root, expected)

    def test_validator_allows_documented_secret_placeholders(self) -> None:
        from scripts.validate import scan_text

        safe_examples = "\n".join(
            (
                "api_" + "key=${API_KEY}",
                "api_" + "key=<YOUR_API_KEY>",
                "api_" + "key=placeholder",
                "token=$" + "{{ github.token }}",
            )
        )
        self.assertEqual([], scan_text("docs/example.md", safe_examples))
        result = self.run_validator(ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

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

    def test_readmes_link_public_evidence_and_exact_release_artifacts(self) -> None:
        english = (ROOT / "README.md").read_text(encoding="utf-8")
        chinese = (ROOT / "README.zh-CN.md").read_text(encoding="utf-8")
        for text in (english, chinese):
            for target in (
                "examples/complete-positioning.md",
                "examples/insufficient-evidence.zh-CN.md",
                "evals/README.md",
            ):
                self.assertRegex(text, rf"\[[^\]]+\]\({re.escape(target)}\)")
            self.assertIn(
                "python -X utf8 scripts/package.py --output-dir dist", text
            )
            self.assertIn(
                "python -X utf8 scripts/verify_artifacts.py "
                "dist/interview-solo-business-startup-positioning-0.1.0.zip "
                "dist/interview-solo-business-startup-positioning-0.1.0.skill",
                text,
            )

        expected_assets = [
            "interview-solo-business-startup-positioning-0.1.0.zip",
            "interview-solo-business-startup-positioning-0.1.0.skill",
            "SHA256SUMS",
        ]
        for text, heading in (
            (english, "### Release artifacts"),
            (chinese, "### Release 制品"),
        ):
            section = re.search(
                rf"(?ms)^{re.escape(heading)}\n(.*?)(?=^### |^## |\Z)", text
            )
            self.assertIsNotNone(section)
            self.assertEqual(
                expected_assets,
                re.findall(r"(?m)^- `([^`]+)`$", section.group(1)),
            )

        self.assertIn("not a claim of live installation", english)
        self.assertIn("不等于已声明某个宿主或版本安装成功", chinese)

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

    def test_candidate_decision_evals_are_self_contained_fictional_states(self) -> None:
        cases = {
            case["id"]: case
            for case in json.loads(
                (ROOT / "evals/cases.json").read_text(encoding="utf-8")
            )
        }
        required_prior_state = (
            "Fresh-context fictional scenario",
            "Current state:",
            "Interview goal:",
            "Experience:",
            "Capabilities:",
            "Resources:",
            "Interests:",
            "Reachable people:",
            "Constraints:",
            "Fictional candidates:",
            "Candidate A:",
            "Candidate B:",
            "User decision:",
        )
        for identifier in ("reject-all", "retain-multiple"):
            with self.subTest(case=identifier):
                prompt = cases[identifier]["prompt"]
                for phrase in required_prior_state:
                    self.assertIn(phrase, prompt)
                self.assertNotIn("After reviewing the candidates", prompt)
                candidate_a = prompt.split("Candidate A:", 1)[1].split(
                    "Candidate B:", 1
                )[0]
                candidate_b = prompt.split("Candidate B:", 1)[1].split(
                    "User decision:", 1
                )[0]
                for candidate in (candidate_a, candidate_b):
                    for field in (
                        "Identity:",
                        "Customer:",
                        "Problem:",
                        "Value:",
                        "Minimum product or service:",
                        "Pricing hypothesis:",
                        "Acquisition hypothesis:",
                        "Delivery:",
                        "Content or brand role:",
                        "Existing evidence:",
                        "Biggest unknown:",
                    ):
                        self.assertIn(field, candidate)

        evaluation = (ROOT / "evals/README.md").read_text(encoding="utf-8")
        self.assertIn("self-contained fictional prior state", evaluation)
        self.assertIn("does not prove that a multi-turn interview occurred", evaluation)

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

    def test_source_hygiene(self) -> None:
        attributes_path = ROOT / ".gitattributes"
        self.assertTrue(attributes_path.is_file(), ".gitattributes must exist")
        attributes = attributes_path.read_text(encoding="utf-8")
        self.assertEqual(
            ["* text=auto eol=lf", "*.zip binary", "*.skill binary"],
            attributes.splitlines(),
        )

        ignored = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        required_ignores = {
            "dist/", ".worktrees/", "work/", "output/", "outputs/",
            "cache/", "caches/", ".venv/", "venv/", "__pycache__/",
            "*.py[cod]", ".pytest_cache/", ".coverage", ".DS_Store",
            ".idea/", ".vscode/", "*.swp", "*~",
        }
        self.assertTrue(required_ignores.issubset(ignored), required_ignores - set(ignored))
        for legacy_path in (
            "SHA256SUMS",
            "dist/interview-solo-business-startup-positioning.zip",
        ):
            with self.subTest(legacy_path=legacy_path):
                result = subprocess.run(
                    ["git", "ls-files", "--error-unmatch", "--", legacy_path],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertNotEqual(
                    result.returncode,
                    0,
                    f"stale artifact remains tracked: {result.stdout}{result.stderr}",
                )

    def test_ci_and_release_workflows_are_pinned_and_complete(self) -> None:
        ci_path = ROOT / ".github/workflows/ci.yml"
        release_path = ROOT / ".github/workflows/release.yml"
        self.assertTrue(ci_path.is_file(), "CI workflow must exist")
        self.assertTrue(release_path.is_file(), "release workflow must exist")
        workflows = {
            "ci": ci_path.read_text(encoding="utf-8"),
            "release": release_path.read_text(encoding="utf-8"),
        }
        ci = workflows["ci"]
        release = workflows["release"]

        self.assertRegex(ci, r"push:\s*\n\s*branches: \[main\]")
        self.assertRegex(ci, r"(?m)^\s*pull_request:\s*$")
        ci_permissions = re.search(
            r"(?ms)^permissions:\n((?:  [^\n]+\n)+)", ci
        )
        self.assertIsNotNone(ci_permissions)
        self.assertEqual("contents: read\n", ci_permissions.group(1).strip() + "\n")
        for version in ("3.10", "3.12", "3.14"):
            self.assertIn(f'"{version}"', ci)
        for command in (
            'python -m unittest discover -s tests -p "test_*.py" -v',
            "python scripts/validate.py",
            "python scripts/package.py --output-dir work/build-one",
            "python scripts/package.py --output-dir work/build-two",
            "work/build-one",
            "work/build-two",
            "retention-days: 7",
        ):
            self.assertIn(command, ci)
        self.assertEqual(3, ci.count("cmp --silent"))
        self.assertGreaterEqual(ci.count("python scripts/verify_artifacts.py"), 2)
        self.assertIn("SHA256SUMS", ci)

        release_triggers = re.search(
            r"(?ms)^on:\n(.*?)(?=^[^ \n]|\Z)", release
        )
        self.assertIsNotNone(release_triggers)
        self.assertEqual(
            'push:\n    tags:\n      - "v*"',
            release_triggers.group(1).strip(),
        )
        release_permissions = re.search(
            r"(?ms)^permissions:\n((?:  [^\n]+\n)+)", release
        )
        self.assertIsNotNone(release_permissions)
        self.assertEqual(
            "contents: write\n", release_permissions.group(1).strip() + "\n"
        )
        for command in (
            'python -m unittest discover -s tests -p "test_*.py" -v',
            "python scripts/validate.py",
            "python scripts/package.py",
            "python scripts/verify_artifacts.py",
            "GITHUB_REF_NAME",
            "VERSION",
            "gh release create",
            "gh release upload",
            "--clobber",
            "SHA256SUMS",
        ):
            self.assertIn(command, release)

        tag_gate = re.search(
            r"(?ms)^      - name: Check tag matches VERSION\n(.*?)(?=^      - name:|\Z)",
            release,
        )
        self.assertIsNotNone(tag_gate)
        self.assertIn('version="$(tr -d \'\\r\\n\' < VERSION)"', tag_gate.group(1))
        self.assertIn(
            'if [[ "$GITHUB_REF_NAME" != "v${version}" ]]; then', tag_gate.group(1)
        )
        self.assertIn("exit 1", tag_gate.group(1))
        self.assertLess(
            release.index("Check tag matches VERSION"),
            release.index("Create or update GitHub Release"),
        )

        for asset_definition in (
            'zip_path="dist/${name}.zip"',
            'skill_path="dist/${name}.skill"',
            'sums_path="dist/SHA256SUMS"',
        ):
            self.assertIn(asset_definition, release)
        self.assertEqual(1, release.count("gh release upload"))
        self.assertEqual(1, release.count("gh release create"))
        self.assertRegex(
            release,
            r'(?m)^            gh release upload "\$GITHUB_REF_NAME" "\$zip_path" "\$skill_path" "\$sums_path" --clobber --repo "\$GITHUB_REPOSITORY"$',
        )
        self.assertRegex(
            release,
            r'(?m)^            gh release create "\$GITHUB_REF_NAME" "\$zip_path" "\$skill_path" "\$sums_path" \\$',
        )
        self.assertNotIn("dist/*", release)

        for name, workflow in workflows.items():
            with self.subTest(workflow=name):
                uses_lines = re.findall(r"(?m)^\s*uses:\s*(.+)$", workflow)
                self.assertTrue(uses_lines)
                for uses in uses_lines:
                    self.assertRegex(
                        uses,
                        r"^[^\s@]+@[0-9a-f]{40}(?:\s+#.*)?$",
                    )

    def test_existing_release_assets_are_fail_closed_before_and_after_upload(self) -> None:
        release = (ROOT / ".github/workflows/release.yml").read_text(
            encoding="utf-8"
        )
        for expected_name in (
            '"${name}.zip"',
            '"${name}.skill"',
            '"SHA256SUMS"',
        ):
            self.assertIn(expected_name, release)
        self.assertIn("expected_asset_names", release)
        self.assertIn("existing_assets", release)
        self.assertIn("unexpected_assets", release)
        self.assertIn("comm -13", release)
        self.assertIn("published_assets", release)
        self.assertIn('if [[ "$published_assets" != "$expected_assets" ]]; then', release)
        upload = release.index("gh release upload")
        self.assertLess(release.index("existing_assets"), upload)
        self.assertGreater(release.index("published_assets"), upload)
        self.assertGreaterEqual(
            release.count("--json assets --jq '.assets[].name'"), 2
        )
        self.assertNotIn("dist/*", release)
