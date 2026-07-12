"""FEMA read-only Ops API (Wave 1 / IS-P2). No write or promote endpoints."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# Allow importing fema_ops when mounted
_AI = Path(os.environ.get("FEMA_REPO_ROOT", "/work")) / "AI"
if _AI.is_dir() and str(_AI) not in sys.path:
    sys.path.insert(0, str(_AI))

app = FastAPI(
    title="FEMA Ops API",
    version="0.1.0",
    description="Read-only Edge Ops plane — Wave 1. Human promote stays offline.",
)
_security = HTTPBearer(auto_error=False)


def _token() -> str:
    return os.environ.get("FEMA_API_TOKEN", "fema-dev-token")


def require_auth(
    creds: HTTPAuthorizationCredentials | None = Security(_security),
) -> None:
    expected = _token()
    if not expected:
        return
    if creds is None or creds.scheme.lower() != "bearer" or creds.credentials != expected:
        raise HTTPException(status_code=401, detail="unauthorized")


def _db_url() -> str | None:
    return os.environ.get("FEMA_DATABASE_URL")


def _ai_dir() -> Path:
    return Path(os.environ.get("FEMA_REPO_ROOT", str(Path(__file__).resolve().parents[2]))) / "AI"


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "plane": "wave1"}


@app.get("/v1/status")
def v1_status(_: None = Depends(require_auth)) -> dict[str, Any]:
    """Prefer DB summary; fall back to AI/STATUS.json."""
    url = _db_url()
    if url:
        try:
            from fema_ops.db_store import fetch_status_summary

            return fetch_status_summary(url)
        except Exception as e:  # noqa: BLE001 — surface for operators
            fallback = _file_status()
            fallback["db_error"] = str(e)
            return fallback
    return _file_status()


def _file_status() -> dict[str, Any]:
    p = _ai_dir() / "STATUS.json"
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    return {"error": "STATUS.json missing — run fema_ops status"}


@app.get("/v1/certificate")
def v1_certificate(_: None = Depends(require_auth)) -> dict[str, Any]:
    p = _ai_dir() / "certificate_PRODUCTION_EURUSD.json"
    if not p.is_file():
        raise HTTPException(404, "certificate not found")
    return json.loads(p.read_text(encoding="utf-8"))


@app.get("/v1/health/latest")
def v1_health_latest(_: None = Depends(require_auth)) -> dict[str, Any]:
    url = _db_url()
    if url:
        try:
            from fema_ops.db_store import fetch_latest_health

            row = fetch_latest_health(url)
            if row:
                return row
        except Exception:
            pass
    p = _ai_dir() / "data" / "live" / "health_latest.json"
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    raise HTTPException(404, "no health snapshot")


@app.get("/v1/runs")
def v1_runs(
    role: str | None = None,
    source: str | None = None,
    limit: int = 50,
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    url = _db_url()
    if not url:
        raise HTTPException(503, "FEMA_DATABASE_URL not set")
    from fema_ops.db_store import list_runs

    return {"runs": list_runs(url, role=role, source=source, limit=min(limit, 200))}


@app.get("/v1/runs/{run_id}")
def v1_run(run_id: str, _: None = Depends(require_auth)) -> dict[str, Any]:
    url = _db_url()
    if not url:
        raise HTTPException(503, "FEMA_DATABASE_URL not set")
    from fema_ops.db_store import get_run

    row = get_run(url, run_id)
    if not row:
        raise HTTPException(404, "run not found")
    return row


@app.get("/v1/runs/{run_id}/baskets")
def v1_baskets(
    run_id: str,
    limit: int = 100,
    _: None = Depends(require_auth),
) -> dict[str, Any]:
    url = _db_url()
    if not url:
        raise HTTPException(503, "FEMA_DATABASE_URL not set")
    from fema_ops.db_store import list_baskets

    return {
        "run_id": run_id,
        "baskets": list_baskets(url, run_id, limit=min(limit, 500)),
    }
