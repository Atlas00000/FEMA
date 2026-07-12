"""Wave 1 integration-style tests (no Docker required for most)."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_REPO = Path(__file__).resolve().parents[2]
_AI = _REPO / "AI"
_API = _REPO / "ops" / "api"
for p in (_AI, _API):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))


class TestWave1ApiAuth(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["FEMA_API_TOKEN"] = "test-token"
        os.environ["FEMA_REPO_ROOT"] = str(_REPO)
        # Force file fallback (no DB)
        os.environ.pop("FEMA_DATABASE_URL", None)
        import importlib

        import main as api

        importlib.reload(api)
        cls.api = api
        try:
            from fastapi.testclient import TestClient

            cls.client = TestClient(api.app)
            cls.has_client = True
        except Exception as e:  # noqa: BLE001
            cls.has_client = False
            cls._skip_reason = str(e)

    def test_healthz_open(self):
        if not self.has_client:
            self.skipTest(self._skip_reason)
        r = self.client.get("/healthz")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["plane"], "wave1")

    def test_v1_requires_bearer(self):
        if not self.has_client:
            self.skipTest(self._skip_reason)
        r = self.client.get("/v1/certificate")
        self.assertEqual(r.status_code, 401)

    def test_v1_certificate_ok(self):
        if not self.has_client:
            self.skipTest(self._skip_reason)
        r = self.client.get(
            "/v1/certificate",
            headers={"Authorization": "Bearer test-token"},
        )
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["preset"], "FEMA_EURUSD_M5_PRODUCTION")

    def test_v1_status_file_fallback(self):
        if not self.has_client:
            self.skipTest(self._skip_reason)
        # Ensure STATUS.json exists
        from fema_ops.status import write_status

        write_status()
        r = self.client.get(
            "/v1/status",
            headers={"Authorization": "Bearer test-token"},
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertIn("phase", body)

    def test_no_promote_route(self):
        if not self.has_client:
            self.skipTest(self._skip_reason)
        r = self.client.post(
            "/v1/promote",
            headers={"Authorization": "Bearer test-token"},
            json={},
        )
        self.assertEqual(r.status_code, 404)


class TestWave1DbIngestUnit(unittest.TestCase):
    def test_metrics_from_rows(self):
        from fema_ops.db_ingest import _metrics_from_rows

        m = _metrics_from_rows(
            [
                {"profit": "10"},
                {"profit": "-25"},
                {"profit": "10"},
            ]
        )
        self.assertEqual(m["n"], 3)
        self.assertAlmostEqual(m["net"], -5.0)
        self.assertGreater(m["profit_factor"], 0)
        self.assertAlmostEqual(m["win_rate"], 2 / 3, places=4)

    def test_ingest_baskets_file_calls_upsert(self):
        from fema_ops import db_ingest

        # Tiny CSV fixture
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "EURUSD_1_baskets.csv"
            p.write_text(
                "basket_id,open_time,close_time,symbol,direction,open_level,max_depth,"
                "profit,exit_reason,hit_tp,hit_bsl,mae,mfe,bars_alive,spread_points\n"
                "1,2026.01.01 00:00:00,2026.01.01 01:00:00,EURUSD,BUY,1,1,10.0,BASKET_TP,"
                "1,0,0,10,12,2\n",
                encoding="utf-8",
            )
            with mock.patch("fema_ops.db_ingest.db_store.upsert_run") as up, mock.patch(
                "fema_ops.db_ingest.db_store.replace_baskets", return_value=1
            ) as rb, mock.patch(
                "fema_ops.db_ingest.resolve_dirs",
                return_value=(Path(td), Path(td) / "art"),
            ):
                (Path(td) / "art" / "runs").mkdir(parents=True)
                out = db_ingest.ingest_baskets_file(
                    p, source="demo", role="demo", url="postgresql://x", copy_artifacts=True
                )
            self.assertEqual(out["n_baskets"], 1)
            self.assertEqual(out["source"], "demo")
            up.assert_called_once()
            rb.assert_called_once()
            kwargs = up.call_args.kwargs
            self.assertEqual(kwargs["source"], "demo")
            self.assertEqual(kwargs["role"], "demo")


class TestWave1SyncScript(unittest.TestCase):
    def test_sync_ps1_exists(self):
        p = _REPO / "ops" / "sync" / "sync.ps1"
        self.assertTrue(p.is_file())
        text = p.read_text(encoding="utf-8")
        self.assertIn("incoming", text)
        self.assertIn("demo", text)


if __name__ == "__main__":
    unittest.main()
