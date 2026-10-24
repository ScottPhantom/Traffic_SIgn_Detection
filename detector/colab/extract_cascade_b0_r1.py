"""Extract an externally hash-pinned B0 archive without tarfile extraction shortcuts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import tarfile
from pathlib import Path, PurePosixPath


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_directory(path: Path) -> Path:
    path = path.absolute()
    for item in reversed([path, *path.parents]):
        if item.is_symlink() or (item.exists() and not item.is_dir()):
            raise RuntimeError(f"unsafe extraction directory: {item}")
    return path


def extract(archive: Path, destination: Path, archive_sha256: str, manifest_sha256: str) -> Path:
    """Fail closed and never overwrite an existing destination; partial output remains for audit."""
    safe_directory(archive.parent)
    info = archive.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or sha256(archive) != archive_sha256:
        raise RuntimeError("untrusted archive")
    destination = safe_directory(destination)
    if destination.exists():
        raise RuntimeError("extraction destination already exists")
    with tarfile.open(archive, "r:gz") as source:
        members = source.getmembers()
        names = set()
        total = 0
        for member in members:
            path = PurePosixPath(member.name)
            if (
                not member.isfile()
                or path.is_absolute()
                or path.as_posix() != member.name
                or any(part in {"..", "test"} for part in path.parts)
                or not path.parts
                or member.name in names
                or member.size < 0
            ):
                raise RuntimeError(f"unsafe archive member: {member.name}")
            names.add(member.name)
            total += member.size
        if total > 5 * 1024**3 or len(names) > 20000:
            raise RuntimeError("archive exceeds B0 size limits")
        manifests = [item for item in members if item.name == "manifest.json"]
        if len(manifests) != 1:
            raise RuntimeError("missing archive manifest")
        manifest_bytes = source.extractfile(manifests[0]).read()
        if hashlib.sha256(manifest_bytes).hexdigest() != manifest_sha256:
            raise RuntimeError("untrusted archive manifest")
        manifest = json.loads(manifest_bytes)
        if names != set(manifest["members"]) | {"manifest.json"}:
            raise RuntimeError("archive roster differs")
        destination.mkdir(parents=True, exist_ok=False)
        for member in members:
            output = destination / member.name
            safe_directory(output.parent).mkdir(parents=True, exist_ok=True)
            digest = hashlib.sha256()
            with source.extractfile(member) as reader, output.open("xb") as writer:
                for chunk in iter(lambda: reader.read(1024 * 1024), b""):
                    digest.update(chunk)
                    writer.write(chunk)
                writer.flush()
                os.fsync(writer.fileno())
            if member.name != "manifest.json":
                expected = manifest["members"][member.name]
                if (
                    output.stat().st_size != expected["bytes"]
                    or digest.hexdigest() != expected["sha256"]
                ):
                    raise RuntimeError(f"extracted payload mismatch: {member.name}")
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--archive-sha256", required=True)
    parser.add_argument("--manifest-sha256", required=True)
    args = parser.parse_args()
    print(extract(args.archive, args.destination, args.archive_sha256, args.manifest_sha256))
