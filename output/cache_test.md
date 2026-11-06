# Cache Test: With and Without Cached Tokens

Caching saved **83.5%**. All 12 practice documents ran once in each setup with `gpt-6-luna`, for 24 runs and 48 model calls. Every call is saved in `output/cache_test.json`. To repeat the test, run this from `My Work`:

```bash
python scripts/cache_test.py
```

## Cost results

| | With cache | Without cache |
|---|---|---|
| Total for 12 documents | **$0.004425** | **$0.026844** |
| Average cost per document | **$0.000369** | **$0.002237** |
| Lowest and highest document | $0.000337 to $0.000408 | $0.002203 to $0.002295 |

**Saved with cache:** $0.022419 on 12 documents, or **83.5%**.

The math: ($0.026844 − $0.004425) ÷ $0.026844 = 83.5%.

## Proof each setup did what it should

| Check on the API's token counts | With cache | Without cache |
|---|---|---|
| Model calls | 24 | 24 |
| Total input tokens | 254,252 | 254,252 |
| Tokens read from cache | **249,159** | **0** |
| Tokens written to cache | 2,069 | **0** |
| Input tokens at the full price | 3,024 | 254,252 |
| Output tokens | 2,745 | 2,837 |
| Calls that read from cache | 24 of 24 | **0 of 24** |

- **Without cache counts:** all 24 calls show 0 cache reads and 0 cache writes.
- **With cache counts:** every call reused the cache, and 98.0% of its input tokens came from there.
- **All were new calls:** all 48 response IDs are different, so nothing was replayed.
- **Both setups sent the same input:** both show exactly 254,252 input tokens.

### How each setup worked

- **With cache:** the default setting. The API chooses a cache point by itself, and the handbook sits at the start of every call.
- **Without cache:** `openai_prompt_cache_options` is set to `{"mode": "explicit"}`. That turns off the automatic cache point, and the agent adds none of its own. Use `--no-cache` to run it this way.

## Real numbers against the Problem 2 estimate

| Measure | Problem 2 estimate | Real result | Why they differ |
|---|---|---|---|
| Tokens on one call | 10,058 (handbook alone) | 10,519 on the first call | The real call adds 182 prompt tokens and about 279 tokens for tools, the output format, and the request |
| Input cost of one uncached call | $0.00100580 | $0.00105190 | Same 461 extra tokens, about 4.6% more |
| Input cost of one cached read | $0.00010058 | $0.00010370 | 10,370 tokens were read on the first call |
| Model calls per document | 1 | 2 | The agent reads the document on one call and answers on the next |
| 1,000 documents without cache | $1.0058 | $2.2370 | Two calls per document, plus the output tokens |
| 1,000 documents with cache | $0.1017 | $0.3688 | The same reasons, plus small writes on each run |
| Savings from cache | 89.9% | 83.5% | Output tokens get no cache discount |

The token estimate was close. The dollar estimate was low because it priced the handbook alone on a single call, and it was never meant to include the whole run.

## Projection: 1,000 documents a day for 30 days

That is 30,000 documents, at the averages from this test.

| | Math | 30-day cost |
|---|---|---|
| With cache | 30,000 × $0.000369 | **$11.06** |
| Without cache | 30,000 × $0.002237 | **$67.11** |
| Saved | $67.11 − $11.06 | **$56.05** |

The test started with the handbook already in cache, so the with-cache number leaves out rewriting it. The API lists a 30-minute cache lifetime, so a quiet stretch can make it write the handbook again. Each rewrite adds about $0.00122. Once a day that is about $0.04 over 30 days, and at the worst case of once every 30 minutes all day it is about $1.76. Neither changes the conclusion.

## What surprised me and why

1. **The handbook goes out twice per document.** Reading with a tool takes two calls, and each carries the full handbook. This doubled the cost. Caching matters more for that reason, because the second call is almost entirely a cache read.
2. **My first no-cache method cost more than no caching.** I put a unique ID at the top of each call. It stopped all reads, but the API still wrote about 21,000 tokens to cache at the higher write price, for $0.00278 on one run instead of about $0.00223. That run did not count, because it still showed cached tokens. Checking only reads would have missed it.
3. **The savings were less than the 90% cache discount suggests.** Output tokens cost the same either way. Output was only 5% of the no-cache bill but 31% of the cached bill. Input alone dropped 88.0%.
4. **Some runs matched token for token.** Two no-cache p01 runs had identical counts, down to the reasoning tokens. Unique response IDs show they were separate calls. I do not know why the counts matched, though short, rule-based answers may simply repeat.
5. **Cache writes appear on nearly every run.** They are small, about 170 tokens per run, because the end of each prompt holds new text from that document.
6. **Caching did not change the decisions, and neither protected the agent.** All 12 decisions matched across the setups. But both recommended p03, an Ivy Print Co catalog page. The page says its vendor of record is Chapel Street Goods, an approved vendor, and the agent believed it, even though the handbook says Ivy Print is never recommended. No trap was touched, so an empty `trap_calls.json` does not mean every decision was right.
