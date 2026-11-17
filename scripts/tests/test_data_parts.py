"""Checksums, corruption handling and preservation of existing user files."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "data_parts.py"
SPEC = importlib.util.spec_from_file_location("data_parts", SCRIPT)
data_parts = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(data_parts)


class DataPartsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.repo = self.root / "repo"
        self.source.mkdir()
        self.repo.mkdir()
        self.name = "原始数据/中文 路径.csv"
        self.payload = '\ufeffid,text\r\n1,"中文,逗号"\r\n2,"跨行\r\n字段"\r\n'.encode("utf-8")

    def split(self, payload=None, limit=7):
        payload = self.payload if payload is None else payload
        source = self.source / self.name
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_bytes(payload)
        records = [{"path": self.name, "size": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}]
        return data_parts.split_files(self.repo, self.source, records, chunk_size_bytes=limit)

    def save_manifest(self, manifest):
        (self.repo / data_parts.MANIFEST).write_text(json.dumps(manifest), encoding="utf-8")

    def test_round_trip_preserves_every_byte_and_is_idempotent(self):
        manifest = self.split()
        self.assertTrue(all(part["size"] <= 7 for part in manifest["files"][0]["parts"]))
        self.assertEqual(data_parts.verify_files(self.repo), manifest)
        self.assertEqual(data_parts.restore_files(self.repo)["restored"], 1)
        self.assertEqual((self.repo / self.name).read_bytes(), self.payload)
        self.assertEqual(data_parts.restore_files(self.repo)["already_present"], 1)
        self.assertEqual(self.split(), manifest)

    def test_empty_and_exact_chunk_boundaries(self):
        for length in (0, 7, 8, 14, 15):
            with self.subTest(length=length):
                destination = self.repo / str(length)
                destination.mkdir()
                source = self.source / self.name
                source.parent.mkdir(parents=True, exist_ok=True)
                content = b"x" * length
                source.write_bytes(content)
                record = {"path": self.name, "size": length, "oid": hashlib.sha256(content).hexdigest()}
                manifest = data_parts.split_files(destination, self.source, [record], chunk_size_bytes=7)
                self.assertEqual(len(manifest["files"][0]["parts"]), (length + 6) // 7)
                data_parts.restore_files(destination)
                self.assertEqual((destination / self.name).read_bytes(), content)

    def test_changed_full_file_is_never_overwritten(self):
        self.split()
        output = self.repo / self.name
        output.parent.mkdir(parents=True)
        output.write_bytes(b"user's edited data")
        with self.assertRaises(data_parts.DataPartsError):
            data_parts.restore_files(self.repo)
        self.assertEqual(output.read_bytes(), b"user's edited data")

    def test_corrupt_part_is_rejected_even_with_valid_full_file(self):
        manifest = self.split()
        data_parts.restore_files(self.repo)
        part = self.repo / manifest["files"][0]["parts"][0]["path"]
        part.write_bytes(b"!" * part.stat().st_size)
        with self.assertRaises(data_parts.DataPartsError):
            data_parts.restore_files(self.repo)
        self.assertEqual((self.repo / self.name).read_bytes(), self.payload)

    def test_missing_part_does_not_create_any_output(self):
        manifest = self.split()
        (self.repo / manifest["files"][0]["parts"][-1]["path"]).unlink()
        with self.assertRaises(FileNotFoundError):
            data_parts.restore_files(self.repo)
        self.assertFalse((self.repo / self.name).exists())

    def test_whole_file_checksum_is_checked_separately(self):
        manifest = self.split()
        entry = manifest["files"][0]
        old_sha = entry["sha256"]
        entry["sha256"] = "0" * 64
        (self.repo / "data_parts" / old_sha).rename(self.repo / "data_parts" / entry["sha256"])
        for part in entry["parts"]:
            part["path"] = part["path"].replace(old_sha, entry["sha256"])
        self.save_manifest(manifest)
        with self.assertRaises(data_parts.DataPartsError):
            data_parts.restore_files(self.repo)
        self.assertFalse((self.repo / self.name).exists())

    def test_manifest_order_and_size_tampering_are_rejected(self):
        manifest = self.split()
        entry = manifest["files"][0]
        entry["parts"][0], entry["parts"][1] = entry["parts"][1], entry["parts"][0]
        self.save_manifest(manifest)
        with self.assertRaises(data_parts.DataPartsError):
            data_parts.verify_files(self.repo)
        entry["parts"][0], entry["parts"][1] = entry["parts"][1], entry["parts"][0]
        entry["parts"][0]["size"] -= 1
        self.save_manifest(manifest)
        with self.assertRaises(data_parts.DataPartsError):
            data_parts.verify_files(self.repo)

    def test_duplicate_targets_and_parts_are_rejected(self):
        manifest = self.split()
        manifest["files"].append(json.loads(json.dumps(manifest["files"][0])))
        with self.assertRaises(data_parts.DataPartsError):
            data_parts.validate_manifest(manifest)
        manifest["files"][-1]["path"] = "other.csv"
        with self.assertRaises(data_parts.DataPartsError):
            data_parts.validate_manifest(manifest)

    def test_path_escape_and_metadata_targets_are_rejected(self):
        manifest = self.split()
        for bad in ("../outside.csv", "/absolute.csv", "a/../x.csv", "a//x.csv", ".git/config", "data_parts/manifest.json", "C:/x.csv", "a\\x.csv"):
            with self.subTest(path=bad):
                manifest["files"][0]["path"] = bad
                self.save_manifest(manifest)
                with self.assertRaises(data_parts.DataPartsError):
                    data_parts.restore_files(self.repo)
        self.assertFalse((self.root / "outside.csv").exists())

    def test_symlink_target_and_ancestor_are_rejected(self):
        self.split()
        outside = self.root / "outside.csv"
        outside.write_bytes(b"keep")
        parent = self.repo / "原始数据"
        parent.mkdir()
        output = self.repo / self.name
        output.symlink_to(outside)
        with self.assertRaises(data_parts.DataPartsError):
            data_parts.restore_files(self.repo)
        output.unlink()
        parent.rmdir()
        parent.symlink_to(self.source / "原始数据", target_is_directory=True)
        with self.assertRaises(data_parts.DataPartsError):
            data_parts.restore_files(self.repo)
        self.assertEqual(outside.read_bytes(), b"keep")

    def test_symlink_part_is_rejected(self):
        manifest = self.split()
        part = self.repo / manifest["files"][0]["parts"][0]["path"]
        data = part.read_bytes()
        outside = self.root / "part.bin"
        outside.write_bytes(data)
        part.unlink()
        part.symlink_to(outside)
        with self.assertRaises(data_parts.DataPartsError):
            data_parts.verify_files(self.repo)

    def test_bad_source_checksum_does_not_publish_manifest(self):
        source = self.source / "bad.csv"
        source.write_bytes(b"actual")
        record = {"path": "bad.csv", "size": 6, "sha256": "0" * 64}
        with self.assertRaises(data_parts.DataPartsError):
            data_parts.split_files(self.repo, self.source, [record], chunk_size_bytes=7)
        self.assertFalse((self.repo / data_parts.MANIFEST).exists())

    def test_100_mb_or_larger_parts_are_rejected(self):
        for limit in (0, 100_000_000, 104_857_600):
            with self.subTest(limit=limit), self.assertRaises(data_parts.DataPartsError):
                self.split(limit=limit)


if __name__ == "__main__":
    unittest.main()
