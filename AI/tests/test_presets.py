"""INF-PRESET clone + subsystem validation tests."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

_AI = Path(__file__).resolve().parents[1]
_REPO = _AI.parent
if str(_AI) not in sys.path:
    sys.path.insert(0, str(_AI))

from fema_ops.presets import clone_preset, parse_set_args, validate_overrides
from fema_ops.presets import load_search_map


class TestParse(unittest.TestCase):
    def test_set_args(self):
        d = parse_set_args(["InpAdxMax=25.0", "InpUseAdxGate=true"])
        self.assertEqual(d["InpAdxMax"], "25.0")


class TestValidate(unittest.TestCase):
    def test_one_subsystem_ok(self):
        sm = load_search_map()
        probs = validate_overrides({"InpUseSessionBlockNo23": "true"}, "session", sm)
        self.assertEqual(probs, [])

    def test_cross_subsystem_fails(self):
        sm = load_search_map()
        probs = validate_overrides(
            {"InpUseSessionBlockNo23": "true", "InpAdxMax": "25"},
            "session",
            sm,
        )
        self.assertTrue(any("other subsystems" in p for p in probs))

    def test_frozen_lot(self):
        sm = load_search_map()
        probs = validate_overrides({"InpBaseLot": "0.02"}, "cooldown", sm)
        self.assertTrue(any("frozen" in p for p in probs))


class TestClone(unittest.TestCase):
    def test_clone_writes_set(self):
        src = _REPO / "Presets" / "PRODUCTION.set"
        if not src.is_file():
            self.skipTest("PRODUCTION.set missing")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            presets = root / "Presets"
            presets.mkdir()
            shutil.copy(src, presets / "PRODUCTION.set")
            man = {
                "schema": "fema_preset_manifest_v1",
                "parent_lock": "PRODUCTION",
                "presets": [
                    {
                        "id": "PRODUCTION",
                        "file": "PRODUCTION.set",
                        "parent": None,
                        "status": "lock",
                    }
                ],
            }
            man_path = presets / "manifest.json"
            man_path.write_text(json.dumps(man), encoding="utf-8")
            cand_csv = root / "candidates.csv"
            # patch module paths via explicit args
            import fema_ops.presets as P

            old_csv = P.CANDIDATES_CSV
            try:
                P.CANDIDATES_CSV = cand_csv
                rec = clone_preset(
                    candidate_id="Candidate_X1",
                    subsystem="session",
                    overrides={"InpUseSessionBlockNo23": "true"},
                    presets_dir=presets,
                    manifest_path=man_path,
                    notes="unit test",
                )
            finally:
                P.CANDIDATES_CSV = old_csv
            out = presets / "Candidate_X1.set"
            self.assertTrue(out.is_file())
            text = out.read_text(encoding="utf-8")
            self.assertIn("InpUseSessionBlockNo23=true", text)
            self.assertEqual(rec["id"], "Candidate_X1")
            man2 = json.loads(man_path.read_text(encoding="utf-8"))
            self.assertEqual(man2["presets"][-1]["id"], "Candidate_X1")
            self.assertTrue(cand_csv.is_file())


if __name__ == "__main__":
    unittest.main()
