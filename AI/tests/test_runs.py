"""Minimal tests for INF-RUN id format + no overwrite."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_AI = Path(__file__).resolve().parents[1]
if str(_AI) not in sys.path:
    sys.path.insert(0, str(_AI))

from fema_ops.runs import make_run_id, register_run, slugify_preset, unique_run_dir, window_hash


class TestRunId(unittest.TestCase):
    def test_slug(self):
        self.assertEqual(slugify_preset("FEMA_EURUSD_M5_PRODUCTION"), "PRODUCTION")
        self.assertEqual(slugify_preset("P2C-001_REG_ADX30"), "P2C-001_REG_ADX30")

    def test_format(self):
        wh = window_hash("EURUSD", "M5", "2026.01.01", "2026.07.31", "b.csv")
        rid = make_run_id("2026.01.01", "PRODUCTION", wh)
        self.assertTrue(rid.startswith("20260101_PRODUCTION_"))
        self.assertEqual(len(wh), 8)


class TestNoOverwrite(unittest.TestCase):
    def test_unique_suffix(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "abc").mkdir()
            rid, folder = unique_run_dir(root, "abc")
            self.assertEqual(rid, "abc_02")
            self.assertFalse(folder.exists())

    def test_register_twice(self):
        sample = _AI / "data" / "EURUSD_20260707_baskets.csv"
        if not sample.is_file():
            self.skipTest("sample baskets missing")
        with tempfile.TemporaryDirectory() as td:
            runs = Path(td)
            a = register_run(
                sample,
                preset="PRODUCTION",
                role="lock",
                window_start="2026.01.01",
                window_end="2026.07.31",
                runs_dir=runs,
                notes="t1",
            )
            b = register_run(
                sample,
                preset="PRODUCTION",
                role="lock",
                window_start="2026.01.01",
                window_end="2026.07.31",
                runs_dir=runs,
                notes="t2",
            )
            self.assertNotEqual(a["run_id"], b["run_id"])
            self.assertTrue(b["run_id"].endswith("_02"))
            self.assertTrue((runs / a["run_id"] / "metrics.json").is_file())
            self.assertTrue((runs / b["run_id"] / "metrics.json").is_file())
            idx = json.loads((runs / "index.json").read_text(encoding="utf-8"))
            self.assertEqual(len(idx), 2)


if __name__ == "__main__":
    unittest.main()
