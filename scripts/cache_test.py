"""Run all 12 practice documents with and without cache, then prove each setup.

Run from anywhere:  python scripts/cache_test.py
Saves every model call to output/cache_test.json. Each run is also added to
the usage log and audit trail, and any trap call goes to the trap file.
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

import agent as vendor_agent  # noqa: E402

SETUPS = (("with_cache", True), ("without_cache", False))
OUTPUT = ROOT / "output" / "cache_test.json"


def main() -> None:
    documents = sorted(path.relative_to(ROOT) for path in (ROOT / "data" / "practice_docs").iterdir())
    calls: list[dict] = []
    failures: list[str] = []

    for setup, use_cache in SETUPS:
        agent = vendor_agent.make_agent(use_cache)
        for document in documents:
            try:
                answer, entry = vendor_agent.run_and_log(document, agent, setup)
            except Exception as error:
                failures.append(f"{setup} {document.name}: {type(error).__name__}: {error}")
                print(failures[-1])
                continue
            for number, call in enumerate(entry["per_request"], 1):
                calls.append({"setup": setup, "document": document.as_posix(), "call": number, **call})
            print(f"{setup:14} {document.name:32} {answer['decision']:17} ${entry['cost_usd']:.6f}")
            OUTPUT.write_text(json.dumps(calls, indent=2), encoding="utf-8")

    without = [call for call in calls if call["setup"] == "without_cache"]
    leaked = [c for c in without if c["cache_read_tokens"] or c["cache_write_tokens"]]
    with_cache = [call for call in calls if call["setup"] == "with_cache"]
    not_reused = [c for c in with_cache if not c["cache_read_tokens"]]
    response_ids = [call["response_id"] for call in calls]

    print(f"\n{len(calls)} calls, {len(failures)} failed runs")
    print(f"without_cache calls showing cached tokens: {len(leaked)} of {len(without)}")
    print(f"with_cache calls with no cache read: {len(not_reused)} of {len(with_cache)}")
    print(f"unique response IDs: {len(set(response_ids))} of {len(response_ids)}")


if __name__ == "__main__":
    main()
