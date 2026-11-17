"""Check staged storage policy against real, isolated Git indexes."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "sync_git_lfs_by_size.py"
SPEC = importlib.util.spec_from_file_location("storage_policy_under_test", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
POLICY = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = POLICY
SPEC.loader.exec_module(POLICY)


class StoragePolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="dachuang-storage-policy-")
        self.addCleanup(self.temporary.cleanup)
        self.repo = Path(self.temporary.name)
        isolated = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
        isolated.update(
            GIT_CONFIG_GLOBAL=os.devnull,
            GIT_CONFIG_SYSTEM=os.devnull,
            GIT_CONFIG_NOSYSTEM="1",
            GIT_TERMINAL_PROMPT="0",
            GIT_OPTIONAL_LOCKS="0",
        )
        self.environment = patch.dict(os.environ, isolated, clear=True)
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.git("init", "--quiet")

    def git(self, *args: str, input_bytes: bytes | None = None) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            ["git", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false", *args],
            cwd=self.repo,
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )

    def stage(self, relative: str, content: bytes) -> Path:
        path = self.repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        self.git("add", "--", relative)
        return path

    def check_without_changing_index(self, **kwargs: int) -> list[str]:
        before = (self.repo / ".git/index").read_bytes()
        errors = POLICY.check_index(self.repo, **kwargs)
        after = (self.repo / ".git/index").read_bytes()
        self.assertEqual(before, after, "A storage check must not rewrite the user's index")
        self.assertIsInstance(errors, list)
        self.assertTrue(all(isinstance(error, str) for error in errors))
        return errors

    def test_small_plain_files_with_chinese_and_spaces_pass(self) -> None:
        self.stage("面板 数据/样本统计.csv", "年份,样本数\n2024,10\n".encode())
        self.stage("notes.txt", b"ordinary Git content\n")
        self.assertEqual([], self.check_without_changing_index())

    def test_small_lfs_pointer_is_rejected(self) -> None:
        relative = "面板 数据/指针.csv"
        pointer = (
            b"version https://git-lfs.github.com/spec/v1\n"
            b"oid sha256:" + b"1" * 64 + b"\nsize 3\n"
        )
        self.stage(relative, pointer)
        errors = self.check_without_changing_index()
        self.assertTrue(any(relative in error and "LFS" in error for error in errors), errors)

    def test_exact_size_limit_is_rejected_and_one_byte_less_passes(self) -> None:
        relative = "数据/边界 file.bin"
        self.stage(relative, b"x" * 31)
        self.assertEqual([], self.check_without_changing_index(threshold_bytes=32))
        self.stage(relative, b"x" * 32)
        errors = self.check_without_changing_index(threshold_bytes=32)
        self.assertTrue(any(relative in error for error in errors), errors)

    def test_unstaged_or_untracked_large_files_do_not_change_staged_policy(self) -> None:
        path = self.stage("data.csv", b"staged\n")
        path.write_bytes(b"not staged\n" * 20)
        (self.repo / "untracked-large.bin").write_bytes(b"x" * 200)
        self.assertEqual([], self.check_without_changing_index(threshold_bytes=32))
        self.assertEqual(b"staged\n", self.git("show", ":data.csv").stdout)

    def test_api_cannot_raise_the_production_size_limit(self) -> None:
        self.stage("plain.txt", b"data\n")
        before = (self.repo / ".git/index").read_bytes()
        with self.assertRaises(ValueError):
            POLICY.check_index(self.repo, threshold_bytes=100_000_001)
        self.assertEqual(before, (self.repo / ".git/index").read_bytes())

    def test_unmerged_index_stages_are_rejected_without_modification(self) -> None:
        relative = "数据/冲突 file.csv"
        entries = []
        for stage, data in enumerate((b"base\n", b"ours\n", b"theirs\n"), 1):
            oid = self.git("hash-object", "-w", "--stdin", input_bytes=data).stdout.strip()
            entries.append(b"100644 " + oid + f" {stage}\t".encode() + relative.encode() + b"\n")
        self.git("update-index", "--index-info", input_bytes=b"".join(entries))
        errors = self.check_without_changing_index()
        self.assertTrue(any(relative in error for error in errors), errors)
        self.assertEqual(3, len(self.git("ls-files", "-u", "-z").stdout.rstrip(b"\0").split(b"\0")))

    def test_cli_check_returns_success_for_plain_index(self) -> None:
        self.stage("plain.txt", b"data\n")
        before = (self.repo / ".git/index").read_bytes()
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "--check"],
            cwd=self.repo,
            capture_output=True,
        )
        self.assertEqual(0, result.returncode, result.stderr.decode(errors="replace"))
        self.assertEqual(before, (self.repo / ".git/index").read_bytes())

    def test_cli_check_returns_failure_for_lfs_pointer(self) -> None:
        self.stage(
            "data.csv",
            b"version https://git-lfs.github.com/spec/v1\noid sha256:"
            + b"2" * 64
            + b"\nsize 10\n",
        )
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "--check"],
            cwd=self.repo,
            capture_output=True,
        )
        self.assertEqual(1, result.returncode, (result.stdout + result.stderr).decode(errors="replace"))
        self.assertIn(b"LFS", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
