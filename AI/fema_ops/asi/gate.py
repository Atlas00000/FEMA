"""ASI-P4 — export offline TEP logistic gate for MT5 runtime."""

from __future__ import annotations

import json
import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np

GATE_SCHEMA = "fema_tep_gate_v1"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def export_tep_gate(
    *,
    asi_dir: Path,
    out_name: str = "tep_gate_v1.txt",
    require_guardrail_ok: bool = True,
) -> dict[str, Any]:
    """Export scaler + logistic weights for MQL AiTepGate.mqh."""
    asi_dir = Path(asi_dir)
    model_path = asi_dir / "tep_model.pkl"
    card_path = asi_dir / "tep_model_card.json"
    guard_path = asi_dir / "asi_guardrail_review_pack.json"

    if not model_path.is_file():
        raise FileNotFoundError(f"Missing {model_path} — run asi-train first")

    with model_path.open("rb") as fh:
        bundle = pickle.load(fh)
    model = bundle["model"]
    scaler = model.named_steps["scaler"]
    clf = model.named_steps["clf"]

    card = json.loads(card_path.read_text(encoding="utf-8")) if card_path.is_file() else {}
    feature_names = list(card.get("feature_names") or bundle.get("feature_names") or [])
    threshold = float(card.get("threshold", bundle.get("threshold", 1.0)))

    guard_kill = None
    if guard_path.is_file():
        guard_kill = json.loads(guard_path.read_text(encoding="utf-8")).get("kill", {}).get("status")
    if require_guardrail_ok and guard_kill not in (None, "ok"):
        raise ValueError(
            f"Guardrail review not ok (kill={guard_kill!r}) — "
            "run asi-review --guardrail or pass require_guardrail_ok=False"
        )

    coef = clf.coef_.ravel()
    if len(coef) != len(feature_names):
        raise ValueError(f"coef len {len(coef)} != features {len(feature_names)}")

    meta: dict[str, Any] = {
        "schema": GATE_SCHEMA,
        "exported_at": _utc_now(),
        "phase": "ASI-P4",
        "model_card": card_path.name,
        "split_profile": (json.loads((asi_dir / "splits.json").read_text(encoding="utf-8"))
                          if (asi_dir / "splits.json").is_file()
                          else {}).get("profile", "default"),
        "threshold": threshold,
        "intercept": float(clf.intercept_[0]),
        "feature_names": feature_names,
        "guardrail_kill": guard_kill,
        "philosophy": "guardrails_not_gates",
    }

    lines = [
        GATE_SCHEMA,
        f"threshold\t{threshold:.8f}",
        f"intercept\t{meta['intercept']:.12f}",
        f"exported_at\t{meta['exported_at']}",
        f"model_card\t{card_path.name}",
        "feature\tmean\tscale\tcoef",
    ]
    for i, name in enumerate(feature_names):
        lines.append(
            f"{name}\t{scaler.mean_[i]:.12f}\t{scaler.scale_[i]:.12f}\t{coef[i]:.12f}"
        )

    txt_path = asi_dir / out_name
    txt_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    json_path = asi_dir / "tep_gate.json"
    json_path.write_text(
        json.dumps(
            {
                **meta,
                "features": [
                    {
                        "name": feature_names[i],
                        "mean": float(scaler.mean_[i]),
                        "scale": float(scaler.scale_[i]),
                        "coef": float(coef[i]),
                    }
                    for i in range(len(feature_names))
                ],
                "paths": {"txt": txt_path.name},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    return {
        "ok": True,
        "threshold": threshold,
        "n_features": len(feature_names),
        "guardrail_kill": guard_kill,
        "paths": {"txt": str(txt_path), "json": str(json_path)},
    }
