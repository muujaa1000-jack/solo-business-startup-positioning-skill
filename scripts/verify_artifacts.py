"""Fail-closed verification for deterministic public release artifacts."""

from __future__ import annotations

import hashlib
import sys
import tempfile
import zipfile
from pathlib import Path

try:
    from scripts.package import FIXED_ZIP_TIMESTAMP, build
    from scripts.validate import RUNTIME_FILES, SKILL_NAME, normalized_runtime_bytes, scan_text
except ModuleNotFoundError:
    from package import FIXED_ZIP_TIMESTAMP, build  # type: ignore[no-redef]
    from validate import (  # type: ignore[no-redef]
        RUNTIME_FILES,
        SKILL_NAME,
        normalized_runtime_bytes,
        scan_text,
    )


_READ_CHUNK_SIZE = 64 * 1024


def expected_members() -> list[str]:
    return [
        f"{SKILL_NAME}/{Path(item).as_posix()}" for item in sorted(RUNTIME_FILES)
    ]


def _unsafe(name: str) -> bool:
    parts = name.split("/")
    return (
        not name
        or name.startswith(("/", "\\"))
        or "\\" in name
        or (len(name) >= 2 and name[0].isalpha() and name[1] == ":")
        or any(part in {"", ".", ".."} for part in parts)
    )


def _artifact_paths(root: Path, artifact: Path) -> tuple[Path, Path, list[str]]:
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    zip_path = artifact.parent / f"{SKILL_NAME}-{version}.zip"
    skill_path = artifact.parent / f"{SKILL_NAME}-{version}.skill"
    findings: list[str] = []
    if artifact.suffix not in {".zip", ".skill"}:
        findings.append(f"{artifact}: unsupported artifact extension")
    expected_name = zip_path.name if artifact.suffix == ".zip" else skill_path.name
    if artifact.name != expected_name:
        findings.append(f"{artifact.name}: does not use the versioned release name")
    return zip_path, skill_path, findings


