"""ASI-P6 — basket recovery probability."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_AI = Path(__file__).resolve().parents[1]
if str(_AI) not in sys.path:
    sys.path.insert(0, str(_AI))

from fema_ops.asi.recovery import (
    REC_STATIC,
    expand_rec_rows,
    featurize_rec,
    recover_label,
    score_rec_baskets,
    train_rec,
    write_rec_review,
)


class TestRecoverLabel(unittest.TestCase):
    def test_tp_recovers(self):
        self.assertEqual(recover_label({"hit_tp": 1, "profit": 10}), 1)

    def test_profit_recovers(self):
        self.assertEqual(recover_label({"hit_tp": 0, "profit": 3.5}), 1)

    def test_bsl_fails(self):
        self.assertEqual(recover_label({"hit_tp": 0, "profit": -25, "hit_bsl": 1}), 0)


class TestExpand(unittest.TestCase):
    def test_recovery_label_propagates(self):
        rows = [
            {
                "basket_id": "b1",
                "open_time": "2024.01.02 10:00:00",
                "symbol": "EURUSD",
                "direction": "BUY",
                "max_depth": 3,
                "profit": 10.0,
                "hit_bsl": 0,
                "hit_tp": 1,
                "mae": -12,
                "mfe": 10,
                "bars_alive": 80,
                "ema_sep_atr": 0.2,
                "ema_slope": 0.01,
                "atr": 0.0007,
                "adx": 22,
                "dist_ema_trend_atr": 0.8,
                "spread_points": 8,
                "hour": 10,
                "dow": 2,
                "roll_wr": 0.55,
                "roll_pf": 1.2,
                "roll_n": 40,
                "ema_slope_accel": 0.001,
                "adx_accel": -0.5,
                "atr_expansion_rate": 0.02,
                "consecutive_same_dir": 2,
                "dist_ema_abs": 0.8,
                "impulse_score": 0.4,
            }
        ]
        rec = expand_rec_rows(rows)
        self.assertEqual(len(rec), 2)  # depths 2,3
        self.assertTrue(all(int(r["y_recover"]) == 1 for r in rec))
        X, y = featurize_rec(rec)
        self.assertEqual(X.shape[0], 2)
        self.assertEqual(int(y.sum()), 2)
        self.assertNotIn("profit", REC_STATIC)
        self.assertNotIn("mae", REC_STATIC)


class TestOfflineArtifacts(unittest.TestCase):
    def test_train_review_if_built(self):
        asi = _AI / "kb" / "asi"
        if not (asi / "rec_dataset_train.csv").is_file():
            self.skipTest("asi-rec-build required")
        report = train_rec(asi_dir=asi)
        self.assertTrue(report["ok"])
        self.assertTrue((asi / "rec_model.pkl").is_file())
        pack = write_rec_review(asi)
        self.assertIn("verdict_hint", pack)
        self.assertTrue((asi / "asi_p6_review_pack.md").is_file())

    def test_shadow_if_trained(self):
        asi = _AI / "kb" / "asi"
        if not (asi / "rec_model.pkl").is_file():
            self.skipTest("asi-rec-train required")
        baskets = _AI / "data" / "EURUSD_baskets_2018_2025.csv"
        if not baskets.is_file():
            self.skipTest("baskets csv required")
        shadow = score_rec_baskets(baskets, asi_dir=asi)
        self.assertEqual(shadow["schema"], "fema_asi_rec_shadow_run_v1")
        self.assertIn("exit_n", shadow["shadow"])


if __name__ == "__main__":
    unittest.main()
