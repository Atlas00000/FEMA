"""CI schema gates (IS-P3-02) — certificate, gates, fingerprint, OpenAPI."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

_AI_DIR = Path(__file__).resolve().parent.parent
_REPO = _AI_DIR.parent
if str(_AI_DIR) not in sys.path:
    sys.path.insert(0, str(_AI_DIR))

from paths import (  # noqa: E402
    CERTIFICATE_JSON,
    GATE_RULES_JSON,
    REPO_ROOT,
    VERSIONS_JSON,
)

FP_SCHEMA = REPO_ROOT / "AI" / "schemas" / "market_fingerprint.schema.json"
OPENAPI_PATH = REPO_ROOT / "ops" / "schemas" / "openapi.json"
FORBIDDEN_PATH_PREFIXES = ("/v1/promote", "/v1/write", "/v1/clone", "/v1/retire")


def _fail(msg: str) -> dict[str, Any]:
    return {"ok": False, "error": msg}


def check_certificate() -> dict[str, Any]:
    if not CERTIFICATE_JSON.is_file():
        return _fail(f"missing {CERTIFICATE_JSON}")
    cert = json.loads(CERTIFICATE_JSON.read_text(encoding="utf-8"))
    w = cert.get("health_weights") or {}
    s = sum(float(v) for v in w.values())
    if abs(s - 1.0) > 1e-6:
        return _fail(f"health_weights sum={s} != 1.0")
    if cert.get("health_formula_version") != "health_v0":
        return _fail("health_formula_version must be health_v0")
    if not cert.get("lock_run_id"):
        return _fail("lock_run_id missing")
    return {"ok": True, "weights_sum": round(s, 6), "lock_run_id": cert["lock_run_id"]}


def check_gate_rules() -> dict[str, Any]:
    if not GATE_RULES_JSON.is_file():
        return _fail("gate_rules.json missing")
    g = json.loads(GATE_RULES_JSON.read_text(encoding="utf-8"))
    if g.get("schema") != "fema_gate_rules_v1":
        return _fail(f"unexpected gate schema {g.get('schema')}")
    gates = g.get("gates") or []
    ids = {x.get("id") for x in gates}
    if "G1" not in ids:
        return _fail("G1 gate missing")
    promo = (g.get("promotion") or {}).get("auto_promote")
    if promo is True:
        return _fail("auto_promote must not be true")
    return {"ok": True, "gates": sorted(ids), "auto_promote": promo}


def check_fingerprint_schema() -> dict[str, Any]:
    if not FP_SCHEMA.is_file():
        return _fail("market_fingerprint.schema.json missing")
    raw = json.loads(FP_SCHEMA.read_text(encoding="utf-8"))
    if raw.get("properties", {}).get("schema", {}).get("const") != "fema_market_fingerprint_v0":
        return _fail("fingerprint schema const mismatch")
    for key in ("volatility", "regime", "pullback", "session"):
        if key not in (raw.get("required") or []):
            return _fail(f"fingerprint required missing {key}")
    return {"ok": True, "schema": "fema_market_fingerprint_v0"}


def check_versions() -> dict[str, Any]:
    if not VERSIONS_JSON.is_file():
        return _fail("versions.json missing")
    v = json.loads(VERSIONS_JSON.read_text(encoding="utf-8"))
    comps = v.get("components") or {}
    for key in ("preset", "certificate", "health_model", "gate_rules"):
        if key not in comps:
            return _fail(f"versions.components missing {key}")
    return {"ok": True, "health_model": (comps.get("health_model") or {}).get("id")}


def export_openapi(path: Path | None = None) -> dict[str, Any]:
    """Write OpenAPI snapshot for CI (no promote routes)."""
    path = path or OPENAPI_PATH
    sys.path.insert(0, str(REPO_ROOT / "ops" / "api"))
    import main as api  # noqa: WPS433

    schema = api.app.openapi()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    return {"ok": True, "path": str(path.relative_to(REPO_ROOT)).replace("\\", "/")}


def check_openapi(path: Path | None = None) -> dict[str, Any]:
    path = path or OPENAPI_PATH
    if not path.is_file():
        try:
            export_openapi(path)
        except Exception as e:  # noqa: BLE001
            return _fail(f"openapi export failed: {e}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    paths = list((raw.get("paths") or {}).keys())
    bad = [p for p in paths if any(p.startswith(f) for f in FORBIDDEN_PATH_PREFIXES)]
    if bad:
        return _fail(f"forbidden write routes in OpenAPI: {bad}")
    for need in ("/v1/status", "/v1/certificate", "/v1/health/latest", "/healthz"):
        if need not in paths:
            return _fail(f"OpenAPI missing {need}")
    return {"ok": True, "routes": len(paths)}


def run_ci_gates(*, refresh_openapi: bool = True) -> dict[str, Any]:
    if refresh_openapi:
        try:
            export_openapi()
        except Exception as e:  # noqa: BLE001
            return {
                "ok": False,
                "checks": {"openapi_export": _fail(str(e))},
            }
    checks = {
        "certificate": check_certificate(),
        "gate_rules": check_gate_rules(),
        "fingerprint_schema": check_fingerprint_schema(),
        "versions": check_versions(),
        "openapi": check_openapi(),
    }
    ok = all(c.get("ok") for c in checks.values())
    return {"schema": "fema_ci_gates_v0", "ok": ok, "checks": checks}
