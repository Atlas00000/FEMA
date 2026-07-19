"""ASI-P5 — mid-basket steamroller early warning."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_AI = Path(__file__).resolve().parents[1]
if str(_AI) not in sys.path:
    sys.path.insert(0, str(_AI))

from fema_ops.asi.midbasket import (
    MID_STATIC,
    expand_mid_rows,
    export_mid_gate,
    featurize_mid,
    mid_checkpoints,
    score_mid_baskets,
    train_mid,
    write_mid_review,
)


class TestMidCheckpoints(unittest.TestCase):
    def test_range(self):
        self.assertEqual(mid_checkpoints(5), [2, 3, 4, 5])
        self.assertEqual(mid_checkpoints(3), [2, 3])
        self.assertEqual(mid_checkpoints(1), [])
        self.assertEqual(mid_checkpoints(8, max_warn=5), [2, 3, 4, 5])


class TestExpand(unittest.TestCase):
    def test_steamroller_label_propagates(self):
        rows = [
            {
                "basket_id": "b1",
                "open_time": "2024.01.02 10:00:00",
                "symbol": "EURUSD",
                "direction": "SELL",
                "max_depth": 4,
                "profit": -25.0,
                "hit_bsl": 1,
                "mae": -30,
                "mfe": 1,
                "bars_alive": 100,
                "ema_sep_atr": 0.1,
                "ema_slope": -0.01,
                "atr": 0.0008,
                "adx": 28,
                "dist_ema_trend_atr": -1.2,
                "spread_points": 8,
                "hour": 10,
                "dow": 2,
                "roll_wr": 0.55,
                "roll_pf": 1.2,
                "roll_n": 40,
                "ema_slope_accel": -0.002,
                "adx_accel": 1.0,
                "atr_expansion_rate": 0.05,
                "consecutive_same_dir": 3,
                "dist_ema_abs": 1.2,
                "impulse_score": 0.7,
            }
        ]
        mid = expand_mid_rows(rows)
        self.assertEqual(len(mid), 3)  # depths 2,3,4
        self.assertTrue(all(int(r["y_mid_steamroller"]) == 1 for r in mid))
        self.assertTrue(all(r["warn_depth"] in (2, 3, 4) for r in mid))
        X, y = featurize_mid(mid)
        self.assertEqual(X.shape[0], 3)
        self.assertEqual(int(y.sum()), 3)
        self.assertNotIn("profit", MID_STATIC)
        self.assertNotIn("mae", MID_STATIC)


class TestOfflineArtifacts(unittest.TestCase):
    def test_train_review_if_built(self):
        asi = _AI / "kb" / "asi"
        if not (asi / "mid_dataset_train.csv").is_file():
            self.skipTest("asi-mid-build required")
        report = train_mid(asi_dir=asi)
        self.assertTrue(report["ok"])
        self.assertTrue((asi / "mid_model.pkl").is_file())
        pack = write_mid_review(asi)
        self.assertIn("verdict_hint", pack)
        self.assertTrue((asi / "asi_p5_review_pack.md").is_file())

    def test_export_and_shadow(self):
        asi = _AI / "kb" / "asi"
        if not (asi / "mid_model.pkl").is_file():
            self.skipTest("asi-mid-train required")
        gate = export_mid_gate(asi_dir=asi)
        self.assertTrue(gate["ok"])
        self.assertTrue((asi / "mid_gate_v1.txt").is_file())
        baskets = _AI / "data" / "EURUSD_baskets_2018_2025.csv"
        if not baskets.is_file():
            self.skipTest("baskets csv required")
        shadow = score_mid_baskets(baskets, asi_dir=asi)
        self.assertEqual(shadow["schema"], "fema_asi_mid_shadow_run_v1")
        self.assertIn("warn_n", shadow["shadow"])


if __name__ == "__main__":
    unittest.main()