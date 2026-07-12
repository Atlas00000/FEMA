"""Wave 6 park freeze is documentation only — no PARK features."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_AI = Path(__file__).resolve().parents[1]
_REPO = _AI.parent
if str(_AI) not in sys.path:
    sys.path.insert(0, str(_AI))


class TestWave6ParkFreeze(unittest.TestCase):
    def test_park_doc_lists_all_ids(self):
        text = (_AI / "kb" / "wave6_park_freeze.md").read_text(encoding="utf-8")
        for pid in (
            "PARK-01",
            "PARK-02",
            "PARK-03",
            "PARK-04",
            "PARK-05",
            "PARK-06",
        ):
            self.assertIn(pid, text)
        self.assertIn("Do not implement", text)
        self.assertIn("Auto-promote", text)

    def test_api_still_has_no_promote(self):
        sys.path.insert(0, str(_REPO / "ops" / "api"))
        import main as api

        paths = {getattr(r, "path", "") for r in api.app.routes}
        for p in paths:
            self.assertFalse(p.startswith("/v1/promote"))
            self.assertFalse(p.startswith("/v1/write"))


if __name__ == "__main__":
    unittest.main()
