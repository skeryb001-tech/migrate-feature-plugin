#!/usr/bin/env python3
"""测试路径冲突扫描器的核心分支。"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from scanMigrationConflicts import scan


class ScanMigrationConflictsTest(unittest.TestCase):
    """覆盖复用、同名、大小写和路径类型冲突。"""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.source = root / "source"
        self.target = root / "target"
        self.source.mkdir()
        self.target.mkdir()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def run_scan(self):
        return scan(self.source, self.target, {".git", "node_modules"})

    def test_same_content_is_reusable(self) -> None:
        (self.source / "upload.ts").write_text("export const upload = true\n")
        (self.target / "upload.ts").write_text("export const upload = true\n")

        conflicts, reusable = self.run_scan()

        self.assertEqual(conflicts, [])
        self.assertEqual([item.kind for item in reusable], ["same-content"])

    def test_different_content_is_blocked(self) -> None:
        (self.source / "upload.ts").write_text("source\n")
        (self.target / "upload.ts").write_text("target\n")

        conflicts, reusable = self.run_scan()

        self.assertEqual(reusable, [])
        self.assertEqual([item.kind for item in conflicts], ["exact-path-conflict"])

    def test_case_insensitive_path_is_blocked(self) -> None:
        (self.source / "Upload.ts").write_text("source\n")
        (self.target / "upload.ts").write_text("target\n")

        conflicts, _ = self.run_scan()

        self.assertEqual([item.kind for item in conflicts], ["case-insensitive-conflict"])

    def test_file_directory_type_is_blocked(self) -> None:
        (self.source / "assets").mkdir()
        (self.target / "assets").write_text("target file\n")

        conflicts, _ = self.run_scan()

        self.assertEqual([item.kind for item in conflicts], ["path-type-conflict"])


if __name__ == "__main__":
    result = unittest.main(exit=False)
    sys.exit(not result.result.wasSuccessful())
