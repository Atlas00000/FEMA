"""Thin ingest wrapper (INF-EXPORT / Wave 0 sync)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_AI_DIR = Path(__file__).resolve().parent.parent


def run_ingest(
    source: str = "auto",
    magic: str = "",
    from_dir: str | None = None,
    allow_empty: bool = False,
) -> int:
    script = _AI_DIR / "sync_from_agent.py"
    if not script.is_file():
        print(f"missing {script}", file=sys.stderr)
        return 1
    cmd = [sys.executable, str(script), "--source", source]
    if magic:
        cmd.extend(["--magic", magic])
    if from_dir:
        cmd.extend(["--from-dir", from_dir])
    if allow_empty:
        cmd.append("--allow-empty")
    return subprocess.call(cmd)
