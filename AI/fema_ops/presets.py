"""Preset clone factory (INF-PRESET) — bookkeeping, not genetics."""

from __future__ import annotations

import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_AI_DIR = Path(__file__).resolve().parent.parent
if str(_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_DIR))

from paths import (  # noqa: E402
    CANDIDATES_CSV,
    GATE_RULES_JSON,
    KB_DIR,
    PRESET_MANIFEST,
    PRESETS_DIR,
    SEARCH_MAP_JSON,
)

SET_LINE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$")


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_manifest(path: Path | None = None) -> dict[str, Any]:
    return load_json(path or PRESET_MANIFEST)


def save_manifest(data: dict[str, Any], path: Path | None = None) -> None:
    p = path or PRESET_MANIFEST
    data["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def load_search_map(path: Path | None = None) -> dict[str, Any]:
    return load_json(path or SEARCH_MAP_JSON)


def parse_set(text: str) -> tuple[list[str], dict[str, str]]:
    """Return (all_lines, key->value for Inp* assignments)."""
    values: dict[str, str] = {}
    lines = text.splitlines()
    for line in lines:
        raw = line.strip()
        if not raw or raw.startswith(";"):
            continue
        m = SET_LINE.match(raw)
        if m:
            values[m.group(1)] = m.group(2)
    return lines, values


def read_set(path: Path) -> tuple[list[str], dict[str, str]]:
    return parse_set(path.read_text(encoding="utf-8", errors="replace"))


def apply_overrides(lines: list[str], overrides: dict[str, str]) -> list[str]:
    remaining = dict(overrides)
    out: list[str] = []
    for line in lines:
        stripped = line.strip()
        m = SET_LINE.match(stripped) if stripped and not stripped.startswith(";") else None
        if m and m.group(1) in remaining:
            key = m.group(1)
            out.append(f"{key}={remaining.pop(key)}")
        else:
            out.append(line)
    for key, val in remaining.items():
        out.append(f"{key}={val}")
    return out


def subsystem_for_key(search_map: dict[str, Any], key: str) -> str | None:
    for block in search_map.get("may_adapt_pairs") or []:
        if key in (block.get("keys") or []):
            return str(block["id"])
    return None


def validate_overrides(
    overrides: dict[str, str],
    subsystem: str,
    search_map: dict[str, Any],
) -> list[str]:
    """Return list of problems (empty = ok)."""
    problems: list[str] = []
    known = {b["id"]: b for b in search_map.get("may_adapt_pairs") or []}
    if subsystem not in known:
        problems.append(f"unknown subsystem '{subsystem}' — see search_map.json")
        return problems
    allowed = set(known[subsystem].get("keys") or [])
    frozen = set(search_map.get("frozen_keys_do_not_clone_as_search") or [])
    other_subs: set[str] = set()
    for key in overrides:
        if key in frozen:
            problems.append(f"{key} is frozen (not a search axis)")
            continue
        sub = subsystem_for_key(search_map, key)
        if sub is None:
            problems.append(f"{key} not in search map (add or drop)")
        elif sub != subsystem:
            other_subs.add(sub)
    if other_subs:
        problems.append(
            f"overrides touch other subsystems {sorted(other_subs)} — one subsystem only"
        )
    for key in overrides:
        sub = subsystem_for_key(search_map, key)
        if sub == subsystem and key not in allowed:
            # still in same subsystem block — keys list is authoritative
            pass
    return problems


def diff_summary(parent_vals: dict[str, str], overrides: dict[str, str]) -> str:
    parts = []
    for k, v in sorted(overrides.items()):
        old = parent_vals.get(k, "?")
        parts.append(f"{k}:{old}->{v}")
    return "; ".join(parts)


def next_candidate_id(manifest: dict[str, Any], prefix: str = "Candidate_X") -> str:
    used = set()
    for p in manifest.get("presets") or []:
        used.add(str(p.get("id") or ""))
    for n in range(1, 100):
        cid = f"{prefix}{n}"
        if cid not in used and not (PRESETS_DIR / f"{cid}.set").exists():
            return cid
    raise RuntimeError("no free Candidate_Xn id")


def append_candidate_row(row: dict[str, str], path: Path | None = None) -> None:
    p = path or CANDIDATES_CSV
    p.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "id",
        "parent",
        "subsystem",
        "diffs",
        "window",
        "symbol",
        "pf",
        "wr",
        "dd",
        "status",
        "failure_reason",
        "run_id",
        "notes",
    ]
    exists = p.is_file()
    with p.open("a", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        if not exists:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in fieldnames})