def _verify_checksums(zip_path: Path, skill_path: Path) -> list[str]:
    sums_path = zip_path.parent / "SHA256SUMS"
    if not sums_path.is_file():
        return ["SHA256SUMS: required checksum manifest is missing"]
    try:
        digest = _sha256_file(zip_path)
        skill_digest = _sha256_file(skill_path)
        actual = sums_path.read_bytes()
    except OSError as error:
        return [f"SHA256SUMS: cannot be read ({error})"]
    expected = (
        f"{digest}  {zip_path.name}\n{skill_digest}  {skill_path.name}\n"
    ).encode("ascii")
    if actual != expected:
        return ["SHA256SUMS: does not exactly match the release artifacts"]
    return []


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(_READ_CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


def _files_are_byte_identical(left: Path, right: Path) -> bool:
    if left.stat().st_size != right.stat().st_size:
        return False
    with left.open("rb") as left_stream, right.open("rb") as right_stream:
        while True:
            left_chunk = left_stream.read(_READ_CHUNK_SIZE)
            right_chunk = right_stream.read(_READ_CHUNK_SIZE)
            if left_chunk != right_chunk:
                return False
            if not left_chunk:
                return True


def _verify_canonical_archive(root: Path, artifact: Path) -> tuple[list[str], bool]:
    """Compare safely with a fresh build and say whether content inspection is bounded."""
    with tempfile.TemporaryDirectory() as directory:
        canonical_path, _, _ = build(root, Path(directory))
        canonical_size = canonical_path.stat().st_size
        artifact_size = artifact.stat().st_size
        if artifact_size != canonical_size:
            finding = (
                "artifact canonical bytes: canonical size is "
                f"{canonical_size} bytes, got {artifact_size}"
            )
            inspection_limit = max(canonical_size * 2, canonical_size + 1_000_000)
            return [finding], artifact_size <= inspection_limit
        if not _files_are_byte_identical(artifact, canonical_path):
            return ["artifact canonical bytes: must exactly match a fresh source build"], True
        return [], True


def verify(root: Path, artifact: Path) -> list[str]:
    """Return all validation findings without extracting an untrusted archive."""
    root = root.resolve()
    artifact = artifact.resolve()
    findings: list[str] = []
    try:
        zip_path, skill_path, path_findings = _artifact_paths(root, artifact)
    except (OSError, UnicodeDecodeError) as error:
        return [f"VERSION: cannot determine release artifact names ({error})"]
    findings.extend(path_findings)

    if not artifact.is_file():
        return [*findings, f"{artifact}: artifact is missing"]
    try:
        canonical_findings, safe_to_inspect = _verify_canonical_archive(root, artifact)
        findings.extend(canonical_findings)
    except (OSError, ValueError) as error:
        findings.append(f"artifact canonical bytes: cannot regenerate ({error})")
        safe_to_inspect = False
    if not safe_to_inspect:
        return findings
    if not zip_path.is_file() or not skill_path.is_file():
        findings.append("release pair: both versioned ZIP and .skill files are required")
    else:
        try:
            if not _files_are_byte_identical(zip_path, skill_path):
                findings.append("release pair: ZIP and .skill must be byte-identical")
        except OSError as error:
            findings.append(f"release pair: cannot read artifact bytes ({error})")
        findings.extend(_verify_checksums(zip_path, skill_path))

    try:
        with zipfile.ZipFile(artifact) as archive:
            infos = archive.infolist()
            if archive.comment:
                findings.append("archive comment: must be empty")
            names = [info.filename for info in infos]
            for name in names:
                if _unsafe(name):
                    findings.append(f"archive member {name!r}: unsafe path")
            required = expected_members()
            if names != required:
                findings.append("archive members: must exactly match the ordered runtime whitelist")
                return findings

            for info in infos:
                relative = info.filename.split("/", 1)[1]
                if info.comment:
                    findings.append(f"{info.filename}: member comment must be empty")
                if info.extra:
                    findings.append(f"{info.filename}: member extra field must be empty")
                if info.date_time != FIXED_ZIP_TIMESTAMP:
                    findings.append(f"{info.filename}: timestamp is not deterministic")
                if info.create_system != 3 or (info.external_attr >> 16) != 0o100644:
                    findings.append(f"{info.filename}: Unix file mode must be 0o100644")
                if info.compress_type != zipfile.ZIP_DEFLATED:
                    findings.append(f"{info.filename}: must use DEFLATE compression")
                try:
                    source = normalized_runtime_bytes(root, relative)
                except OSError as error:
                    findings.append(f"{relative}: source file cannot be read ({error})")
                    continue
                if info.file_size > max(len(source) * 2, len(source) + 1_000_000):
                    findings.append(f"{info.filename}: untrusted member is too large to inspect")
                    continue
                data = archive.read(info)
                if b"\r" in data:
                    findings.append(f"{info.filename}: text must use LF line endings")
                if hashlib.sha256(data).digest() != hashlib.sha256(source).digest():
                    findings.append(f"{info.filename}: does not match source bytes")
                try:
                    text = data.decode("utf-8")
                except UnicodeDecodeError:
                    findings.append(f"{info.filename}: must be valid UTF-8")
                else:
                    findings.extend(
                        f"{info.filename}: {finding}"
                        for finding in scan_text(relative, text)
                    )
    except (OSError, zipfile.BadZipFile, RuntimeError) as error:
        findings.append(f"{artifact.name}: cannot safely read ZIP contents ({error})")
    return findings


def main(argv: list[str] | None = None) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if len(arguments) != 2:
        print("usage: verify_artifacts.py <artifact.zip> <artifact.skill>", file=sys.stderr)
        return 2
    artifacts = [Path(argument).resolve() for argument in arguments]
    zip_artifacts = [path for path in artifacts if path.suffix == ".zip"]
    skill_artifacts = [path for path in artifacts if path.suffix == ".skill"]
    if len(zip_artifacts) != 1 or len(skill_artifacts) != 1:
        print("usage: verify_artifacts.py <artifact.zip> <artifact.skill>", file=sys.stderr)
        return 2
    root = Path(__file__).resolve().parents[1]
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    zip_path, skill_path = zip_artifacts[0], skill_artifacts[0]
    expected_zip = f"{SKILL_NAME}-{version}.zip"
    expected_skill = f"{SKILL_NAME}-{version}.skill"
    findings: list[str] = []
    if zip_path.parent != skill_path.parent:
        findings.append("release pair: ZIP and .skill must be in the same directory")
    if zip_path.name != expected_zip:
        findings.append(f"{zip_path.name}: does not use the versioned release name")
    if skill_path.name != expected_skill:
        findings.append(f"{skill_path.name}: does not use the versioned release name")
    if not zip_path.is_file():
        findings.append(f"{zip_path}: artifact is missing")
    if not skill_path.is_file():
        findings.append(f"{skill_path}: artifact is missing")
    if not findings:
        findings = verify(root, zip_path)
    if findings:
        for finding in findings:
            print(f"[FAIL] {finding}")
        return 1
    print("[OK] artifact verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
