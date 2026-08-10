"""Contracts for deterministic release artifacts."""

from __future__ import annotations

import subprocess
import sys
import hashlib
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


class PackagingTests(unittest.TestCase):
    def test_package_cli_exists_and_builds_default_output(self) -> None:
        result = subprocess.run(
            [sys.executable, "-X", "utf8", "scripts/package.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_package_cli_accepts_an_explicit_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_dir = Path(directory) / "release"
            result = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    "scripts/package.py",
                    "--output-dir",
                    str(output_dir),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(
                (output_dir / "interview-solo-business-startup-positioning-0.1.0.zip").is_file()
            )

    def copied_repository(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        temporary = tempfile.TemporaryDirectory()
        copied_root = Path(temporary.name) / "repository"
        shutil.copytree(
            ROOT,
            copied_root,
            ignore=shutil.ignore_patterns(
                ".git", "dist", "work", "__pycache__", "*.pyc"
            ),
        )
        return temporary, copied_root

    def build_valid_artifacts(self) -> tuple[
        tempfile.TemporaryDirectory[str], Path, Path, Path, Path
    ]:
        from scripts.package import build

        temporary, copied_root = self.copied_repository()
        output_dir = Path(temporary.name) / "artifacts"
        zip_path, skill_path, sums_path = build(copied_root, output_dir)
        return temporary, copied_root, zip_path, skill_path, sums_path

    def write_archive(
        self,
        path: Path,
        source_root: Path,
        changed: dict[str, bytes] | None = None,
        members: list[str] | None = None,
    ) -> None:
        from scripts.verify_artifacts import expected_members
        from scripts.validate import normalized_runtime_bytes

        changed = changed or {}
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
            for member in members or expected_members():
                relative = member.split("/", 1)[1]
                archive.writestr(
                    member, changed.get(relative, normalized_runtime_bytes(source_root, relative))
                )

    def replace_release_pair(
        self,
        source_root: Path,
        zip_path: Path,
        skill_path: Path,
        sums_path: Path,
        changed: dict[str, bytes] | None = None,
        members: list[str] | None = None,
    ) -> None:
        self.write_archive(zip_path, source_root, changed, members)
        shutil.copyfile(zip_path, skill_path)
        digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
        sums_path.write_text(
            f"{digest}  {zip_path.name}\n{digest}  {skill_path.name}\n",
            encoding="ascii",
            newline="\n",
        )

    def rewrite_with_metadata(
        self,
        source_root: Path,
        zip_path: Path,
        skill_path: Path,
        sums_path: Path,
        *,
        archive_comment: bytes = b"",
        member_comment: bytes = b"",
        member_extra: bytes = b"",
    ) -> None:
        from scripts.package import FIXED_ZIP_TIMESTAMP
        from scripts.verify_artifacts import expected_members
        from scripts.validate import normalized_runtime_bytes

        rewritten = zip_path.with_suffix(".rewritten")
        with zipfile.ZipFile(
            rewritten, "w", zipfile.ZIP_DEFLATED, compresslevel=9
        ) as archive:
            archive.comment = archive_comment
            for index, member in enumerate(expected_members()):
                relative = member.split("/", 1)[1]
                info = zipfile.ZipInfo(member, FIXED_ZIP_TIMESTAMP)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                if index == 0:
                    info.comment = member_comment
                    info.extra = member_extra
                archive.writestr(info, normalized_runtime_bytes(source_root, relative))
        rewritten.replace(zip_path)
        shutil.copyfile(zip_path, skill_path)
        digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
        sums_path.write_text(
            f"{digest}  {zip_path.name}\n{digest}  {skill_path.name}\n",
            encoding="ascii",
            newline="\n",
        )

    def test_builds_are_byte_identical_and_whitelisted(self) -> None:
        from scripts.package import FIXED_ZIP_TIMESTAMP, build
        from scripts.verify_artifacts import expected_members
        from scripts.validate import normalized_runtime_bytes

        temporary, copied_root = self.copied_repository()
        with temporary:
            (copied_root / "SKILL.md").write_text(
                (copied_root / "SKILL.md").read_text(encoding="utf-8"),
                encoding="utf-8",
                newline="\r\n",
            )
            one = Path(temporary.name) / "one"
            two = Path(temporary.name) / "two"
            first = build(copied_root, one)
            second = build(copied_root, two)
            self.assertEqual(
                [path.read_bytes() for path in first],
                [path.read_bytes() for path in second],
            )
            zip_path, skill_path, sums_path = first
            self.assertEqual(zip_path.name, "interview-solo-business-startup-positioning-0.1.0.zip")
            self.assertEqual(skill_path.name, "interview-solo-business-startup-positioning-0.1.0.skill")
            self.assertEqual(zip_path.read_bytes(), skill_path.read_bytes())
            digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
            self.assertEqual(
                sums_path.read_bytes(),
                (
                    f"{digest}  {zip_path.name}\n{digest}  {skill_path.name}\n"
                ).encode("ascii"),
            )
            with zipfile.ZipFile(zip_path) as archive:
                self.assertEqual(archive.namelist(), expected_members())
                for info in archive.infolist():
                    self.assertEqual(info.date_time, FIXED_ZIP_TIMESTAMP)
                    self.assertEqual(info.create_system, 3)
                    self.assertEqual(info.external_attr >> 16, 0o100644)
                    self.assertEqual(info.compress_type, zipfile.ZIP_DEFLATED)
                    relative = info.filename.split("/", 1)[1]
                    data = archive.read(info)
                    self.assertNotIn(b"\r", data)
                    self.assertEqual(data, normalized_runtime_bytes(copied_root, relative))

    def test_build_rejects_invalid_source_before_writing_output(self) -> None:
        from scripts.package import build

        temporary, copied_root = self.copied_repository()
        with temporary:
            (copied_root / "VERSION").write_text("not-a-version\n", encoding="utf-8")
            output_dir = Path(temporary.name) / "should-not-exist"
            with self.assertRaisesRegex(ValueError, "repository validation failed"):
                build(copied_root, output_dir)
            self.assertFalse(output_dir.exists())

    def test_verifies_valid_zip_and_skill_artifacts(self) -> None:
        from scripts.verify_artifacts import verify

        temporary, copied_root, zip_path, skill_path, _ = self.build_valid_artifacts()
        with temporary:
            self.assertEqual(verify(copied_root, zip_path), [])
            self.assertEqual(verify(copied_root, skill_path), [])

    def test_verifier_rejects_oversized_artifact_before_reading_content(self) -> None:
        from scripts.verify_artifacts import verify

        temporary, copied_root, zip_path, skill_path, sums_path = (
            self.build_valid_artifacts()
        )
        with temporary:
            oversized = zip_path.read_bytes() + (b"oversized" * 200_000)
            zip_path.write_bytes(oversized)
            skill_path.write_bytes(oversized)
            digest = hashlib.sha256(oversized).hexdigest()
            sums_path.write_text(
                f"{digest}  {zip_path.name}\n{digest}  {skill_path.name}\n",
                encoding="ascii",
                newline="\n",
            )
            original_open = Path.open

            def reject_untrusted_open(path: Path, *args: object, **kwargs: object):
                if path in {zip_path, skill_path}:
                    raise AssertionError("oversized artifact content was opened")
                return original_open(path, *args, **kwargs)

            try:
                with mock.patch.object(Path, "open", reject_untrusted_open):
                    findings = "\n".join(verify(copied_root, zip_path))
            except AssertionError as error:
                self.fail(str(error))
            self.assertIn("canonical size", findings)

    def test_verifier_rejects_oversized_skill_before_open_or_hash(self) -> None:
        from scripts.verify_artifacts import verify

        temporary, copied_root, zip_path, skill_path, _ = self.build_valid_artifacts()
        with temporary:
            skill_path.write_bytes(
                skill_path.read_bytes() + (b"oversized-skill" * 200_000)
            )
            original_open = Path.open

            def reject_oversized_skill_open(
                path: Path, *args: object, **kwargs: object
            ):
                if path == skill_path:
                    raise AssertionError("oversized .skill was opened or hashed")
                return original_open(path, *args, **kwargs)

            try:
                with mock.patch.object(Path, "open", reject_oversized_skill_open):
                    findings = "\n".join(verify(copied_root, zip_path))
            except AssertionError as error:
                self.fail(str(error))
            self.assertIn(skill_path.name, findings)
            self.assertIn("canonical size", findings)

    def test_verifier_rejects_oversized_checksum_manifest_before_open(self) -> None:
        from scripts.verify_artifacts import verify

        temporary, copied_root, zip_path, _, sums_path = self.build_valid_artifacts()
        with temporary:
            sums_path.write_bytes(
                sums_path.read_bytes() + (b"oversized-manifest" * 200_000)
            )
            original_open = Path.open

            def reject_oversized_manifest_open(
                path: Path, *args: object, **kwargs: object
            ):
                if path == sums_path:
                    raise AssertionError("oversized SHA256SUMS was opened")
                return original_open(path, *args, **kwargs)

            try:
                with mock.patch.object(Path, "open", reject_oversized_manifest_open):
                    findings = "\n".join(verify(copied_root, zip_path))
            except AssertionError as error:
                self.fail(str(error))
            self.assertIn("SHA256SUMS: canonical size", findings)

    def test_verifier_uses_chunked_reads_for_canonical_compare_and_hashing(self) -> None:
        from scripts.verify_artifacts import _READ_CHUNK_SIZE, verify

        temporary, copied_root, zip_path, skill_path, _ = self.build_valid_artifacts()
        with temporary:
            original_open = Path.open
            read_sizes: list[int] = []

            class BoundedReader:
                def __init__(self, stream: object) -> None:
                    self.stream = stream

                def __enter__(self) -> "BoundedReader":
                    return self

                def __exit__(self, *args: object) -> object:
                    return self.stream.__exit__(*args)  # type: ignore[attr-defined]

                def read(self, size: int = -1) -> bytes:
                    if size < 0 or size > _READ_CHUNK_SIZE:
                        raise AssertionError(f"unbounded artifact read requested: {size}")
                    read_sizes.append(size)
                    return self.stream.read(size)  # type: ignore[attr-defined,no-any-return]

            def bound_artifact_reads(path: Path, *args: object, **kwargs: object):
                if path in {zip_path, skill_path}:
                    return BoundedReader(original_open(path, *args, **kwargs))
                return original_open(path, *args, **kwargs)

            try:
                with mock.patch.object(Path, "open", bound_artifact_reads):
                    findings = verify(copied_root, zip_path)
            except AssertionError as error:
                self.fail(str(error))
            self.assertEqual(findings, [])
            self.assertTrue(read_sizes)
            self.assertTrue(all(size == _READ_CHUNK_SIZE for size in read_sizes))

    def test_verifier_compares_exact_size_checksum_manifest_in_chunks(self) -> None:
        from scripts.verify_artifacts import _READ_CHUNK_SIZE, verify

        temporary, copied_root, zip_path, _, sums_path = self.build_valid_artifacts()
        with temporary:
            original_open = Path.open
            read_sizes: list[int] = []

            class BoundedReader:
                def __init__(self, stream: object) -> None:
                    self.stream = stream

                def __enter__(self) -> "BoundedReader":
                    return self

                def __exit__(self, *args: object) -> object:
                    return self.stream.__exit__(*args)  # type: ignore[attr-defined]

                def read(self, size: int = -1) -> bytes:
                    if size < 0 or size > _READ_CHUNK_SIZE:
                        raise AssertionError(f"unbounded manifest read requested: {size}")
                    read_sizes.append(size)
                    return self.stream.read(size)  # type: ignore[attr-defined,no-any-return]

            def bound_manifest_reads(path: Path, *args: object, **kwargs: object):
                if path == sums_path:
                    return BoundedReader(original_open(path, *args, **kwargs))
                return original_open(path, *args, **kwargs)

            try:
                with mock.patch.object(Path, "open", bound_manifest_reads):
                    findings = verify(copied_root, zip_path)
            except AssertionError as error:
                self.fail(str(error))
            self.assertEqual(findings, [])
            self.assertTrue(read_sizes)
            self.assertTrue(all(size == _READ_CHUNK_SIZE for size in read_sizes))

    def test_verifier_rejects_unsafe_member_paths_without_extracting(self) -> None:
        from scripts.verify_artifacts import _unsafe, verify

        unsafe_names = (
            "",
            "../outside.txt",
            "/absolute.txt",
            "C:/absolute.txt",
            "interview-solo-business-startup-positioning\\backslash.txt",
            "interview-solo-business-startup-positioning/./dot.txt",
            "interview-solo-business-startup-positioning/../parent.txt",
            "interview-solo-business-startup-positioning//empty.txt",
        )
        for unsafe_name in unsafe_names:
            with self.subTest(predicate=unsafe_name):
                self.assertTrue(_unsafe(unsafe_name))

        temporary, copied_root, zip_path, _, _ = self.build_valid_artifacts()
        with temporary:
            # Python 3.10's zipfile rejects an empty member name before it can
            # be written. The predicate contract above covers that case;
            # archive-level tests use the dangerous names every supported
            # stdlib can construct.
            for index, unsafe_name in enumerate(unsafe_names[1:]):
                with self.subTest(member=unsafe_name):
                    hostile = zip_path.with_name(f"hostile-{index}.zip")
                    self.write_archive(hostile, copied_root)
                    with zipfile.ZipFile(hostile, "a") as archive:
                        archive.writestr(unsafe_name, b"not extracted")
                    sentinel = hostile.parent / "outside.txt"
                    self.assertFalse(sentinel.exists())
                    self.assertTrue(verify(copied_root, hostile))
                    self.assertFalse(sentinel.exists())

    def test_verifier_rejects_extra_member_invalid_utf8_and_source_mismatch(self) -> None:
        from scripts.verify_artifacts import expected_members, verify

        temporary, copied_root, zip_path, _, _ = self.build_valid_artifacts()
        with temporary:
            extra = zip_path.with_name("extra.zip")
            self.write_archive(extra, copied_root)
            with zipfile.ZipFile(extra, "a") as archive:
                archive.writestr("interview-solo-business-startup-positioning/extra.txt", b"extra")
            self.assertTrue(verify(copied_root, extra))

            invalid_utf8 = zip_path.with_name("invalid-utf8.zip")
            self.write_archive(invalid_utf8, copied_root, {"SKILL.md": b"\xff"})
            self.assertIn("valid UTF-8", "\n".join(verify(copied_root, invalid_utf8)))

            mismatch = zip_path.with_name("mismatch.zip")
            self.write_archive(mismatch, copied_root, {"LICENSE": b"changed\n"})
            self.assertIn("does not match source", "\n".join(verify(copied_root, mismatch)))
            self.assertEqual(expected_members(), sorted(expected_members()))

    def test_verifier_rejects_noncanonical_zip_metadata_after_rechecksumming(self) -> None:
        from scripts.package import build
        from scripts.verify_artifacts import verify

        temporary, copied_root, zip_path, skill_path, sums_path = (
            self.build_valid_artifacts()
        )
        with temporary:
            cases = (
                ("archive comment", {"archive_comment": b"hostile archive comment"}),
                ("member comment", {"member_comment": b"hostile member comment"}),
                (
                    "member extra field",
                    {"member_extra": b"\xfe\xca\x04\x00evil"},
                ),
            )
            for expected, metadata in cases:
                with self.subTest(metadata=expected):
                    build(copied_root, zip_path.parent)
                    self.rewrite_with_metadata(
                        copied_root,
                        zip_path,
                        skill_path,
                        sums_path,
                        **metadata,
                    )
                    findings = "\n".join(verify(copied_root, zip_path))
                    self.assertIn(expected, findings)
                    self.assertIn("canonical bytes", findings)

    def test_verifier_rejects_checksum_and_peer_identity_mismatches(self) -> None:
        from scripts.verify_artifacts import verify

        temporary, copied_root, zip_path, skill_path, sums_path = self.build_valid_artifacts()
        with temporary:
            sums_path.write_text("0" * 64 + f"  {zip_path.name}\n", encoding="ascii", newline="\n")
            self.assertIn("SHA256SUMS", "\n".join(verify(copied_root, zip_path)))

            temporary_two, copied_root_two, zip_path_two, skill_path_two, _ = (
                self.build_valid_artifacts()
            )
            with temporary_two:
                skill_path_two.write_bytes(skill_path_two.read_bytes() + b"changed")
                self.assertIn(
                    "byte-identical", "\n".join(verify(copied_root_two, zip_path_two))
                )

    def test_verifier_cli_requires_artifacts(self) -> None:
        result = subprocess.run(
            [sys.executable, "-X", "utf8", "scripts/verify_artifacts.py"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)

    def test_verifier_cli_accepts_the_zip_and_skill_arguments(self) -> None:
        temporary, _, zip_path, skill_path, _ = self.build_valid_artifacts()
        with temporary:
            result = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    "scripts/verify_artifacts.py",
                    str(zip_path),
                    str(skill_path),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("[OK] artifact verification passed", result.stdout)

    def test_verifier_cli_rejects_an_arbitrary_or_missing_skill_argument(self) -> None:
        temporary, _, zip_path, _, _ = self.build_valid_artifacts()
        with temporary:
            arbitrary_skill = zip_path.with_name("arbitrary.skill")
            arbitrary_skill.write_bytes(b"not the release artifact")
            for skill_path in (arbitrary_skill, zip_path.with_name("missing.skill")):
                with self.subTest(skill=skill_path.name):
                    result = subprocess.run(
                        [
                            sys.executable,
                            "-X",
                            "utf8",
                            "scripts/verify_artifacts.py",
                            str(zip_path),
                            str(skill_path),
                        ],
                        cwd=ROOT,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    self.assertIn("[FAIL]", result.stdout)

    def test_verifier_rejects_private_runtime_content_and_missing_member(self) -> None:
        from scripts.verify_artifacts import expected_members, verify

        temporary, copied_root, zip_path, skill_path, sums_path = self.build_valid_artifacts()
        with temporary:
            self.replace_release_pair(
                copied_root,
                zip_path,
                skill_path,
                sums_path,
                {"SKILL.md": b"api_key = \"not-a-real-secret\"\n"},
            )
            privacy_findings = "\n".join(verify(copied_root, zip_path))
            self.assertIn("embedded secret", privacy_findings)

            self.replace_release_pair(
                copied_root,
                zip_path,
                skill_path,
                sums_path,
                members=expected_members()[:-1],
            )
            member_findings = "\n".join(verify(copied_root, zip_path))
            self.assertIn("ordered runtime whitelist", member_findings)

    def test_verifier_cli_exits_one_when_artifact_has_findings(self) -> None:
        temporary, copied_root, zip_path, skill_path, sums_path = self.build_valid_artifacts()
        with temporary:
            self.replace_release_pair(
                copied_root,
                zip_path,
                skill_path,
                sums_path,
                {"LICENSE": b"changed\n"},
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "-X",
                    "utf8",
                    "scripts/verify_artifacts.py",
                    str(zip_path),
                    str(skill_path),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("does not match source", result.stdout)


if __name__ == "__main__":
    unittest.main()
