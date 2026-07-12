"""Wave 1 contract tests (schema file + API auth surface)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_AI = _REPO / "AI"
if str(_AI) not in sys.path:
    sys.path.insert(0, str(_AI))


class TestWave1Contracts(unittest.TestCase):
    def test_schema_sql_exists(self):
        p = _REPO / "ops" / "postgres" / "init" / "001_schema.sql"
        self.assertTrue(p.is_file())
        text = p.read_text(encoding="utf-8")
        for table in ("runs", "baskets", "events", "health_snapshots", "sync_heartbeats"):
            self.assertIn(f"CREATE TABLE IF NOT EXISTS {table}", text)

    def test_certificate_json_loads(self):
        import json

        cert = json.loads(
            (_AI / "certificate_PRODUCTION_EURUSD.json").read_text(encoding="utf-8")
        )
        self.assertEqual(cert["preset"], "FEMA_EURUSD_M5_PRODUCTION")
        w = sum(float(v) for v in cert["health_weights"].values())
        self.assertAlmostEqual(w, 1.0, places=6)

    def test_api_module_has_readonly_routes(self):
        sys.path.insert(0, str(_REPO / "ops" / "api"))
        import main as api

        paths = {r.path for r in api.app.routes}
        self.assertIn("/v1/status", paths)
        self.assertIn("/v1/certificate", paths)
        self.assertIn("/v1/health/latest", paths)
        self.assertIn("/v1/runs", paths)
        # No write/promote
        for p in paths:
            self.assertFalse(p.startswith("/v1/promote"))
            self.assertFalse(p.startswith("/v1/write"))


if __name__ == "__main__":
    unittest.main()
