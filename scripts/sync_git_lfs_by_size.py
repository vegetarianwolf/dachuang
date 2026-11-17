#!/usr/bin/env python3
"""Validate the staged snapshot against this repository's plain-Git policy.

The historical filename is retained for compatibility. This command only reads
Git's index: it does not generate attributes, stage files, or migrate history.
Every ordinary Git blob must be strictly smaller than 100,000,000 bytes, and
LFS placeholder pointers are rejected. Large source datasets belong in the
lossless parts managed by scripts/data_parts.py.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

MAX_FILE_BYTES = 100_000_000
POINTER_SCAN_LIMIT = 1024
POINTER_PREFIX = b"version https://git-lfs.github.com/spec/v1\n"
OID = re.compile(r"[0-9a-f]{40,64}\Z")


class GitError(RuntimeError):
    """A read-only Git query failed."""


def _git_command(repo_root: Path, *args: str) -> list[str]:
    return ["git", "-c", "core.hooksPath=/dev/null", "-c",
            "core.fsmonitor=false", "-C", str(repo_root), *args]


def _git_env() -> dict[str, str]:
    # Preserve GIT_INDEX_FILE: commit hooks may receive a temporary commit index.
    return dict(os.environ, GIT_OPTIONAL_LOCKS="0")


def run_git(repo_root: Path, *args: str,
            input_bytes: bytes | None = None) -> bytes:
    result = subprocess.run(_git_command(repo_root, *args), input=input_bytes,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env=_git_env())
    if result.returncode:
        detail = result.stderr.decode("utf-8", "replace").strip()
        raise GitError(detail or f"Git 查询失败：{args[0]}")
    return result.stdout


def _read_small_blobs(repo_root: Path, sizes: dict[str, int]) -> dict[str, bytes]:
    """Read only blobs that were already measured at no more than 1 KiB."""
    if not sizes:
        return {}
    proc = subprocess.Popen(_git_command(repo_root, "cat-file", "--batch"),
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, env=_git_env())
    blobs: dict[str, bytes] = {}
    try:
        assert proc.stdin is not None and proc.stdout is not None
        for oid, expected_size in sizes.items():
            proc.stdin.write((oid + "\n").encode("ascii"))
            proc.stdin.flush()
            fields = proc.stdout.readline(256).split()
            if len(fields) != 3 or fields[0].decode("ascii") != oid or fields[1] != b"blob":
                raise GitError("git cat-file 返回了无效对象信息")
            size = int(fields[2])
            if size != expected_size or size > POINTER_SCAN_LIMIT:
                raise GitError("候选指针的对象大小发生变化")
            content = proc.stdout.read(size)
            if len(content) != size or proc.stdout.read(1) != b"\n":
                raise GitError("无法完整读取候选指针")
            blobs[oid] = content
        proc.stdin.close()
        if proc.wait() != 0:
            raise GitError("git cat-file 查询失败")
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait()
        for stream in (proc.stdin, proc.stdout, proc.stderr):
            if stream is not None and not stream.closed:
                stream.close()
    return blobs


def is_lfs_pointer(content: bytes) -> bool:
    # An extension-bearing pointer still contains the standard version, oid,
    # and size fields. Do not mistake an ordinary prose mention for a pointer.
    lines = content.splitlines()
    if not lines or lines[0] != POINTER_PREFIX.rstrip(b"\n"):
        return False
    has_oid = any(re.fullmatch(rb"oid sha256:[0-9a-f]{64}", line)
                  for line in lines[1:])
    has_size = any(re.fullmatch(rb"size [0-9]+", line) for line in lines[1:])
    return has_oid and has_size


def check_index(repo_root: Path, threshold_bytes: int = MAX_FILE_BYTES) -> list[str]:
    """Return violations without changing the index or working files.

    A lower threshold is useful for focused tests. Increasing the production
    limit through this API is rejected as well as through the CLI.
    """
    if not 0 < threshold_bytes <= MAX_FILE_BYTES:
        raise ValueError("阈值必须大于 0 且不能超过 100,000,000 字节")
    records = run_git(repo_root, "ls-files", "--stage", "--full-name", "-z")
    paths_by_oid: dict[str, list[str]] = defaultdict(list)
    errors: list[str] = []
    conflicts: set[str] = set()
    for record in records.split(b"\0"):
        if not record:
            continue
        try:
            metadata, raw_path = record.split(b"\t", 1)
            mode, oid, stage = metadata.decode("ascii").split()
            path = os.fsdecode(raw_path)
            if not OID.fullmatch(oid):
                raise ValueError("无效对象编号")
        except (ValueError, UnicodeError) as error:
            raise GitError("无法解析 Git 索引条目") from error
        if stage != "0":
            conflicts.add(path)
        elif mode != "160000":  # Gitlinks are commits rather than file blobs.
            paths_by_oid[oid].append(path)
    errors.extend(f"未解决的合并冲突：{path}" for path in sorted(conflicts))
    if not paths_by_oid:
        return errors
    response = run_git(repo_root, "cat-file",
                       "--batch-check=%(objectname) %(objecttype) %(objectsize)",
                       input_bytes="".join(oid + "\n" for oid in paths_by_oid).encode("ascii"))
    sizes: dict[str, int] = {}
    for line in response.splitlines():
        fields = line.split()
        if len(fields) != 3 or fields[1] != b"blob":
            raise GitError("索引中的文件对象不存在或不是 blob")
        oid = fields[0].decode("ascii")
        if oid not in paths_by_oid:
            raise GitError("git cat-file 返回了未知对象")
        sizes[oid] = int(fields[2])
    if sizes.keys() != paths_by_oid.keys():
        raise GitError("部分索引对象未返回大小信息")
    for oid, paths in paths_by_oid.items():
        if sizes[oid] >= threshold_bytes:
            errors.extend(f"文件必须小于 {threshold_bytes:,} 字节：{path}（{sizes[oid]:,} 字节）"
                          for path in paths)
    candidates = {oid: size for oid, size in sizes.items() if size <= POINTER_SCAN_LIMIT}
    for oid, content in _read_small_blobs(repo_root, candidates).items():
        if is_lfs_pointer(content):
            errors.extend(f"仍为 LFS 占位指针：{path}" for path in paths_by_oid[oid])
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="检查索引：普通 Git 文件须小于 100 MB，且不得含 LFS 指针。")
    parser.add_argument("--check", action="store_true", help="只检查已暂存的快照，不修改任何文件。")
    parser.add_argument("--write", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--restage-staged", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--threshold-mb", type=int, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.write or args.restage_staged or args.threshold_mb is not None:
        parser.error("原有自动生成 LFS 规则的方式已停用；请使用 --check，大文件请用 scripts/data_parts.py 分片。")
    try:
        root = Path(os.fsdecode(run_git(Path.cwd(), "rev-parse", "--show-toplevel").rstrip(b"\n")))
        errors = check_index(root)
    except (GitError, OSError, ValueError) as error:
        print(f"存储检查无法完成：{error}", file=sys.stderr)
        return 2
    if errors:
        print("普通 Git 存储检查未通过：", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        print("小文件请重新暂存实际内容；大数据请使用 scripts/data_parts.py 分片后暂存分片。",
              file=sys.stderr)
        return 1
    print("普通 Git 存储检查通过：索引中无 LFS 指针，所有文件均小于 100 MB。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
