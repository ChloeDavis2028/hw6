"""Run all 12 practice documents with no defenses and with each layer alone.

Run from anywhere:  python scripts/layer_test.py
Saves one row per document and setup to output/layer_test.json. These runs can
add to the trap file if an undefended setup falls for a document.
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

import agent as vendor_agent  # noqa: E402
import tools  # noqa: E402

OUTPUT = ROOT / "output" / "layer_test.json"
SETUPS = {
    "no_defenses": {"code": False, "design": False, "prompt": False},
    "code_only": {"code": True, "design": False, "prompt": False},
    "design_only": {"code": False, "design": True, "prompt": False},
    "prompt_only": {"code": False, "design": False, "prompt": True},
}
FIELDS = {
    "vendor": "vendor",
    "sku": "sku",
    "unit_price": "unit_price",
    "lead_time_days": "lead_time_days",
    "min_order_units": "min_order",
}


def trap_count() -> int:
    tools.ensure_trap_log()
    return len(json.loads(tools.TRAP_LOG.read_text(encoding="utf-8")))


def main() -> None:
    key = json.loads((ROOT / "data" / "practice_key.json").read_text(encoding="utf-8"))
    rows = []
    for setup, layers in SETUPS.items():
        desk = vendor_agent.make_agent(**layers)
        for correct in key:
            document = Path("data") / "practice_docs" / correct["file"]
            traps_before = trap_count()
            row = {"setup": setup, "file": correct["file"]}
            try:
                answer, entry = vendor_agent.run_and_log(document, desk, "with_cache")
                row |= {
                    "decision_matches": answer["decision"] == correct["decision"],
                    "wrong_fields": [f for f, k in FIELDS.items() if answer[f] != correct[k]],
                    "input_tokens": entry["input_tokens"],
                    "output_tokens": entry["output_tokens"],
                    "cache_read_tokens": entry["cache_read_tokens"],
                    "cache_write_tokens": entry["cache_write_tokens"],
                    "requests": entry["requests"],
                    "cost_usd": entry["cost_usd"],
                }
            except Exception as error:
                row |= {"decision_matches": False, "error": f"{type(error).__name__}: {error}"}
            row["trap_tool_called"] = trap_count() > traps_before
            rows.append(row)
            print(setup, correct["file"], row["decision_matches"], row.get("wrong_fields"),
                  "TRAP" if row["trap_tool_called"] else "", flush=True)
            OUTPUT.write_text(json.dumps(rows, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
