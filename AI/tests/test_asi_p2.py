"""ASI-P2 — TEP offline training."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np

_AI = Path(__file__).resolve().parents[1]
if str(_AI) not in sys.path:
    sys.path.insert(0, str(_AI))

from fema_ops.asi.tep import (
    evaluate_threshold,
    featurize,
    select_permissive_threshold,
    train_tep,
    train_tep_variant,
    TEP_FEATURES,
)
from csv_util import read_csv_rows


class TestTepCore(unittest.TestCase):
    def test_featurize_shape(self):
        rows = [
            {
                "direction": "BUY",
                "y_steamroller": "1",
                **{c: "1.0" for c in TEP_FEATURES},
            }
        ]
        X, y = featurize(rows, TEP_FEATURES + ["is_sell"])
        self.assertEqual(X.shape[0], 1)
        self.assertEqual(y[0], 1)

    def test_select_threshold_respects_max_skip(self):
        rows = [{"y_steamroller": str(i % 3), "profit": "-10" if i % 3 else "10"} for i in range(50)]
        for c in TEP_FEATURES:
            for r in rows:
                r.setdefault(c, "0.5")
                r.setdefault("direction", "BUY")
        proba = np.linspace(0, 1, len(rows))
        sel, _ = select_permissive_threshold(rows, proba, max_skip=0.10)
        self.assertLessEqual(sel.get("skip_rate", 0), 0.11)


class TestTepTrain(unittest.TestCase):
    def test_train_on_kb(self):
        asi = _AI / "kb" / "asi"
        if not (asi / "dataset_train.csv").is_file():
            self.skipTest("run asi-build first")
        report = train_tep(asi_dir=asi)
        self.assertTrue(report.get("ok"))
        self.assertTrue((asi / "tep_model_card.json").is_file())
        self.assertTrue((asi / "tep_model.pkl").is_file())
        card_path = asi / "tep_model_card.json"
        import json

        card = json.loads(card_path.read_text(encoding="utf-8"))
        self.assertEqual(card["label"], "y_steamroller")
        self.assertIn("ablation", card)


class TestTepGateExport(unittest.TestCase):
    def test_export_gate(self):
        asi = _AI / "kb" / "asi"
        if not (asi / "tep_model.pkl").is_file():
            self.skipTest("run asi-train first")
        from fema_ops.asi.gate import export_tep_gate

        report = export_tep_gate(asi_dir=asi)
        self.assertTrue(report.get("ok"))
        txt = asi / "tep_gate_v1.txt"
        self.assertTrue(txt.is_file())
        head = txt.read_text(encoding="utf-8").splitlines()[0]
        self.assertEqual(head, "fema_tep_gate_v1")


if __name__ == "__main__":
    unittest.main()
