"""Pipeline skips health when demo baskets are empty."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest import mock

_AI = Path(__file__).resolve().parents[1]
if str(_AI) not in sys.path:
    sys.path.insert(0, str(_AI))


class TestPipeline(unittest.TestCase):
    def test_skips_health_when_no_rows(self):
        from fema_ops import pipeline as pl

        with mock.patch.object(pl, "_basket_rows", return_value=0), mock.patch(
            "fema_ops.ingest.run_ingest", return_value=0
        ), mock.patch("fema_ops.drift.detect_drift", return_value={"severity": "ok", "n_alerts": 0}), mock.patch(
            "fema_ops.factory.write_recommend",
            return_value={"compat_signal": "compatible", "cloneable": []},
        ), mock.patch(
            "fema_ops.observatory.write_observatory",
            return_value={"action": "wait_for_basket_close", "source": "demo"},
        ), mock.patch(
            "fema_ops.status.write_status",
            return_value={
                "phase": "test",
                "health": {"on_demo_path": False},
                "sync": {"header_only": True, "baskets_locked": False},
            },
        ), mock.patch(
            "fema_ops.artifacts.archive_from_live",
            return_value={"run_id": "x", "note": "skip"},
        ):
            report = pl.run_pipeline(with_archive=False, with_db=False, with_ci=False)
        self.assertTrue(report["ok"])
        self.assertFalse(report["health_ran"])
        names = {s["name"]: s for s in report["steps"]}
        self.assertTrue(names["health"].get("skipped"))
        self.assertTrue(names["fingerprint"].get("skipped"))
        self.assertTrue(names["status"].get("ok"))


if __name__ == "__main__":
    unittest.main()
