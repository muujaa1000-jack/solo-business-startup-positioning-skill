# Open Source Parity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring `solo-business-startup-positioning-skill` to the same open-source engineering maturity as `solo-business-validation-skill` and publish verified `v0.1.0` release artifacts.

**Architecture:** Keep the runtime Skill small and explicit while adding repository-only documentation, examples, evaluations, deterministic Python tooling, tests, and GitHub automation. Package only a fixed runtime whitelist, normalize text to LF, and fail closed on unsafe paths, private data, invalid metadata, version drift, or artifact mismatch.

**Tech Stack:** Markdown, YAML, JSON, Python 3.10+ standard library, `unittest`, GitHub Actions, GitHub CLI.

## Global Constraints

- Do not modify the `solo-business-validation-skill` repository.
- Do not change `SKILL.md`, `agents/openai.yaml`, or either reference unless a failing existing contract proves a real behavior gap.
- Keep the five evidence states, first-turn single-question contract, four candidate decision paths, six final-output gates, and seven-section handoff contract unchanged.
- Runtime release files are exactly `LICENSE`, `SKILL.md`, `agents/openai.yaml`, `references/interview-guide.md`, and `references/output-contract.md`.
- No runtime third-party dependency; all scripts use Python 3.10+ standard library only.
- All examples are fictional or composite and contain no identifying business or machine detail.
- Static tests do not claim model behavior; dated evidence remains in `docs/validation.md`.
- Version and tag are exactly `0.1.0` and `v0.1.0`.
- Release assets are exactly `interview-solo-business-startup-positioning-0.1.0.zip`, `interview-solo-business-startup-positioning-0.1.0.skill`, and `SHA256SUMS`.
- Pin every third-party GitHub Action to an immutable commit SHA.

## File Responsibility Map

- `README.md` / `README.zh-CN.md`: bilingual onboarding, compatibility, boundaries, and maintenance.
- `examples/`: fictional full and insufficient-evidence examples.
- `evals/`: public fresh-context behavior cases and methodology.
- `scripts/validate.py`: repository, metadata, schema, UTF-8, and privacy checks.
- `scripts/package.py`: deterministic ZIP and `.skill` builder.
- `scripts/verify_artifacts.py`: archive member, path, hash, UTF-8, identity, and checksum verifier.
- `tests/test_skill.py`: existing runtime behavior contracts.
- `tests/test_repository_contract.py`: public-repository and workflow contracts.
- `tests/test_packaging.py`: deterministic packaging and hostile-archive contracts.
- `.github/workflows/`: CI candidate builds and tag-triggered releases.

---

### Task 1: Public documentation, examples, evaluations, and governance

**Files:**
- Create: `README.zh-CN.md`, `CHANGELOG.md`, `CONTRIBUTING.md`, `SECURITY.md`, `VERSION`
- Create: `examples/complete-positioning.md`, `examples/insufficient-evidence.zh-CN.md`
- Create: `evals/README.md`, `evals/cases.json`, `tests/test_repository_contract.py`
- Modify: `README.md`

**Interfaces:**
- Consumes the exact terminology in the current Skill and references.
- Produces `VERSION=0.1.0` and five eval objects with `id`, `prompt`, `stage`, and `expected_behaviors`.

- [ ] **Step 1: Write the failing repository contract**

Create `tests/test_repository_contract.py` with these tests:

```python
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
```

Implement each method with real file reads. Require exactly five eval IDs in order: `no-direction`, `too-many-direct-choice-pressure`, `ai-core-advantage-pressure`, `reject-all`, `retain-multiple`. Require both READMEs to contain install, compatibility, development/release, evidence-boundary, and commercialization-validator sections. Require the SECURITY advisory URL to name this repository.

- [ ] **Step 2: Run RED**

Run: `python -X utf8 -m unittest tests.test_repository_contract -v`

Expected: assertion failures listing missing files; no import or syntax error.

- [ ] **Step 3: Add the minimum public content**

