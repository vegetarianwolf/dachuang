#!/usr/bin/env python3
"""Store large files as bounded, lossless binary parts and restore their paths.

Run ``python3 scripts/data_parts.py restore`` after cloning the repository.
CSV encodings, headers, line endings and quoted multiline fields are preserved
byte for byte; individual binary parts are not standalone CSV documents.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile


DEFAULT_CHUNK_SIZE = 95_000_000
MAX_FILE_SIZE = 100_000_000
MANIFEST = "data_parts/manifest.json"
BUFFER_SIZE = 1024 * 1024
SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class DataPartsError(ValueError):
    """An input, checksum or user-file conflict prevents a safe operation."""


def root_path(value: str | Path) -> Path:
    path = Path(value).absolute()
    if path.is_symlink():
        raise DataPartsError(f"根目录不能是符号链接：{path}")
    path = path.resolve(strict=True)
    if not path.is_dir():
        raise DataPartsError(f"根目录不是目录：{path}")
    return path


def relative_parts(value: object, *, target: bool = False) -> list[str]:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise DataPartsError("路径必须是非空的相对 POSIX 路径")
    parts = value.split("/")
    if any(p in ("", ".", "..") or p.casefold() == ".git" for p in parts):
        raise DataPartsError(f"不安全的相对路径：{value!r}")
    if ":" in parts[0] or (target and parts[0].casefold() == "data_parts"):
        raise DataPartsError(f"不允许的数据目标路径：{value!r}")
    return parts


def safe_path(root: Path, relative: str, *, create_parents: bool = False) -> Path:
    parts = relative_parts(relative)
    current = root
    for part in parts[:-1]:
        current = current / part
        if current.is_symlink():
            raise DataPartsError(f"路径含符号链接目录：{relative}")
        if create_parents:
            current.mkdir(exist_ok=True)
        if current.exists() and not current.is_dir():
            raise DataPartsError(f"路径祖先不是目录：{relative}")
    path = current / parts[-1]
    if path.is_symlink():
        raise DataPartsError(f"路径不能是符号链接：{relative}")
    if path.exists() and not path.is_file():
        raise DataPartsError(f"路径不是普通文件：{relative}")
    return path


def open_regular(path: Path):
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    if not stat.S_ISREG(os.fstat(descriptor).st_mode):
        os.close(descriptor)
        raise DataPartsError(f"不是普通文件：{path}")
    return os.fdopen(descriptor, "rb")


def digest_file(path: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    size = 0
    with open_regular(path) as stream:
        before = os.fstat(stream.fileno())
        for block in iter(lambda: stream.read(BUFFER_SIZE), b""):
            size += len(block)
            digest.update(block)
        after = os.fstat(stream.fileno())
    if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
        after.st_size, after.st_mtime_ns, after.st_ctime_ns
    ):
        raise DataPartsError(f"校验时文件发生变化：{path}")
    return size, digest.hexdigest()


def integer(value: object, label: str, *, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        raise DataPartsError(f"{label} 必须是至少 {minimum} 的整数")
    return value


def checksum(value: object) -> str:
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise DataPartsError("SHA256 必须是 64 位小写十六进制字符串")
    return value


def chunk_size(value: object) -> int:
    value = integer(value, "分片大小", minimum=1)
    if value >= MAX_FILE_SIZE:
        raise DataPartsError("每片必须严格小于 100,000,000 字节")
    return value


def validate_manifest(data: object) -> dict:
    if not isinstance(data, dict) or type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        raise DataPartsError("不支持的 manifest 版本")
    limit = chunk_size(data.get("chunk_size_bytes"))
    entries = data.get("files")
    if not isinstance(entries, list):
        raise DataPartsError("manifest.files 必须是列表")
    targets: set[str] = set()
    all_parts: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise DataPartsError("文件记录必须是对象")
        path = entry.get("path")
        relative_parts(path, target=True)
        # Case-folding also prevents collisions on normal macOS/Windows disks.
        if path.casefold() in targets:
            raise DataPartsError(f"重复的恢复目标：{path}")
        targets.add(path.casefold())
        size = integer(entry.get("size"), "原文件大小")
        sha = checksum(entry.get("sha256"))
        parts = entry.get("parts")
        if not isinstance(parts, list) or len(parts) != (size + limit - 1) // limit:
            raise DataPartsError(f"分片数量与文件大小不符：{path}")
        total = 0
        for number, part in enumerate(parts, 1):
            if not isinstance(part, dict):
                raise DataPartsError("分片记录必须是对象")
            expected = f"data_parts/{sha}/part-{number:05d}.bin"
            if part.get("path") != expected:
                raise DataPartsError(f"分片路径或顺序错误：{path}")
            if expected in all_parts:
                raise DataPartsError(f"重复的分片路径：{expected}")
            all_parts.add(expected)
            actual_size = integer(part.get("size"), "分片大小", minimum=1)
            expected_size = min(limit, size - total)
            if actual_size != expected_size:
                raise DataPartsError(f"分片大小或边界错误：{expected}")
            checksum(part.get("sha256"))
            total += actual_size
        if total != size:
            raise DataPartsError(f"分片总大小不符：{path}")
    # A target cannot be another target's parent directory.
    for path in targets:
        components = path.split("/")
        if any("/".join(components[:n]) in targets for n in range(1, len(components))):
            raise DataPartsError(f"恢复目标存在文件/目录冲突：{path}")
    return data


def load_manifest(repo: Path) -> dict:
    path = safe_path(repo, MANIFEST)
    with open_regular(path) as stream:
        # Repository metadata must remain small, independent of the data size.
        content = stream.read(16 * 1024 * 1024 + 1)
    if len(content) > 16 * 1024 * 1024:
        raise DataPartsError("manifest 大小异常")
    return validate_manifest(json.loads(content))


def publish_part(temporary: Path, path: Path, size: int, sha: str) -> None:
    """No-overwrite publication also protects files created concurrently."""
    try:
        os.link(temporary, path, follow_symlinks=False)
    except FileExistsError:
        if path.is_symlink() or digest_file(path) != (size, sha):
            raise DataPartsError(f"已有分片内容不同，未覆盖：{path}")


def split_files(
    repo: str | Path,
    source_root: str | Path,
    records: list[dict],
    *,
    chunk_size_bytes: int = DEFAULT_CHUNK_SIZE,
) -> dict:
    repo, source_root = root_path(repo), root_path(source_root)
    limit = chunk_size(chunk_size_bytes)
    if not isinstance(records, list):
        raise DataPartsError("输入文件清单必须是列表")
    prepared = []
    seen_paths, seen_sha = set(), set()
    for record in records:
        if not isinstance(record, dict):
            raise DataPartsError("输入文件记录必须是对象")
        path = record.get("path")
        relative_parts(path, target=True)
        size = integer(record.get("size"), "原文件大小")
        sha = checksum(record.get("sha256", record.get("oid")))
        if path.casefold() in seen_paths or (size and sha in seen_sha):
            raise DataPartsError("输入存在重复目标或相同内容的重复大文件")
        seen_paths.add(path.casefold())
        seen_sha.add(sha)
        source = safe_path(source_root, path)
        if not source.is_file() or source.stat().st_size != size:
            raise DataPartsError(f"源文件缺失或大小不符：{path}")
        prepared.append((path, size, sha, source))
    result = {"schema_version": 1, "chunk_size_bytes": limit, "files": []}
    for path, size, expected_sha, source in prepared:
        digest = hashlib.sha256()
        parts = []
        total = 0
        with open_regular(source) as stream:
            before = os.fstat(stream.fileno())
            number = 1
            while total < size:
                relative = f"data_parts/{expected_sha}/part-{number:05d}.bin"
                output = safe_path(repo, relative, create_parents=True)
                descriptor, temporary_name = tempfile.mkstemp(prefix=".part-", dir=output.parent)
                temporary = Path(temporary_name)
                part_digest = hashlib.sha256()
                part_size = 0
                try:
                    with os.fdopen(descriptor, "wb") as destination:
                        remaining = min(limit, size - total)
                        while remaining:
                            block = stream.read(min(BUFFER_SIZE, remaining))
                            if not block:
                                raise DataPartsError(f"源文件在分片时缩短：{path}")
                            destination.write(block)
                            digest.update(block)
                            part_digest.update(block)
                            remaining -= len(block)
                            total += len(block)
                            part_size += len(block)
                        destination.flush()
                        os.fsync(destination.fileno())
                    part_sha = part_digest.hexdigest()
                    publish_part(temporary, output, part_size, part_sha)
                finally:
                    temporary.unlink(missing_ok=True)
                parts.append({"path": relative, "size": part_size, "sha256": part_sha})
                number += 1
            after = os.fstat(stream.fileno())
            if stream.read(1) or (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
                after.st_size, after.st_mtime_ns, after.st_ctime_ns
            ):
                raise DataPartsError(f"源文件在分片时发生变化：{path}")
        if digest.hexdigest() != expected_sha:
            raise DataPartsError(f"源文件 SHA256 不匹配，未发布清单：{path}")
        result["files"].append({"path": path, "size": size, "sha256": expected_sha, "parts": parts})
    validate_manifest(result)
    manifest = safe_path(repo, MANIFEST, create_parents=True)
    if manifest.exists():
        if load_manifest(repo) != result:
            raise DataPartsError("已有 manifest 与新清单不同，未覆盖；请先核对数据版本")
    else:
        descriptor, temporary_name = tempfile.mkstemp(prefix=".manifest-", dir=manifest.parent)
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
                json.dump(result, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(temporary, manifest, follow_symlinks=False)
            except FileExistsError:
                if load_manifest(repo) != result:
                    raise DataPartsError("manifest 被并发创建且内容不同，未覆盖")
        finally:
            temporary.unlink(missing_ok=True)
    return result


def read_parts(repo: Path, entry: dict, destination=None) -> None:
    whole_digest = hashlib.sha256()
    total = 0
    for part in entry["parts"]:
        path = safe_path(repo, part["path"])
        part_digest, part_size = hashlib.sha256(), 0
        with open_regular(path) as stream:
            for block in iter(lambda: stream.read(BUFFER_SIZE), b""):
                part_size += len(block)
                if part_size > part["size"]:
                    raise DataPartsError(f"分片大小异常：{part['path']}")
                part_digest.update(block)
                whole_digest.update(block)
                total += len(block)
                if destination is not None:
                    destination.write(block)
        if part_size != part["size"] or part_digest.hexdigest() != part["sha256"]:
            raise DataPartsError(f"分片 SHA256 或大小不符：{part['path']}")
    if total != entry["size"] or whole_digest.hexdigest() != entry["sha256"]:
        raise DataPartsError(f"合并文件 SHA256 或大小不符：{entry['path']}")


def verify_files(repo: str | Path) -> dict:
    repo = root_path(repo)
    manifest = load_manifest(repo)
    for entry in manifest["files"]:
        read_parts(repo, entry)
    return manifest


def restore_files(repo: str | Path) -> dict:
    repo = root_path(repo)
    # Validate every part first, including when full local CSVs already exist.
    manifest = verify_files(repo)
    missing = []
    for entry in manifest["files"]:
        output = safe_path(repo, entry["path"])
        if output.exists():
            if digest_file(output) != (entry["size"], entry["sha256"]):
                raise DataPartsError(f"原文件已有不同内容，已保留且未覆盖：{entry['path']}")
        else:
            missing.append(entry)
    for entry in missing:
        output = safe_path(repo, entry["path"], create_parents=True)
        descriptor, temporary_name = tempfile.mkstemp(prefix=".restore-", dir=output.parent)
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                read_parts(repo, entry, stream)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(temporary, output, follow_symlinks=False)
            except FileExistsError:
                if output.is_symlink() or digest_file(output) != (entry["size"], entry["sha256"]):
                    raise DataPartsError(f"恢复时目标被并发创建，未覆盖：{entry['path']}")
        finally:
            temporary.unlink(missing_ok=True)
    return {"files": len(manifest["files"]), "restored": len(missing), "already_present": len(manifest["files"]) - len(missing)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="将大文件无损分片，或校验后恢复到原路径。")
    commands = parser.add_subparsers(dest="command", required=True)
    default_repo = Path(__file__).resolve().parents[1]
    for command in ("split", "restore", "verify"):
        child = commands.add_parser(command)
        child.add_argument("--repo", type=Path, default=default_repo)
        if command == "split":
            child.add_argument("--source-root", type=Path, required=True)
            child.add_argument("--paths-json", type=Path, required=True)
            child.add_argument("--chunk-size-bytes", type=int, default=DEFAULT_CHUNK_SIZE)
    args = parser.parse_args(argv)
    try:
        if args.command == "split":
            with args.paths_json.open(encoding="utf-8") as stream:
                records = json.load(stream)
            result = split_files(args.repo, args.source_root, records, chunk_size_bytes=args.chunk_size_bytes)
            print(f"分片完成：{len(result['files'])} 个文件，{sum(len(x['parts']) for x in result['files'])} 个分片。")
        elif args.command == "verify":
            result = verify_files(args.repo)
            print(f"校验通过：{len(result['files'])} 个文件的分片及整体 SHA256 均一致。")
        else:
            result = restore_files(args.repo)
            print(f"恢复完成：{result['restored']} 个文件；{result['already_present']} 个原文件已完整保留。")
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.exit(1, f"错误：{error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
