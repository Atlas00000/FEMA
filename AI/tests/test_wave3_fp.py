"""Wave 3 — Market Fingerprint / genome / compatibility."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_AI = _REPO / "AI"
if str(_AI) not in sys.path:
    sys.path.insert(0, str(_AI))


class TestWave3Fingerprint(unittest.TestCase):
    def test_schema_file(self):
        p = _AI / "schemas" / "market_fingerprint.schema.json"
        self.assertTrue(p.is_file())
        raw = json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(raw["properties"]["schema"]["const"], "fema_market_fingerprint_v0")
        for key in (
            "volatility",
            "trend_persistence",
            "liquidity",
            "session",
            "pullback",
            "ema_geometry",
            "regime",
        ):
            self.assertIn(key, raw["required"])

    def test_genome_exists(self):
        g = json.loads((_AI / "kb" / "genome_PRODUCTION.json").read_text(encoding="utf-8"))
        self.assertEqual(g["schema"], "fema_edge_genome_v0")
        self.assertIn("thrive", g)
        self.assertIn("fail", g)
        self.assertTrue((_AI / "kb" / "genome_PRODUCTION.md").is_file())
        self.assertTrue((_AI / "kb" / "telemetry_checklist.md").is_file())

    def test_compute_and_compat(self):
        from fema_ops.fingerprint import compute_fingerprint, score_compatibility

        rows = [
            {
                "direction": "BUY",
                "atr": "0.0002",
                "mae": "-5",
                "spread_points": "10",
                "max_depth": "3",
                "open_level": "1",
                "dist_ema_trend_atr": "0.5",
                "ema_slope": "0.00001",
                "ema_sep_atr": "2.0",
                "adx": "20",
                "hour": "3",
                "dow": "1",
                "open_time": "2026.01.02 03:00:00",
            }
            for _ in range(20)
        ]
        fp = compute_fingerprint(rows, window=20, run_id="test")
        self.assertEqual(fp["schema"], "fema_market_fingerprint_v0")
        self.assertEqual(fp["window"]["n_baskets"], 20)
        self.assertGreaterEqual(fp["regime"]["adx_lt_30_share"], 0.99)
        compat = score_compatibility(fp)
        self.assertEqual(compat["schema"], "fema_compatibility_v0")
        self.assertTrue(compat["shadow"])
        self.assertIn(compat["signal"], ("compatible", "watch", "investigate", "insufficient"))

    def test_deep_pullback_mismatch(self):
        from fema_ops.fingerprint import compute_fingerprint, score_compatibility

        rows = [
            {
                "direction": "SELL",
                "atr": "0.0003",
                "mae": "-24",
                "spread_points": "12",
                "max_depth": "5",
                "open_level": "5",
                "dist_ema_trend_atr": "2.0",
                "ema_slope": "0",
                "ema_sep_atr": "0.1",
                "adx": "35",
                "hour": "14",
                "dow": "2",
                "open_time": "2026.01.02 14:00:00",
            }
            for _ in range(30)
        ]
        fp = compute_fingerprint(rows, window=30)
        compat = score_compatibility(fp)
        self.assertIn(compat["signal"], ("watch", "investigate"))
        self.assertTrue(compat["suggest_subsystems"])


if __name__ == "__main__":
    unittest.main()