- Rewrite `README.md` as the English primary README and create a same-order Chinese mirror.
- Document Codex, Claude Code, and other Agent Skills hosts without claiming live behavior compatibility.
- Add a fictional full-positioning example with two or three candidates, explicit user choice, seven final sections, and a not-market-validated handoff card.
- Add a Chinese insufficient-evidence example showing the compliant one-question first turn and the after-one-answer staged stop.
- Add five eval cases; each behavior list has at least three observable requirements.
- Add eval instructions requiring no-Skill/with-Skill fresh contexts, five repetitions per case, manual review, and dated model-host claims.
- Add semantic-version changelog, contribution rules, and private security-reporting policy.

- [ ] **Step 4: Verify GREEN and regressions**

```powershell
python -X utf8 -m unittest tests.test_repository_contract -v
python -X utf8 -m unittest discover -s tests -p "test_*.py" -v
```

Expected: new repository contracts pass; all existing 24 Skill tests remain green.

- [ ] **Step 5: Commit Task 1**

```powershell
git add README.md README.zh-CN.md CHANGELOG.md CONTRIBUTING.md SECURITY.md VERSION examples evals tests/test_repository_contract.py
git commit -m "docs: complete public skill documentation"
```

---

### Task 2: Repository validator and privacy gates

**Files:**
- Create: `scripts/__init__.py`, `scripts/validate.py`
- Modify: `tests/test_repository_contract.py`

**Interfaces:**
- Produce `SKILL_NAME`, `RUNTIME_FILES`, `REQUIRED_FILES`, `normalized_runtime_bytes`, `parse_frontmatter`, `scan_text`, and `validate_repository`.
- Task 3 imports the runtime whitelist, normalization, repository validation, and text scanner.

- [ ] **Step 1: Add failing validator tests**

Add tests that run the missing CLI with subprocess and assert exit 0, so RED is an assertion failure. Add temporary-copy tests for invalid semver, wrong frontmatter, missing reference links, fewer than five evals, missing eval fields, invalid UTF-8, Windows and Unix home paths, a machine-specific Windows workspace path, private-key headers, GitHub tokens, and embedded secrets.

- [ ] **Step 2: Run RED**

Run: `python -X utf8 -m unittest tests.test_repository_contract.RepositoryContractTests.test_validator_cli_passes tests.test_repository_contract.RepositoryContractTests.test_validator_rejects_invalid_version_and_eval_schema tests.test_repository_contract.RepositoryContractTests.test_validator_detects_private_paths_and_tokens -v`

Expected: fail because `scripts/validate.py` is absent.

- [ ] **Step 3: Implement the minimum validator**

Use these public constants:

```python
SKILL_NAME = "interview-solo-business-startup-positioning"
RUNTIME_FILES = (
    "LICENSE",
    "SKILL.md",
    "agents/openai.yaml",
    "references/interview-guide.md",
    "references/output-contract.md",
)
REQUIRED_FILES = (*RUNTIME_FILES, "README.md", "README.zh-CN.md", "CHANGELOG.md",
                  "CONTRIBUTING.md", "SECURITY.md", "VERSION",
                  "evals/README.md", "evals/cases.json",
                  "examples/complete-positioning.md",
                  "examples/insufficient-evidence.zh-CN.md")
```

Implement the shared byte and frontmatter functions with these exact signatures:

```python
def normalized_runtime_bytes(root: Path, relative: str) -> bytes:
    data = (root / relative).read_bytes()
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")

def parse_frontmatter(skill_text: str) -> tuple[list[str], dict[str, str]]:
    match = re.match(r"\A---\n(.*?)\n---\n", skill_text, re.DOTALL)
    if not match:
        return [], {}
    keys, values = [], {}
    for line in match.group(1).splitlines():
        if line.strip() and not line.startswith((" ", "\t")) and ":" in line:
            key, value = line.split(":", 1)
            keys.append(key.strip())
            values[key.strip()] = value.strip().strip("'\"")
    return keys, values
```

Validate stable semver, exact frontmatter keys and name, `Use when` description, under-500-line Skill, both reference links, metadata invocation, unique exact eval fields, at least five cases, at least three nonempty behaviors, official compatibility links, UTF-8, and privacy patterns. Ignore `.git`, `dist`, `work`, outputs, caches, virtual environments, and editor directories.

- [ ] **Step 4: Verify GREEN**

