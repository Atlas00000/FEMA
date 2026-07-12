"""Wave 4 — factory recommend, EL7 trigger, experiments index."""

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


class TestWave4Factory(unittest.TestCase):
    def test_recommend_from_mismatches(self):
        from fema_ops.factory import recommend

        compat = {
            "signal": "investigate",
            "score": 40.0,
            "suggest_subsystems": ["adx", "grid", "execution"],
            "mismatches": [
                {"key": "regime.adx_lt_30_share", "value": 0.5, "subsystem": "adx"},
                {"key": "pullback.avg_depth", "value": 5.0, "subsystem": "grid"},
            ],
        }
        r = recommend(compat=compat, max_n=3)
        self.assertEqual(r["schema"], "fema_factory_recommend_v0")
        cloneable = r["cloneable"]
        self.assertLessEqual(len(cloneable), 3)
        ids = [c["subsystem"] for c in cloneable]
        self.assertIn("adx", ids)
        self.assertIn("grid", ids)
        # execution is not cloneable
        notes = [s for s in r["suggestions"] if not s.get("cloneable")]
        self.assertTrue(any(s.get("subsystem") == "execution" for s in notes))
        for c in cloneable:
            self.assertTrue(c.get("recipe"))
            self.assertTrue(c.get("hypothesis"))

    def test_propose_dry_run_explicit_subsystem(self):
        from fema_ops.factory import propose_clone

        out = propose_clone(subsystem="adx", dry_run=True, hypothesis="unit test")
        self.assertTrue(out["ok"])
        self.assertTrue(out["dry_run"])
        self.assertEqual(out["subsystem"], "adx")
        self.assertIn("InpAdxMax", out["overrides"])

    def test_factory_apply_temp_clone(self):
        from fema_ops.presets import clone_preset

        with tempfile.TemporaryDirectory() as td:
            tdir = Path(td)
            # minimal parent set + manifest
            (tdir / "PRODUCTION.set").write_text(
                "InpAdxMax=30\nInpUseAdxGate=true\nInpBaseLot=0.01\n",
                encoding="utf-8",
            )
            manifest = {
                "schema": "fema_preset_manifest_v1",
                "presets": [{"id": "PRODUCTION", "file": "PRODUCTION.set"}],
            }
            man_path = tdir / "manifest.json"
            man_path.write_text(json.dumps(manifest), encoding="utf-8")
            cand_csv = tdir / "candidates.csv"
            rec = clone_preset(
                candidate_id="Candidate_W4T",
                subsystem="adx",
                overrides={"InpAdxMax": "28"},
                parent_id="PRODUCTION",
                notes="wave4 unit",
                presets_dir=tdir,
                manifest_path=man_path,
            )
            self.assertEqual(rec["id"], "Candidate_W4T")
            self.assertTrue((tdir / "Candidate_W4T.set").is_file())
            body = (tdir / "Candidate_W4T.set").read_text(encoding="utf-8")
            self.assertIn("InpAdxMax=28", body)


class TestWave4El7(unittest.TestCase):
    def test_trigger_retire_opens(self):
        from fema_ops.el7 import evaluate_el7_trigger

        t = evaluate_el7_trigger(
            {
                "ladder": {"label": "retire"},
                "persistence": {"warning_active": False, "consecutive_deteriorate": 0},
                "health": 10,
                "would_pause_new": True,
            }
        )
        self.assertTrue(t["open_discovery"])
        self.assertEqual(t["reason"], "ladder_retire")

    def test_trigger_normal_closed(self):
        from fema_ops.el7 import evaluate_el7_trigger

        t = evaluate_el7_trigger(
            {
                "ladder": {"label": "normal"},
                "persistence": {"warning_active": False, "consecutive_deteriorate": 0},
                "health": 90,
            }
        )
        self.assertFalse(t["open_discovery"])

    def test_el7_dry_run_writes(self):
        from fema_ops.el7 import EL7_DRY_RUN, el7_dry_run

        plan = el7_dry_run(apply_lineage=False)
        self.assertEqual(plan["schema"], "fema_el7_dry_run_v0")
        self.assertTrue(plan["dry_run"])
        self.assertFalse(plan["applied"])
        self.assertTrue(EL7_DRY_RUN.is_file())
        self.assertGreaterEqual(len(plan["steps"]), 4)

    def test_docs_exist(self):
        kb = _AI / "kb"
        for name in (
            "el7_trigger_table.md",
            "el7_rediscovery_runbook.md",
            "clone_playbook.md",
        ):
            self.assertTrue((kb / name).is_file(), name)
        text = (_AI / "kb" / "pause_policy.md").read_text(encoding="utf-8")
        self.assertIn("IS-EL6-01", text)
        self.assertIn("NOT SIGNED", text)


class TestWave4Experiments(unittest.TestCase):
    def test_experiments_index(self):
        from fema_ops.el7 import EXPERIMENTS_INDEX, build_experiments_index

        out = build_experiments_index()
        self.assertEqual(out["schema"], "fema_experiments_index_v0")
        self.assertGreater(out["n"], 0)
        self.assertTrue(EXPERIMENTS_INDEX.is_file())
        row = out["experiments"][0]
        for key in (
            "preset",
            "run_id",
            "failure_reason",
            "parent_lock_run_id",
            "fingerprint",
        ):
            self.assertIn(key, row)
        # lock fingerprint from Wave 3
        lock = next(
            (
                e
                for e in out["experiments"]
                if e.get("run_id") == "20260101_PRODUCTION_13c52cd9"
            ),
            None,
        )
        if lock:
            self.assertTrue(lock.get("fingerprint"))


if __name__ == "__main__":
    unittest.main()
