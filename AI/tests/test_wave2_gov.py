"""Wave 2 governance / versioning contracts."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_AI = _REPO / "AI"
if str(_AI) not in sys.path:
    sys.path.insert(0, str(_AI))


class TestWave2Governance(unittest.TestCase):
    def test_versions_json(self):
        raw = json.loads((_AI / "kb" / "versions.json").read_text(encoding="utf-8"))
        comps = raw["components"]
        for key in ("preset", "certificate", "health_model", "gate_rules", "kb"):
            self.assertIn(key, comps)
        self.assertEqual(comps["health_model"]["id"], "health_v0")
        self.assertEqual(comps["certificate"]["version"], 1)

    def test_lineage_production_chain(self):
        raw = json.loads((_AI / "kb" / "lineage.json").read_text(encoding="utf-8"))
        active = raw["active_lock"]
        self.assertEqual(active["preset_id"], "PRODUCTION")
        self.assertEqual(active["run_id"], "20260101_PRODUCTION_13c52cd9")
        self.assertEqual(active["parent_preset_id"], "P2A-002_BSL_25")
        self.assertIn("retired_run_id", active)
        chain = raw["promotion_chain"]
        self.assertGreaterEqual(len(chain), 3)
        self.assertEqual(chain[-1]["decision"], "promote")
        for step in chain:
            for field in ("preset_id", "run_id", "parent_preset_id", "child_preset_id", "retired_run_id"):
                self.assertIn(field, step)

    def test_governance_docs_exist(self):
        kb = _AI / "kb"
        for name in (
            "raci.md",
            "retrain_rediscovery_policy.md",
            "research_loop_sop.md",
            "versions.json",
            "lineage.json",
        ):
            self.assertTrue((kb / name).is_file(), name)

    def test_status_cites_versions(self):
        from fema_ops.status import gather

        data = gather()
        self.assertEqual(data["versions"]["file"], "AI/kb/versions.json")
        self.assertEqual(data["versions"]["health_model"], "health_v0")
        self.assertIn("raci", data["governance"])
        self.assertTrue(data["health"]["formula"])

    def test_health_latest_has_formula_if_present(self):
        path = _AI / "data" / "live" / "health_latest.json"
        if not path.is_file():
            self.skipTest("no health_latest yet")
        raw = json.loads(path.read_text(encoding="utf-8"))
        self.assertTrue(str(raw.get("formula_version") or "").startswith("health_"))


if __name__ == "__main__":
    unittest.main()
