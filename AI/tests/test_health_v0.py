"""Unit tests for health_v0 weights + persistence (INF-OPS-005)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_AI = Path(__file__).resolve().parents[1]
if str(_AI) not in sys.path:
    sys.path.insert(0, str(_AI))

from cert_loader import ladder_label, load_certificate
from fema_ops.health import component_scores, weighted_health
from fema_ops.persistence import PersistenceState, update_persistence
from fema_ops.scoring import score_pf


class TestWeights(unittest.TestCase):
    def test_weights_sum_one(self):
        cert = load_certificate()
        s = sum(cert["health_weights"].values())
        self.assertAlmostEqual(s, 1.0, places=6)

    def test_weighted_health_bounds(self):
        cert = load_certificate()
        comps = {k: 80.0 for k in cert["health_weights"]}
        h = weighted_health(comps, cert["health_weights"])
        self.assertAlmostEqual(h, 80.0, places=2)

    def test_pf_green(self):
        cert = load_certificate()
        self.assertGreaterEqual(score_pf(1.35, cert["bands"]), 85.0)
        self.assertLess(score_pf(0.95, cert["bands"]), 55.0)


class TestPersistence(unittest.TestCase):
    def test_three_deteriorate_latches_warning(self):
        st = PersistenceState()
        flags = None
        for h in (90.0, 80.0, 70.0, 60.0):
            flags = update_persistence(st, h, ladder_label(h)["label"])
        assert flags is not None
        self.assertTrue(flags["warning_active"])
        self.assertGreaterEqual(flags["consecutive_deteriorate"], 3)

    def test_two_recover_clears(self):
        st = PersistenceState()
        for h in (90.0, 70.0, 55.0, 40.0):
            update_persistence(st, h, ladder_label(h)["label"])
        self.assertTrue(st.warning_active)
        update_persistence(st, 55.0, ladder_label(55)["label"])
        flags = update_persistence(st, 75.0, ladder_label(75)["label"])
        self.assertTrue(flags["clear_warning"] or not flags["warning_active"])
        self.assertFalse(st.warning_active)

    def test_flat_does_not_count(self):
        st = PersistenceState()
        update_persistence(st, 80.0, "investigate")
        update_persistence(st, 80.0, "investigate")
        update_persistence(st, 80.0, "investigate")
        self.assertEqual(st.consecutive_deteriorate, 0)
        self.assertFalse(st.warning_active)


class TestComponents(unittest.TestCase):
    def test_birth_like_metrics_score_high(self):
        cert = load_certificate()
        birth = cert["birth_metrics"]
        metrics = {
            "pf": float(birth["profit_factor"]),
            "wr": float(birth["win_rate"]),
            "tp_hit_rate": float(birth["tp_hit_rate_approx"]),
            "avg_bars_alive": float(birth["avg_bars_alive"]),
            "avg_depth": float(birth["avg_depth"]),
            "avg_mae_abs": 10.0,
            "avg_mfe": 8.0,
            "baskets_per_day": float(birth["baskets_per_day"]),
            "adx_ok_share": 0.85,
        }
        comps = component_scores(metrics, cert, reject_rate=0.01)
        h = weighted_health(comps, cert["health_weights"])
        self.assertGreaterEqual(h, 70.0)
        self.assertEqual(ladder_label(h, cert)["label"], "investigate" if h < 85 else "normal")


if __name__ == "__main__":
    unittest.main()
