# Handbook Token and Cost Estimate

Model: `gpt-6-luna`. These numbers cover the handbook alone. They leave out the instructions, the vendor document, and the model's reply.

## Summary

| | One call | 1,000 calls |
|---|---|---|
| Without caching | $0.00100580 | $1.0058 |
| With caching | $0.00125725 on the first call, then $0.00010058 on each later call | $0.1017 |

**Token count: 10,058 tokens (estimated).** Over 1,000 calls, caching saves about $0.90, or 89.9%.

## Token count and how I got it

I counted the tokens in `data/shop_handbook.md` on this computer with the `tiktoken` library (version 0.14.0). This uses no AI call and costs nothing. To repeat the count, run this from `My Work`:

```bash
python scripts/handbook_estimate.py
```

`tiktoken` does not have an entry for `gpt-6-luna`, so I used `o200k_base`, the encoding for recent OpenAI models. This means 10,058 is an estimate until a real run confirms it.

| Way of counting | Result |
|---|---|
| `tiktoken` with `o200k_base` (the number used here) | **10,058 tokens** |
| `tiktoken` with `cl100k_base` (older encoding, as a cross-check) | 10,184 tokens |
| Characters ÷ 4 (28,903 ÷ 4, rule of thumb) | 7,226 tokens |

The two `tiktoken` counts differ by about 1%, and both match the assignment's "about 10,000". The rule of thumb is about 28% too low because the handbook is mostly tables full of SKUs, prices, and punctuation, and these split into more tokens than ordinary sentences do.

## Prices used

From `data/prices.json`, per 1 million tokens:

| Token type | Price per 1M tokens | Price per token |
|---|---|---|
| Input | $0.10 | $0.0000001 |
| Cached input (a cache read) | $0.01 | $0.00000001 |
| Cache write | $0.125 | $0.000000125 |

The formula is: cost = tokens × price per 1M ÷ 1,000,000.

## The math

### Without caching

Every call pays the full input price.

- One call: 10,058 × $0.10 ÷ 1,000,000 = **$0.00100580**
- 1,000 calls: $0.00100580 × 1,000 = **$1.0058**

### With caching

The first call writes the handbook to the cache. Later calls read it from there.

- First call (cache write): 10,058 × $0.125 ÷ 1,000,000 = **$0.00125725**
- Each later call (cache read): 10,058 × $0.01 ÷ 1,000,000 = **$0.00010058**
- 1,000 calls: 1 write + 999 reads = $0.00125725 + (999 × $0.00010058) = $0.00125725 + $0.10047942 = **$0.10173667**, about **$0.1017**

### If every call were a cache read

This simpler view leaves out the first write, so it is the lowest possible cached cost.

- One call: 10,058 × $0.01 ÷ 1,000,000 = **$0.00010058**
- 1,000 calls: $0.00010058 × 1,000 = **$0.10058**

### What caching saves

- Dollars: $1.00580000 − $0.10173667 = **$0.90406333**
- Percent: $0.90406333 ÷ $1.00580000 = **89.9%**

The first call costs about 25% more with caching ($0.00125725 against $0.00100580). The second call more than makes up for that, because each cache read saves $0.00090522.

## What this estimate assumes

- The handbook comes first in every call and does not change, so it stays cached.
- The cache lasts through all 1,000 calls with exactly one write. If it expires, each new write adds $0.00115667 compared with a cache read.
- Every token is billed at the rates in `prices.json`.

## Checking against real runs in Problem 4

These real numbers come from the 12-document test in Problem 4. The full comparison is in `output/cache_test.md`.

| Check | Estimate | Real run | Difference | Why it differs |
|---|---|---|---|---|
| Input tokens, first call | 10,058 (handbook alone) | 10,519 average | +461 | The real call adds the prompt, tools, output format, and request |
| Cached tokens, first call | 10,058 | 10,370 average | +312 | The cache also holds the prompt and tool text |
| Input cost of one uncached call | $0.00100580 (handbook alone) | $0.00105190 | +4.6% | The same 461 extra tokens |
| Input cost of one cached call | $0.00010058 (handbook alone) | $0.00010370 | +3.1% | The same 312 extra tokens |

The token estimate held up. The larger miss was that each document takes two model calls, not one, so a real document costs about twice as much before output tokens are added.
