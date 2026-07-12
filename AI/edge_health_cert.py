#!/usr/bin/env python3
"""ESR-W03 — certificate health_v0 (wrapper around fema_ops.health)."""

from __future__ import annotations

import sys
from pathlib import Path

_AI_DIR = Path(__file__).resolve().parent
if str(_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_DIR))

from fema_ops.cli import main  # noqa: E402

if __name__ == "__main__":
    # default to health if no subcommand
    argv = sys.argv[1:]
    if not argv or argv[0].startswith("-"):
        argv = ["health", *argv]
    raise SystemExit(main(argv))
