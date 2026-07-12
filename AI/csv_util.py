#!/usr/bin/env python3
"""CSV helpers for FEMA schema-versioned AI logs (skip # FEMA_META lines)."""

from __future__ import annotations

import csv
from pathlib import Path


def parse_meta_lines(path: Path) -> dict[str, str]:
    """Parse leading '# FEMA_META key=value' lines and optional *.meta.txt sidecar."""
    meta: dict[str, str] = {}
    if not path.exists():
        return meta
    with path.open(encoding="utf-8-sig", errors="replace") as fh:
        for line in fh:
            s = line.strip()
            if not s:
                continue
            if s.startswith("# FEMA_META "):
                body = s[len("# FEMA_META ") :]
                if "=" in body:
                    k, v = body.split("=", 1)
                    meta[k.strip()] = v.strip()
                continue
            if s.startswith("#"):
                continue
            break
    sidecar = path.with_name(path.name.replace("_baskets.csv", "_run.meta.txt").replace("_events.csv", "_run.meta.txt"))
    if sidecar.exists():
        for line in sidecar.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            meta.setdefault(k.strip(), v.strip())
    return meta


def open_data_lines(path: Path):
    """Yield file lines that are not FEMA meta comments (for csv.reader)."""
    with path.open(newline="", encoding="utf-8-sig", errors="replace") as fh:
        for line in fh:
            s = line.lstrip()
            if s.startswith("#"):
                continue
            yield line


def read_csv_rows(path: Path) -> list[dict]:
    """DictReader over schema-versioned FEMA CSV (v1 or v2)."""
    rows: list[dict] = []
    # csv needs an iterator that supports newline handling — materialize filtered text
    text = "".join(open_data_lines(path))
    if not text.strip():
        return rows
    import io

    reader = csv.DictReader(io.StringIO(text))
    for raw in reader:
        if not raw:
            continue
        # skip empty trailing
        if not any((v or "").strip() for v in raw.values()):
            continue
        rows.append(raw)
    return rows
