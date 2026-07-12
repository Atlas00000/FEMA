"""Stable paths for INF-EXPORT live pointers + INF-RUN registry."""

from __future__ import annotations

import os
from pathlib import Path

_AI_DIR = Path(__file__).resolve().parent
# INF-DOCKER: set FEMA_REPO_ROOT=/work when AI and Presets are siblings in the container
REPO_ROOT = Path(os.environ.get("FEMA_REPO_ROOT", str(_AI_DIR.parent))).resolve()

LIVE_DIR = _AI_DIR / "data" / "live"
LATEST_BASKETS = LIVE_DIR / "latest_baskets.csv"
LATEST_EVENTS = LIVE_DIR / "latest_events.csv"
LATEST_META = LIVE_DIR / "latest_run.meta.txt"
LATEST_SOURCE = LIVE_DIR / "latest_source.txt"
CERTIFICATE_JSON = _AI_DIR / "certificate_PRODUCTION_EURUSD.json"
CERTIFICATE_MD = _AI_DIR / "certificate_PRODUCTION_EURUSD.md"
HEALTH_LATEST_JSON = LIVE_DIR / "health_latest.json"
HEALTH_LATEST_MD = LIVE_DIR / "health_latest.md"
HEALTH_STATE = LIVE_DIR / "health_state.json"
KB_DIR = _AI_DIR / "kb"
KB_RUNS_DIR = KB_DIR / "runs"
CANDIDATES_CSV = KB_DIR / "candidates.csv"
SEARCH_MAP_JSON = KB_DIR / "search_map.json"
GATE_RULES_JSON = KB_DIR / "gate_rules.json"
VERSIONS_JSON = KB_DIR / "versions.json"
LINEAGE_JSON = KB_DIR / "lineage.json"
GENOME_JSON = KB_DIR / "genome_PRODUCTION.json"
FINGERPRINT_LATEST = LIVE_DIR / "fingerprint_latest.json"
COMPAT_LATEST = LIVE_DIR / "compatibility_latest.json"
PRESETS_DIR = REPO_ROOT / "Presets"
PRESET_MANIFEST = PRESETS_DIR / "manifest.json"
PAUSE_FLAG_LIVE = LIVE_DIR / "pause_new.flag"
PAUSE_POLICY_MD = KB_DIR / "pause_policy.md"
