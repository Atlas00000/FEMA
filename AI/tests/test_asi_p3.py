"""ASI-P3 — TEP shadow scoring."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

_AI = Path(__file__).resolve().parents[1]
if str(_AI) not in sys.path:
    sys.path.insert(0, str(_AI))

from fema_ops.asi.shadow import (
    equity_dd_pct,
    kill_criteria,
    score_baskets,
    write_review_pack,
)


class TestShadowHelpers(unittest.TestCase):
    def test_equity_dd(self):
        # +10, -25, +10 from 400 → peak 410, trough 385 → dd ~6.1%
        dd = equity_dd_pct([10.0, -25.0, 10.0], deposit=400.0)
        self.assertGreater(dd, 0)

    def test_kill_false_winners(self):
        k = kill_criteria(
            {
                "skip_n": 10,
                "false_skip_winners": 9,
                "skipped_steamrollers": 1,
                "skip_rate": 0.05,
                "steamroller_precision": 0.1,
                "net_skipped": 50.0,
            }
        )
        self.assertEqual(k["status"], "kill")


class TestShadowScore(unittest.TestCase):
    def test_score_promote(self):
        promote = _AI / "kb" / "asi" / "dataset_promote_frozen.csv"
        model = _AI / "kb" / "asi" / "tep_model.pkl"
        if not promote.is_file() or not model.is_file():
            self.skipTest("asi-build + asi-train required")
        report = score_baskets(promote)
        self.assertEqual(report["schema"], "fema_asi_shadow_run_v1")
        self.assertIn("skip_n", report["shadow"])
        self.assertIn("dd_if_skipped_pct", report["shadow"])
        self.assertIn("status", report["kill"])

    def test_review_pack(self):
        asi = _AI / "kb" / "asi"
        if not (asi / "tep_model.pkl").is_file():
            self.skipTest("asi-train required")
        pack = write_review_pack(asi_dir=asi)
        self.assertTrue((asi / "asi_p3_review_pack.json").is_file())
        self.assertTrue((asi / "asi_p3_review_pack.md").is_file())
        self.assertIn(pack["kill"]["status"], ("ok", "kill", "empty_skip"))


if __name__ == "__main__":
    unittest.main()
