"""Build deterministic public release artifacts for the Skill."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import zipfile
from pathlib import Path

try:
    from scripts.validate import (
        RUNTIME_FILES,
        SKILL_NAME,
        normalized_runtime_bytes,
        validate_repository,
    )
except ModuleNotFoundError:
    from validate import (  # type: ignore[no-redef]
        RUNTIME_FILES,
        SKILL_NAME,
        normalized_runtime_bytes,
        validate_repository,
    )


FIXED_ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)


def build(root: Path, output_dir: Path) -> tuple[Path, Path, Path]:
    """Build a byte-stable ZIP, matching .skill file, and checksum manifest."""
    findings = validate_repository(root)
    if findings:
        raise ValueError("repository validation failed:\n" + "\n".join(findings))

    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    output_dir.mkdir(parents=True, exist_ok=True)
    zip_path = output_dir / f"{SKILL_NAME}-{version}.zip"
    skill_path = output_dir / f"{SKILL_NAME}-{version}.skill"
    sums_path = output_dir / "SHA256SUMS"

    with zipfile.ZipFile(
        zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for relative in sorted(RUNTIME_FILES):
            info = zipfile.ZipInfo(
                f"{SKILL_NAME}/{Path(relative).as_posix()}", FIXED_ZIP_TIMESTAMP
            )
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, normalized_runtime_bytes(root, relative))

    shutil.copyfile(zip_path, skill_path)
    digest = hashlib.sha256(zip_path.read_bytes()).hexdigest()
    sums_path.write_text(
        f"{digest}  {zip_path.name}\n{digest}  {skill_path.name}\n",
        encoding="utf-8",
        newline="\n",
    )
    return zip_path, skill_path, sums_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "dist",
        help="directory for the ZIP, .skill, and SHA256SUMS outputs",
    )
    args = parser.parse_args(argv)
    zip_path, skill_path, sums_path = build(
        Path(__file__).resolve().parents[1], args.output_dir
    )
    for path in (zip_path, skill_path, sums_path):
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