def clone_preset(
    *,
    candidate_id: str | None = None,
    subsystem: str,
    overrides: dict[str, str],
    parent_id: str = "PRODUCTION",
    notes: str = "",
    status: str = "queued",
    presets_dir: Path | None = None,
    manifest_path: Path | None = None,
    search_map_path: Path | None = None,
    allow_multi: bool = False,
) -> dict[str, Any]:
    presets_dir = presets_dir or PRESETS_DIR
    manifest_path = manifest_path or PRESET_MANIFEST
    search_map = load_search_map(search_map_path)
    manifest = load_manifest(manifest_path)

    if not overrides:
        raise ValueError("need at least one --set Key=Value override")

    problems = validate_overrides(overrides, subsystem, search_map)
    if problems and not allow_multi:
        raise ValueError("; ".join(problems))

    parent_file = presets_dir / f"{parent_id}.set"
    if not parent_file.is_file():
        # resolve via manifest
        for p in manifest.get("presets") or []:
            if p.get("id") == parent_id:
                parent_file = presets_dir / str(p.get("file") or f"{parent_id}.set")
                break
    if not parent_file.is_file():
        raise FileNotFoundError(f"parent preset not found: {parent_file}")

    cid = candidate_id or next_candidate_id(manifest)
    out_path = presets_dir / f"{cid}.set"
    if out_path.exists():
        raise FileExistsError(f"refusing overwrite: {out_path}")

    lines, parent_vals = read_set(parent_file)
    new_lines = apply_overrides(lines, overrides)
    diff = diff_summary(parent_vals, overrides)

    header = [
        f"; ID: {cid} | parent={parent_id} | subsystem={subsystem}",
        f"; DIFF: {diff}",
        f"; cloned={_utc_now()} | INF-PRESET factory (one subsystem)",
        f"; notes: {notes}" if notes else "; notes:",
        "",
    ]
    # drop old leading comment block until first Inp
    body_start = 0
    for i, line in enumerate(new_lines):
        if line.strip().startswith("Inp"):
            body_start = i
            break
    body = new_lines[body_start:]
    out_path.write_text("\n".join(header + body) + "\n", encoding="utf-8")

    entry = {
        "id": cid,
        "file": out_path.name,
        "parent": parent_id,
        "alias_of": None,
        "subsystem": subsystem,
        "diff_summary": diff,
        "status": status,
        "run_id": None,
        "notes": notes,
        "cloned_at": _utc_now(),
    }
    presets = list(manifest.get("presets") or [])
    presets.append(entry)
    manifest["presets"] = presets
    save_manifest(manifest, manifest_path)

    append_candidate_row(
        {
            "id": cid,
            "parent": parent_id,
            "subsystem": subsystem,
            "diffs": diff,
            "window": "",
            "symbol": "EURUSD",
            "pf": "",
            "wr": "",
            "dd": "",
            "status": status,
            "failure_reason": "",
            "run_id": "",
            "notes": notes,
        }
    )

    return {
        "id": cid,
        "file": str(out_path).replace("\\", "/"),
        "parent": parent_id,
        "subsystem": subsystem,
        "diff_summary": diff,
        "status": status,
        "warnings": problems,
    }


def parse_set_args(items: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(f"override must be Key=Value, got {item!r}")
        k, v = item.split("=", 1)
        out[k.strip()] = v.strip()
    return out


def list_subsystems() -> list[str]:
    sm = load_search_map()
    return [str(b["id"]) for b in sm.get("may_adapt_pairs") or []]


def gate_rules_summary() -> str:
    g = load_json(GATE_RULES_JSON)
    lines = [f"gates={','.join(x['id'] for x in g.get('gates') or [])}"]
    lines.append(f"auto_promote={g.get('promotion', {}).get('auto_promote')}")
    return " ".join(lines)