```powershell
python -X utf8 scripts/validate.py
python -X utf8 -m unittest discover -s tests -p "test_*.py" -v
```

Expected: validator prints `[OK] repository validation passed`; all tests pass.

- [ ] **Step 5: Commit Task 2**

```powershell
git add scripts/__init__.py scripts/validate.py tests/test_repository_contract.py
git commit -m "test: add repository safety validation"
```

---

### Task 3: Deterministic release artifacts

**Files:**
- Create: `scripts/package.py`, `scripts/verify_artifacts.py`, `tests/test_packaging.py`

**Interfaces:**
- `build(root: Path, output_dir: Path) -> tuple[Path, Path, Path]`
- `expected_members() -> list[str]`
- `verify(root: Path, artifact: Path) -> list[str]`
- CLI package output directory and verifier artifact arguments.

- [ ] **Step 1: Write failing packaging tests**

Use subprocess for the initial missing-script failure, then real imports for final behavior. Cover two-build byte identity, ZIP/`.skill` identity, versioned names, exact sorted runtime member list, LF-only text, source hash equality, checksum accuracy, and valid verification. Add hostile archives for `../`, absolute paths, backslashes, extra members, invalid UTF-8, source mismatch, and checksum mismatch.

- [ ] **Step 2: Run RED**

Run: `python -X utf8 -m unittest tests.test_packaging -v`

Expected: assertion failure because packaging scripts are absent.

- [ ] **Step 3: Implement `package.py`**

Fail before writing when `validate_repository()` returns findings. Use timestamp `(1980,1,1,0,0,0)`, DEFLATE level 9, Unix mode `0o100644`, sorted explicit runtime files, LF-normalized bytes, and one top-level Skill directory. Copy ZIP bytes to `.skill`; write lowercase SHA-256 lines with LF.

The core builder is:

```python
FIXED_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)

def build(root: Path, output_dir: Path) -> tuple[Path, Path, Path]:
    findings = validate_repository(root)
    if findings:
        raise ValueError("repository validation failed:\n" + "\n".join(findings))
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / f"{SKILL_NAME}-{version}.zip"
    skill_path = output_dir / f"{SKILL_NAME}-{version}.skill"
    sums_path = output_dir / "SHA256SUMS"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative in sorted(RUNTIME_FILES):
            info = zipfile.ZipInfo(f"{SKILL_NAME}/{Path(relative).as_posix()}", FIXED_ZIP_TIMESTAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, normalized_runtime_bytes(root, relative))
    shutil.copyfile(zip_path, skill_path)
    digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    sums_path.write_text(
        f"{digest}  {zip_path.name}\n{digest}  {skill_path.name}\n",
        encoding="utf-8", newline="\n",
    )
    return zip_path, skill_path, sums_path
```

- [ ] **Step 4: Implement `verify_artifacts.py`**

Require exact ordered members; reject empty/absolute/backslash/dot/dot-dot paths; compare source hashes; decode UTF-8 and reuse privacy scanning; check SHA256SUMS; require ZIP and `.skill` byte identity; use exit 2 for missing arguments and exit 1 for findings.

Use this path predicate and exact member interface:

```python
def expected_members() -> list[str]:
    return [f"{SKILL_NAME}/{Path(item).as_posix()}" for item in sorted(RUNTIME_FILES)]

def _unsafe(name: str) -> bool:
    path = PurePosixPath(name)
    return (
        not name
        or name.startswith(("/", "\\"))
        or "\\" in name
        or any(part in {"", ".", ".."} for part in path.parts)
    )
```

- [ ] **Step 5: Verify GREEN and official structure**

```powershell
python -X utf8 -m unittest tests.test_packaging -v
python -X utf8 scripts/package.py
python -X utf8 scripts/verify_artifacts.py dist/*.zip dist/*.skill
python -X utf8 -m unittest discover -s tests -p "test_*.py" -v
```

Extract ZIP and `.skill` separately and run official `quick_validate.py` on each.

- [ ] **Step 6: Commit without generated `dist/`**

```powershell
git add scripts/package.py scripts/verify_artifacts.py tests/test_packaging.py
git commit -m "build: add deterministic skill packaging"
```

