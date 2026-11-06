"""Run the final defended agent on all exam documents and save the results as they come.

Run from anywhere:  python scripts/exam_run.py
Saves output/exam_results.json. Nothing in it is edited by hand.
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

OUTPUT = ROOT / "output" / "exam_results.json"


def trap_count() -> int:
    tools.ensure_trap_log()
    return len(json.loads(tools.TRAP_LOG.read_text(encoding="utf-8")))


def main() -> None:
    desk = vendor_agent.make_agent()
    results = []
    for path in sorted((Path("data") / "exam_docs").iterdir()):
        traps_before = trap_count()
        answer, entry, error = None, {}, None
        try:
            answer, entry = vendor_agent.run_and_log(path, desk, "with_cache")
        except Exception as run_error:
            error = f"{type(run_error).__name__}: {run_error}"
        answer = answer or {}
        results.append({
            "file": path.name,
            "vendor": answer.get("vendor"),
            "sku": answer.get("sku"),
            "unit_price": answer.get("unit_price"),
            "lead_time_days": answer.get("lead_time_days"),
            "min_order": answer.get("min_order_units"),
            "decision": answer.get("decision"),
            "reason": answer.get("reason"),
            "trap_tool_called": trap_count() > traps_before,
            "input_tokens": entry.get("input_tokens"),
            "cached_tokens": entry.get("cache_read_tokens"),
            "output_tokens": entry.get("output_tokens"),
            "cost_usd": entry.get("cost_usd"),
        })
        print(path.name, answer.get("decision") or error, flush=True)
    OUTPUT.write_text(json.dumps(results, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
