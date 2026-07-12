"""Wave 5 — artifacts, CI gates, drift, platform docs."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_AI = _REPO / "AI"
if str(_AI) not in sys.path:
    sys.path.insert(0, str(_AI))


class TestWave5CiGates(unittest.TestCase):
    def test_ci_gates_pass(self):
        from fema_ops.ci_gates import run_ci_gates

        out = run_ci_gates(refresh_openapi=True)
        self.assertTrue(out["ok"], out)
        self.assertTrue((_REPO / "ops" / "schemas" / "openapi.json").is_file())
        for name in (
            "certificate",
            "gate_rules",
            "fingerprint_schema",
            "versions",
            "openapi",
        ):
            self.assertTrue(out["checks"][name]["ok"], name)

    def test_openapi_no_promote(self):
        raw = json.loads(
            (_REPO / "ops" / "schemas" / "openapi.json").read_text(encoding="utf-8")
        )
        for p in raw.get("paths") or {}:
            self.assertFalse(p.startswith("/v1/promote"))
            self.assertFalse(p.startswith("/v1/write"))


class TestWave5Artifacts(unittest.TestCase):
    def test_archive_and_manifest(self):
        from fema_ops.artifacts import archive_from_live, list_artifact_runs, run_dir

        from paths import LATEST_BASKETS

        if not LATEST_BASKETS.is_file():
            self.skipTest("no latest baskets")
        out = archive_from_live(run_id="wave5_test_archive", source="demo", role="demo")
        self.assertEqual(out["run_id"], "wave5_test_archive")
        man = run_dir("wave5_test_archive") / "manifest.json"
        self.assertTrue(man.is_file())
        meta = json.loads(man.read_text(encoding="utf-8"))
        self.assertEqual(meta["schema"], "fema_artifact_manifest_v0")
        rows = list_artifact_runs(limit=20)
        self.assertTrue(any(r["run_id"] == "wave5_test_archive" for r in rows))

    def test_rehydrate_requires_db_or_raises_clean(self):
        from fema_ops.artifacts import rehydrate_run

        # Without DB URL, psycopg connect fails — ensure FileNotFound for missing run
        with self.assertRaises(FileNotFoundError):
            rehydrate_run("definitely_missing_run_xyz")


class TestWave5Drift(unittest.TestCase):
    def test_detect_drift_writes(self):
        from fema_ops.drift import DRIFT_LATEST, detect_drift

        r = detect_drift()
        self.assertEqual(r["schema"], "fema_drift_v0")
        self.assertIn(r["severity"], ("ok", "warn", "high"))
        self.assertTrue(DRIFT_LATEST.is_file())
        self.assertTrue(r.get("shadow"))


class TestWave5Docs(unittest.TestCase):
    def test_platform_and_queue(self):
        self.assertTrue((_AI / "kb" / "platform_modules.md").is_file())
        self.assertTrue((_REPO / "ops" / "tester_queue" / "README.md").is_file())
        self.assertTrue((_REPO / "ops" / "tester_queue" / "queue.json").is_file())
        self.assertTrue((_REPO / ".github" / "workflows" / "ci.yml").is_file())
        q = json.loads(
            (_REPO / "ops" / "tester_queue" / "queue.json").read_text(encoding="utf-8")
        )
        self.assertEqual(q["schema"], "fema_tester_queue_v0")
        self.assertEqual(q["max_concurrent"], 1)


if __name__ == "__main__":
    unittest.main()
