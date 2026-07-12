"""EL2 G1 gate unit tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_AI = Path(__file__).resolve().parents[1]
if str(_AI) not in sys.path:
    sys.path.insert(0, str(_AI))

from fema_ops.gates import classify_row, eval_g1


class TestG1(unittest.TestCase):
    def test_production_passes(self):
        r = eval_g1(
            {
                "pf": 1.36,
                "dd": 18,
                "window_start": "2026.01.01",
                "window_end": "2026.07.31",
            }
        )
        self.assertTrue(r["pass"])

    def test_p2d_dd_fails(self):
        r = eval_g1(
            {
                "pf": 1.40,
                "dd": 19,
                "window_start": "2026.01.01",
                "window_end": "2026.07.31",
            }
        )
        self.assertFalse(r["pass"])
        self.assertEqual(r["failure_reason"], "dd_breach")

    def test_stale_slice(self):
        r = eval_g1(
            {
                "pf": 1.50,
                "dd": 10,
                "window_start": "2025.01.01",
                "window_end": "2025.12.31",
            }
        )
        self.assertTrue(r["stale_slice"])
        self.assertFalse(r["pass"])

    def test_classify_lock_row22(self):
        c = classify_row(
            {
                "row": 22,
                "preset": "PRODUCTION",
                "status": "Candidate",
                "pf": 1.36,
                "dd": 18,
                "window_start": "2026.01.01",
                "window_end": "2026.07.31",
            }
        )
        self.assertEqual(c["status"], "lock")


if __name__ == "__main__":
    unittest.main()
