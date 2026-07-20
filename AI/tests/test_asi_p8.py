"""ASI-P8 — regime intelligence."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_AI = Path(__file__).resolve().parents[1]
if str(_AI) not in sys.path:
    sys.path.insert(0, str(_AI))

from fema_ops.asi.regime import (
    REGIME_ORDER,
    classify_regime,
    derive_policy,
)


class TestClassify(unittest.TestCase):
    def test_liquidity_thin_hour(self):
        self.assertEqual(
            classify_regime({"hour": 3, "spread_points": 2, "adx": 22}),
            "liquidity_vacuum",
        )

    def test_expansion(self):
        r = classify_regime(
            {
                "hour": 12,
                "spread_points": 2,
                "impulse_score": 5,
                "atr_expansion_rate": 1.0,
                "adx": 26,
                "adx_accel": 0,
                "dist_ema_abs": 2,
                "consecutive_same_dir": 1,
                "ema_slope": 0.00002,
            }
        )
        self.assertEqual(r, "expansion")

    def test_taxonomy_complete(self):
        self.assertIn("pullback_trend", REGIME_ORDER)
        self.assertIn("impulse", REGIME_ORDER)
        self.assertEqual(len(REGIME_ORDER), 9)


class TestPolicy(unittest.TestCase):
    def test_skip_toxic(self):
        research = {
            "overall": {"steamroller_rate": 0.1},
            "regimes": {
                name: {
                    "n": 100,
                    "profit_factor": 1.2,
                    "steamroller_rate": 0.08,
                    "net": 50,
                    "dd_pct": 10,
                    "win_rate": 0.7,
                }
                for name in REGIME_ORDER
            },
        }
        research["regimes"]["impulse"] = {
            "n": 80,
            "profit_factor": 0.5,
            "steamroller_rate": 0.25,
            "net": -200,
            "dd_pct": 30,
            "win_rate": 0.4,
        }
        pol = derive_policy(research)
        self.assertEqual(pol["table"]["impulse"]["action"], "skip")
        self.assertIn("impulse", pol["skip"])


class TestOffline(unittest.TestCase):
    def test_build_if_data(self):
        baskets = _AI / "data" / "EURUSD_baskets_2018_2025.csv"
        if not baskets.is_file():
            self.skipTest("baskets missing")
        from fema_ops.asi.regime import build_regime_pack, score_regime_shadow, write_regime_review
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            report = build_regime_pack(baskets_path=baskets, out_dir=out, lock_baskets_path=None)
            self.assertGreater(report["n_baskets"], 0)
            self.assertTrue((out / "regime_scorecard.json").is_file())
            self.assertTrue((out / "regime_policy.json").is_file())
            shadow = score_regime_shadow(baskets, asi_dir=out)
            self.assertEqual(shadow["schema"], "fema_asi_regime_shadow_v1")
            (out / "asi_shadow_regime.json").write_text(
                __import__("json").dumps(shadow), encoding="utf-8"
            )
            pack = write_regime_review(out)
            self.assertIn("verdict_hint", pack)


if __name__ == "__main__":
    unittest.main()
