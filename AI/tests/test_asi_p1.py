"""ASI-P1 — labels, features, dataset build."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

_AI = Path(__file__).resolve().parents[1]
if str(_AI) not in sys.path:
    sys.path.insert(0, str(_AI))

from fema_ops.asi.dataset import merge_labeled_rows, shadow_skip_v0, split_rows
from fema_ops.asi.features import build_open_features, tep_derived
from fema_ops.asi.labels import classify_basket, label_summary


class TestLabels(unittest.TestCase):
    def test_steamroller_bsl(self):
        lab = classify_basket(
            {"hit_bsl": "1", "hit_tp": "0", "profit": "-25", "max_depth": "5", "mae": "-25"}
        )
        self.assertEqual(lab["label_class"], "steamroller_bsl")
        self.assertEqual(lab["y_steamroller"], 1)

    def test_winner(self):
        lab = classify_basket(
            {"hit_bsl": "0", "hit_tp": "1", "profit": "10", "max_depth": "2", "mae": "-2"}
        )
        self.assertEqual(lab["label_class"], "winner")
        self.assertEqual(lab["y_steamroller"], 0)

    def test_expansion_stress(self):
        lab = classify_basket(
            {"hit_bsl": "0", "hit_tp": "0", "profit": "-8", "max_depth": "4", "mae": "-12"}
        )
        self.assertEqual(lab["label_class"], "expansion_stress")
        self.assertEqual(lab["y_steamroller"], 1)


class TestFeatures(unittest.TestCase):
    def test_accel_from_prior(self):
        prev = {"ema_slope": "0.00001", "adx": "20", "atr": "0.00040", "direction": "BUY"}
        cur = {
            "ema_slope": "0.00005",
            "adx": "24",
            "atr": "0.00048",
            "dist_ema_trend_atr": "1.5",
            "direction": "BUY",
        }
        d = tep_derived(prev, cur)
        self.assertGreater(d["adx_accel"], 0)
        self.assertGreater(d["atr_expansion_rate"], 0)
        self.assertEqual(d["consecutive_same_dir"], 2)


class TestDataset(unittest.TestCase):
    def test_build_and_split(self):
        sample = _AI / "data" / "live" / "latest_baskets.csv"
        if not sample.is_file():
            self.skipTest("latest_baskets.csv missing")
        rows = merge_labeled_rows(__import__("csv_util").read_csv_rows(sample))
        self.assertGreater(len(rows), 0)
        self.assertIn("impulse_score", rows[0])
        self.assertIn("y_steamroller", rows[0])
        summ = label_summary(rows)
        self.assertEqual(summ["n"], len(rows))

        buckets = split_rows(
            rows,
            {
                "train": {"start": "2020.01.01", "end": "2023.12.31"},
                "calibrate": {"start": "2024.01.01", "end": "2025.12.31"},
                "promote_frozen": {"start": "2026.01.01", "end": "2026.07.31"},
            },
        )
        self.assertGreater(len(buckets["promote_frozen"]), 0)

    def test_shadow_skip(self):
        rows = [
            {"basket_id": "1", "impulse_score": "1", "profit": "10", "y_steamroller": "0"},
            {"basket_id": "2", "impulse_score": "5", "profit": "-25", "y_steamroller": "1"},
            {"basket_id": "3", "impulse_score": "9", "profit": "-25", "y_steamroller": "1"},
            {"basket_id": "4", "impulse_score": "2", "profit": "10", "y_steamroller": "0"},
        ]
        sh = shadow_skip_v0(rows, train_rows=rows, skip_quantile=0.75)
        self.assertGreaterEqual(sh["skip_rate"], 0.25)
        self.assertIn("skipped_steamrollers", sh)


if __name__ == "__main__":
    unittest.main()
