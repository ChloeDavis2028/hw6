"""Count the tokens in the shop handbook and price it, with no AI calls.

Run from My Work:  python scripts/handbook_estimate.py
Uses tiktoken, which counts tokens on this computer, so this costs nothing.
"""
import json
from pathlib import Path

import tiktoken

DATA = Path(__file__).resolve().parent.parent / "data"
MODEL = "gpt-6-luna"
CALLS = 1000

handbook = (DATA / "shop_handbook.md").read_text(encoding="utf-8")
prices = json.loads((DATA / "prices.json").read_text(encoding="utf-8"))[MODEL]

try:
    encoding_name = tiktoken.encoding_for_model(MODEL).name
    print(f"tiktoken knows {MODEL}: {encoding_name}")
except KeyError:
    encoding_name = "o200k_base"
    print(f"tiktoken does not know {MODEL}, so using {encoding_name}")

tokens = len(tiktoken.get_encoding(encoding_name).encode(handbook))


def per_token(price_per_million: float) -> float:
    return price_per_million / 1_000_000


uncached = tokens * per_token(prices["input_per_1m"])
cache_read = tokens * per_token(prices["cached_input_per_1m"])
cache_write = tokens * per_token(prices["cache_write_per_1m"])
cached_run = cache_write + (CALLS - 1) * cache_read

print(f"characters: {len(handbook):,}")
print(f"words: {len(handbook.split()):,}")
print(f"tokens ({encoding_name}): {tokens:,}")
print(f"tokens (cl100k_base): {len(tiktoken.get_encoding('cl100k_base').encode(handbook)):,}")
print(f"characters / 4 rule of thumb: {len(handbook) / 4:,.0f}")
print(f"one call, no cache:      ${uncached:.8f}")
print(f"one call, cache write:   ${cache_write:.8f}")
print(f"one call, cache read:    ${cache_read:.8f}")
print(f"{CALLS} calls, no cache:     ${uncached * CALLS:.6f}")
print(f"{CALLS} calls, cached:       ${cached_run:.6f}")
print(f"saved by caching:        ${uncached * CALLS - cached_run:.6f}"
      f" ({1 - cached_run / (uncached * CALLS):.1%})")
