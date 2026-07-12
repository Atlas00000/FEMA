"""EL3 lock / certificate confirm tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_AI = Path(__file__).resolve().parents[1]
if str(_AI) not in sys.path:
    sys.path.insert(0, str(_AI))

from fema_ops.lock_confirm import LOCK_RUN_ID, confirm, parse_set
from paths import PRESETS_DIR


class TestLockConfirm(unittest.TestCase):
    def test_parse_production_set(self):
        kv = parse_set(PRESETS_DIR / "PRODUCTION.set")
        self.assertEqual(kv.get("InpUseAdxGate"), "true")
        self.assertEqual(float(kv["InpBasketSl"]), 25.0)
        self.assertEqual(float(kv["InpBasketTp"]), 10.0)

    def test_confirm_passes(self):
        r = confirm()
        self.assertEqual(r["status"], "confirmed")
        self.assertEqual(r["lock_run_id"], LOCK_RUN_ID)
        failed = [c for c in r["checks"] if not c["ok"]]
        self.assertEqual(failed, [])


if __name__ == "__main__":
    unittest.main()