---

### Task 4: Source hygiene and GitHub automation

**Files:**
- Create: `.gitattributes`, `.github/workflows/ci.yml`, `.github/workflows/release.yml`
- Modify: `.gitignore`, `tests/test_repository_contract.py`
- Delete: `SHA256SUMS`, `dist/interview-solo-business-startup-positioning.zip`

**Interfaces:**
- CI consumes the test, validate, package, and verify commands from Tasks 1–3.
- Release consumes `VERSION` and publishes exactly the builder outputs.

- [ ] **Step 1: Add failing hygiene and workflow tests**

Require `.gitattributes` LF and binary rules; `.gitignore` for `dist/`, `.worktrees/`, work/output, virtualenvs, caches, editors, and OS files; absence of tracked stale artifacts; CI push-main/PR triggers, Python 3.10/3.12/3.14, tests, validation, two candidate builds, verification, comparison, and upload; Release `v*`, contents-write only, tag/VERSION gate, full verification, and create-or-update release. Require every `uses:` line to contain a 40-character SHA.

- [ ] **Step 2: Run RED**

Run: `python -X utf8 -m unittest tests.test_repository_contract.RepositoryContractTests.test_source_hygiene tests.test_repository_contract.RepositoryContractTests.test_ci_and_release_workflows_are_pinned_and_complete -v`

Expected: fail because attributes/workflows are missing and stale artifacts still exist.

- [ ] **Step 3: Implement source hygiene**

Add `* text=auto eol=lf`, `*.zip binary`, and `*.skill binary`. Expand `.gitignore` with the approved paths. Delete only the checked-in ZIP and root checksum; generated Release assets remain remote.

- [ ] **Step 4: Add pinned workflows**

Use immutable action SHAs already proven in the reference repository. CI runs the Python matrix and then builds into `work/build-one` and `work/build-two`, compares all three outputs byte-for-byte, verifies each set, and uploads one candidate set for seven days. Release checks tag equality to `v$(VERSION)`, reruns full validation, builds once, verifies, and uses `gh release create` or `gh release upload --clobber`.

- [ ] **Step 5: Verify GREEN**

```powershell
python -X utf8 -m unittest discover -s tests -p "test_*.py" -v
python -X utf8 scripts/validate.py
python -X utf8 scripts/package.py
python -X utf8 scripts/verify_artifacts.py dist/*.zip dist/*.skill
git diff --check
git status --short
```

Expected: tests and validation pass; generated `dist/` is ignored; only intended source files are modified.

- [ ] **Step 6: Commit Task 4**

```powershell
git add .gitattributes .gitignore .github tests/test_repository_contract.py
git add -u -- SHA256SUMS dist/interview-solo-business-startup-positioning.zip
git commit -m "ci: automate skill validation and releases"
```

---

### Task 5: Fresh full validation and independent review

**Files:**
- No planned source modification. A validated finding starts a focused fix task with exact files and its own RED-GREEN cycle.

**Interfaces:**
- Consumes every command and contract from Tasks 1–4.
- Produces a clean review-ready branch with no Critical or Important findings.

- [ ] **Step 1: Run the full matrix fresh**

```powershell
python -X utf8 -m unittest discover -s tests -p "test_*.py" -v
python -X utf8 scripts/validate.py
python -X utf8 scripts/package.py --output-dir work/build-one
python -X utf8 scripts/package.py --output-dir work/build-two
python -X utf8 scripts/verify_artifacts.py work/build-one/*.zip work/build-one/*.skill
python -X utf8 scripts/verify_artifacts.py work/build-two/*.zip work/build-two/*.skill
git diff --check origin/main...HEAD
git status --short --branch
```

Compare both build directories byte-for-byte. Extract ZIP and `.skill` into separate new directories and run official `quick_validate.py` on each.

- [ ] **Step 2: Audit public safety**

Scan tracked text for private keys, GitHub tokens, embedded secrets, user-home paths, machine-specific workspace paths, email addresses, phone numbers, and identifying operating evidence. Read every match manually; no unsafe match is allowed.

- [ ] **Step 3: Request whole-branch review**

