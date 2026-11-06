# Campus Customs Vendor Desk

An AI agent that reads one vendor document (HTML, PDF, or email), pulls out the key facts, and recommends whether to buy under the Campus Customs Shop Handbook. Built for MGT 409 Homework 6 with PydanticAI and `gpt-6-luna` through Portkey.

## Setup

```bash
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your own `PORTKEY_API_KEY`.

## Run the agent

Run these from the project folder.

Defended agent, the default:

```bash
python agent.py --doc data/practice_docs/p01_bluehen_quote.html
```

Original agent with no defenses:

```bash
python agent.py --doc data/practice_docs/p01_bluehen_quote.html --no-defenses
```

Add `--no-cache` to stop the handbook being read from or written to the cache.

Each run prints the report and appends to `output/usage_log.json` and `output/audit_trail.json`. If `output/trap_calls.json` ever has an entry, a document took over the agent.

## How the defended agent works

A reader model sees the cleaned document but has no email or payment tools. A decider model has the handbook and those tools but never sees the document. Code applies the four handbook checks and makes the final decision. The handbook goes to the model on every call in the original agent. In the defended agent it goes only to the decider. See `output/harness.md` for details.

## Results

Open `output/hw6_report.html` by double-clicking it. It needs no internet.

To repeat the tests, run any of these. Each one calls the model and costs a small amount:

- `python scripts/attack_test.py` scores the defended agent against the practice key.
- `python scripts/attack_test.py --no-defenses` scores the original agent.
- `python scripts/red_team.py` runs the two attacks in `data/my_attacks/` on both agents.
- `python scripts/exam_run.py` runs the final agent on the exam documents.
- `python scripts/cache_test.py` compares the defended agent with and without cache. The saved results in `output/cache_test.json` came from the original agent in Problem 4.

Campus Customs is a class setting, not a partnership. All vendors and documents are made up.
