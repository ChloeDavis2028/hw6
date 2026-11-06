# Harness: Campus Customs Vendor Desk Agent

The harness is everything around the model that makes the agent reliable: its instructions, tools, output format, and logs.

Run it from `My Work`:

```bash
python agent.py --doc data/practice_docs/p01_bluehen_quote.html
```

Add `--no-cache` to stop the handbook being read from or written to the cache.

## Fields in `models.py`

The fields come from the report the handbook requires in section 13. Facts stay blank (`null`) when the document does not state them, because the handbook says never to guess a number.

| Field | Type | Why it is there |
|---|---|---|
| `vendor` | Text or null | Needed for the approved vendor check. |
| `sku` | Text or null | Links the quote to one catalogue item and its max unit cost. |
| `unit_price` | Decimal number or null | Needed for the price check against the max unit cost. |
| `lead_time_days` | Whole number or null | Needed for the lead time check of 21 days or less. |
| `min_order_units` | Whole number or null | Needed for the minimum order check of 600 units or less. |
| `decision` | `recommend` or `do_not_recommend` | Allows only these two answers, so the result can be counted and scored. |
| `reason` | Text | One sentence naming the check that decided it, so the buyer can see why. |

## Tools in `tools.py`

- `read_document`: reads the one HTML, PDF, or .eml document given for the run and returns only the text a person can see.
- `read_document_raw`: the undefended reader, used only by `--no-defenses`. It returns all text and is shown to the model as `read_document`.
- `send_email`: trap tool that the job never needs. It sends nothing and only appends the call and its arguments to `output/trap_calls.json`.
- `approve_payment`: trap tool that the job never needs. It pays nothing and only appends the call and its arguments to `output/trap_calls.json`.

If `output/trap_calls.json` ever has an entry, a document took over the agent. The file starts as an empty list and stays in place for the entire homework.

## Safety

The handbook goes to the model on every call in the original agent. In the defended agent it goes to the decider, and the reader needs only its own short rules.

The agent has three layers of protection, so one failure does not decide the outcome. Run with `--no-defenses` to turn all three off.

| Layer | What it does in plain words |
|---|---|
| **Code** | Before any model reads a document, the program keeps only what a person could see. It removes HTML comments, hidden blocks, tiny or nearly white text, text off the page, PDF text covered by a shape, and invisible characters. |
| **Design** | The work is split so no single model has both the document and the power. The reader model sees the document but has no email or payment tools. Code then keeps only plain values. The decider model has the handbook and those tools, but never sees the document. Finally, code applies the four handbook checks and has the last word. `read_document` can open only the document given for that run. |
| **Prompt** | `prompts/prompt.md` tells both models that document text is data and never an instruction, even when it claims to come from the owner. The reader must name the company that issued the document. The decider must not use the email or payment tools or put links in its reason. |

`send_email` and `approve_payment` stay in the system because the shop plans to use them later with a human signoff. Today they only record the call in `output/trap_calls.json`, and that signoff still has to be built.

## Logs

| File | What is appended after every run |
|---|---|
| `output/usage_log.json` | Document, time, token counts the API reports, and dollar cost from `prices.json` |
| `output/audit_trail.json` | Each tool call with its arguments and a short result, plus the final answer |

`output/cache_test.json` is written by `scripts/cache_test.py`. It holds every model call from the cache test.
