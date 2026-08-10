"""Validate the public Skill repository before packaging or release."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


SKILL_NAME = "interview-solo-business-startup-positioning"
RUNTIME_FILES = (
    "LICENSE",
    "SKILL.md",
    "agents/openai.yaml",
    "references/interview-guide.md",
    "references/output-contract.md",
)
REQUIRED_FILES = (
    *RUNTIME_FILES,
    "README.md",
    "README.zh-CN.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    "VERSION",
    "evals/README.md",
    "evals/cases.json",
    "examples/complete-positioning.md",
    "examples/insufficient-evidence.zh-CN.md",
)

_IGNORED_DIRECTORIES = {
    ".git",
    ".idea",
    ".mypy_cache",
    ".nox",
    ".pytest_cache",
    ".ruff_cache",
    ".superpowers",
    ".tox",
    ".venv",
    ".vs",
    ".vscode",
    "__pycache__",
    "cache",
    "caches",
    "dist",
    "env",
    "node_modules",
    "output",
    "outputs",
    "venv",
    "work",
}
_SEMVER = re.compile(r"^(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)$")
_WINDOWS_HOME = re.compile(r"(?i)\b[a-z]:[\\/]+users[\\/]+[^\\/\s]+")
_UNIX_HOME = re.compile(r"(?<![:\w/])/(?:home|users)/[^/\s]+", re.IGNORECASE)
_LOCAL_PROJECT = re.compile(r"(?i)\b[a-z]:[\\/]+codex[\\/]+")
_PRIVATE_KEY = re.compile(r"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----")
_GITHUB_TOKEN = re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")
_EMBEDDED_SECRET = re.compile(
    r"(?im)\b(?:api[_-]?key|secret|token|password|passwd|access[_-]?key)"
    r"\b\s*[:=]\s*['\"][^'\"\r\n]{8,}['\"]"
)


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


def scan_text(relative: str, text: str) -> list[str]:
    """Return public-safety findings for one decoded repository text file."""
    checks = (
        (_WINDOWS_HOME, "Windows home path"),
        (_UNIX_HOME, "Unix home path"),
        (_LOCAL_PROJECT, "local project path"),
        (_PRIVATE_KEY, "private-key header"),
        (_GITHUB_TOKEN, "GitHub token"),
        (_EMBEDDED_SECRET, "embedded secret"),
    )
    return [f"{relative}: {label}" for pattern, label in checks if pattern.search(text)]


def _text_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative_parts = path.relative_to(root).parts
        if any(part in _IGNORED_DIRECTORIES for part in relative_parts):
            continue
        files.append(path)
    return files


def _interface_default_prompt(metadata: str) -> str | None:
    in_interface = False
    for line in metadata.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line == "interface:":
            in_interface = True
            continue
        if not in_interface:
            continue
        if not line.startswith((" ", "\t")):
            break
        match = re.match(r"^[ \t]+default_prompt:\s*(.*)$", line)
        if match:
            return match.group(1).strip().strip("'\"")
    return None


def validate_repository(root: Path) -> list[str]:
    """Return every repository contract or public-safety failure at *root*."""
    root = root.resolve()
    findings: list[str] = []
    for relative in REQUIRED_FILES:
        if not (root / relative).is_file():
            findings.append(f"{relative}: required file is missing")

    decoded: dict[str, str] = {}
    for path in _text_files(root):
        relative = path.relative_to(root).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            findings.append(f"{relative}: must be valid UTF-8")
            continue
        except OSError as error:
            findings.append(f"{relative}: cannot be read ({error})")
            continue
        decoded[relative] = text
        findings.extend(scan_text(relative, text))

    version = decoded.get("VERSION")
    if version is not None and not _SEMVER.fullmatch(version.strip()):
        findings.append("VERSION: must be a stable semantic version")

    skill_text = decoded.get("SKILL.md")
    if skill_text is not None:
        keys, frontmatter = parse_frontmatter(skill_text)
        if keys != ["name", "description"]:
            findings.append("SKILL.md: frontmatter keys must be exactly name and description")
        if frontmatter.get("name") != SKILL_NAME:
            findings.append("SKILL.md: frontmatter name must match the Skill name")
        description = frontmatter.get("description", "")
        if not description.startswith("Use when") or len(description) > 1024:
            findings.append("SKILL.md: description must start with 'Use when' and be at most 1024 characters")
        if len(skill_text.splitlines()) >= 500:
            findings.append("SKILL.md: must stay under 500 lines")
        for reference in (
            "references/interview-guide.md",
            "references/output-contract.md",
        ):
            if reference not in skill_text:
                findings.append(f"SKILL.md: missing {reference} reference link")

    metadata = decoded.get("agents/openai.yaml")
    if metadata is not None:
        default_prompt = _interface_default_prompt(metadata)
        if default_prompt is None or f"${SKILL_NAME}" not in default_prompt:
            findings.append(
                "agents/openai.yaml: interface.default_prompt must invoke the Skill by name"
            )

    cases_text = decoded.get("evals/cases.json")
    if cases_text is not None:
        try:
            cases = json.loads(cases_text)
        except json.JSONDecodeError as error:
            findings.append(f"evals/cases.json: invalid JSON ({error.msg})")
        else:
            if not isinstance(cases, list) or len(cases) < 5:
                findings.append("evals/cases.json: requires at least five cases")
            if isinstance(cases, list):
                ids: list[str] = []
                exact_fields = {"id", "prompt", "stage", "expected_behaviors"}
                for index, case in enumerate(cases):
                    prefix = f"evals/cases.json[{index}]"
                    if not isinstance(case, dict) or set(case) != exact_fields:
                        findings.append(f"{prefix}: fields must be exactly {sorted(exact_fields)}")
                        continue
                    identifier = case["id"]
                    if not isinstance(identifier, str) or not identifier.strip():
                        findings.append(f"{prefix}: id must be a nonempty string")
                    else:
                        ids.append(identifier)
                    for field in ("prompt", "stage"):
                        if not isinstance(case[field], str) or not case[field].strip():
                            findings.append(f"{prefix}: {field} must be a nonempty string")
                    behaviors = case["expected_behaviors"]
                    if (
                        not isinstance(behaviors, list)
                        or len(behaviors) < 3
                        or any(not isinstance(item, str) or not item.strip() for item in behaviors)
                    ):
                        findings.append(f"{prefix}: expected_behaviors needs at least three nonempty behaviors")
                if len(ids) != len(set(ids)):
                    findings.append("evals/cases.json: case ids must be unique")

    readme = decoded.get("README.md", "")
    for url in (
        "https://developers.openai.com/codex/skills/",
        "https://docs.anthropic.com/en/docs/claude-code",
        "https://agentskills.io/specification",
    ):
        if url not in readme:
            findings.append(f"README.md: missing official compatibility link {url}")
    return findings


def main() -> int:
    findings = validate_repository(Path(__file__).resolve().parents[1])
    if findings:
        for finding in findings:
            print(f"[FAIL] {finding}")
        return 1
    print("[OK] repository validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