Use base `origin/main`, current HEAD, the approved design, and this plan. Ask the reviewer to check runtime whitelist, bilingual parity, eval honesty, deterministic bytes, hostile archive handling, workflow permissions, tag gate, stale-artifact deletion, and behavior overclaims.

Fix every Critical and Important finding with a focused failing test first. Re-run review until it returns no merge-blocking finding.

- [ ] **Step 4: Handle review results**

If review reports no Critical or Important finding, proceed without another commit. If it reports one, stop this plan, append a focused fix task naming the exact files and failing test, execute that RED-GREEN cycle, and request review again before Task 6.

---

### Task 5A: Fix whole-branch review findings

**Files:**
- Modify: `evals/cases.json`, `evals/README.md`, `README.md`, `README.zh-CN.md`
- Modify: `scripts/validate.py`, `scripts/verify_artifacts.py`
- Modify: `.github/workflows/release.yml`
- Modify: `tests/test_repository_contract.py`, `tests/test_packaging.py`

**Required RED-GREEN slices:**

1. Add repository-contract tests proving `reject-all` and `retain-multiple` each carry a complete fictional prior interview/candidate state in their own prompt; then update the two cases and evaluation instructions.
2. Add temporary-repository tests that reject symlinked required/runtime files, resolved paths outside the repository, `/root/...`, `~/...`, and unquoted `api_key=...`; then harden validation without adding dependencies.
3. Add hostile archive tests for ZIP comments, member comments, and extra fields; then make artifact verification regenerate canonical bytes from source and require byte identity.
4. Add workflow-contract tests that require an existing release to have exactly the three expected asset names before and after upload; then add fail-closed remote asset-set checks.
5. Add bilingual README contracts for linked examples/evals, the exact three Release assets, deterministic package and artifact-verification commands; then update both mirrors in the same order without expanding compatibility claims.
6. Run the focused tests after each RED, then the entire Task 5 matrix, public-safety audit, and a new independent whole-branch review. Do not proceed to Task 6 while any Critical or Important finding remains.

---

### Task 6: Publish PR, merge, tag, and verify GitHub Release

**Files:**
- No source change unless remote CI exposes a locally reproducible defect with a failing test.

**Interfaces:**
- Branch: `agent/complete-open-source-scaffolding`
- PR base: `main`
- Tag: `v0.1.0`

- [ ] **Step 1: Confirm publish prerequisites**

Run `gh --version`, `gh auth status`, `git status -sb`, `git diff --stat origin/main...HEAD`, and `git remote -v`. Require account `muujaa1000-jack`, the intended repository, and a clean worktree.

- [ ] **Step 2: Push and open a draft PR**

```powershell
git push -u origin agent/complete-open-source-scaffolding
```

Create the PR through the GitHub connector. Summarize bilingual docs, examples/evals, deterministic tooling, CI/Release, stale-artifact removal, exact test output, official validation, and evidence limits.

- [ ] **Step 3: Wait for GitHub CI**

Require every Python matrix and package check to pass. For failure, inspect Actions logs, reproduce locally, add a failing test, fix, rerun, commit, and push.

- [ ] **Step 4: Mark ready and squash-merge**

Use the expected head SHA. Fetch `origin/main` afterward and require its tree to equal the reviewed PR tree.

- [ ] **Step 5: Create the release tag**

Before tagging, require `VERSION=0.1.0` and no existing remote tag.

```powershell
git switch main
git pull --ff-only
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin v0.1.0
```

- [ ] **Step 6: Verify the public Release**

Wait for the tag workflow. Require exactly `interview-solo-business-startup-positioning-0.1.0.zip`, `interview-solo-business-startup-positioning-0.1.0.skill`, and `SHA256SUMS`. Download all three into a fresh directory; verify checksums, ZIP/`.skill` identity, exact members, source hashes against tag `v0.1.0`, and official Skill validation after extraction.

- [ ] **Step 7: Report evidence boundaries**

Report repository, merged PR, release URL, tag commit, exact test count, workflow status, artifact names and SHA-256. State that full multi-turn/cross-model stability and real demand/payment/acquisition/delivery economics remain unverified, and no user-level installation was performed.
