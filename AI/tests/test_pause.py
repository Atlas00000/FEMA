"""EL6 would_pause_new unit tests."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_AI = Path(__file__).resolve().parents[1]
if str(_AI) not in sys.path:
    sys.path.insert(0, str(_AI))

from fema_ops.pause import would_pause_new


class TestWouldPause(unittest.TestCase):
    def test_keep_running_normal(self):
        d = would_pause_new(90.0, "normal", {"warning_active": False})
        self.assertFalse(d["would_pause_new"])

    def test_retire(self):
        d = would_pause_new(20.0, "retire", {"warning_active": False})
        self.assertTrue(d["would_pause_new"])

    def test_re_discovery_needs_persistence(self):
        a = would_pause_new(40.0, "re_discovery", {"warning_active": False})
        b = would_pause_new(40.0, "re_discovery", {"warning_active": True})
        self.assertFalse(a["would_pause_new"])
        self.assertTrue(b["would_pause_new"])

    def test_watch_with_warning(self):
        d = would_pause_new(45.0, "watch", {"warning_active": True})
        self.assertTrue(d["would_pause_new"])


if __name__ == "__main__":
    unittest.main()
