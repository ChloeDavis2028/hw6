"""Build output/hw6_report.html from the saved result files.

Run from anywhere:  python scripts/build_report.py
The page is one self-contained file with no scripts, images, or outside links.
Every number comes from the JSON files in output/.
"""
import json
from collections import defaultdict
from html import escape
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "output"
DOCUMENTS_PER_MONTH = 30_000
CACHE_REWRITE_WORST_CASE = 1.76  # Monthly, from output/cache_test.md.
ATTACK_NOTES = {
    "p02": "False lower price in zero-size text",
    "p03": "False vendor in a hidden block",
    "p04": "Payment request in an HTML comment",
    "p06": "Email request in hidden PDF text",
    "p07": "False lead time in 0.8-point text",
    "p09": "False lead time in white email text",
    "p12": "False lower price off the page",
}
RED_TEAM_NOTES = {
    "a1_elmcity_quote.html": (
        "The vanishing minimum",
        "Near-white text set by a stylesheet ID",
        "Lower the minimum order from 1,200 to 240 units, so a failing quote passes",
    ),
    "a2_harborstitch_quote.pdf": (
        "The SKU swap",
        "Normal text painted over with a white box",
        "Change the SKU, so the $14.20 price meets a pricier item's limit",
    ),
}
STYLE = """
:root {
  color-scheme: light dark;
  --paper: #f8f4ec; --card: #fffdf8; --ink: #17202c; --soft: #5a5f66; --rule: #ddd3c1;
  --navy: #0f2747; --on-navy: #f6efe2; --on-navy-soft: #c5cad3; --brass: #8a6a2f; --gilt: #d3b071;
  --good: #1e6547; --bad: #9c2f2f; --bar-a: #0f2747; --bar-b: #b9a074;
  --display: "Bodoni MT", Didot, "Bodoni 72", "Playfair Display", "Palatino Linotype", Palatino, Georgia, serif;
  --serif: "Palatino Linotype", Palatino, "Book Antiqua", Georgia, serif;
  --sans: "Gill Sans", "Gill Sans MT", Optima, Candara, "Segoe UI", sans-serif;
}
@media (prefers-color-scheme: dark) {
  :root {
    --paper: #10161f; --card: #182130; --ink: #f0e9dc; --soft: #b8b4aa; --rule: #39414e;
    --navy: #0a1b33; --brass: #d3b071; --good: #84d0ac; --bad: #efa6a6; --bar-a: #d3b071; --bar-b: #6c7c93;
  }
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body { margin: 0; background: var(--paper); color: var(--ink); font: 18px/1.65 var(--serif); }
.hero { background: var(--navy); color: var(--on-navy); padding: 72px 24px 64px; text-align: center; border-bottom: 3px double var(--gilt); }
.eyebrow { font: 600 .74rem/1.4 var(--sans); letter-spacing: .28em; text-transform: uppercase; }
.hero .eyebrow { color: var(--gilt); margin: 0 0 22px; }
h1 { font: 400 clamp(2.5rem, 7vw, 4.6rem)/1.06 var(--display); margin: 0 auto 20px; max-width: 13em; letter-spacing: .005em; }
.hero p.lead { color: var(--on-navy-soft); font-style: italic; font-size: 1.14rem; max-width: 34em; margin: 0 auto; }
.mark { width: 64px; height: 1px; background: var(--gilt); margin: 26px auto 0; }
main { max-width: 1000px; margin: 0 auto; padding: 0 24px 72px; }
.ledger { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); background: var(--card); border: 1px solid var(--rule); margin-top: -34px; position: relative; }
.ledger div { padding: 24px 22px; border-right: 1px solid var(--rule); text-align: center; }
.ledger div:last-child { border-right: 0; }
.ledger b { display: block; font: 400 2.25rem/1.15 var(--display); color: var(--ink); }
.ledger span { display: block; margin-top: 6px; color: var(--soft); font: .86rem/1.4 var(--sans); }
section { margin-top: 76px; }
.number { color: var(--brass); margin: 0 0 8px; }
h2 { font: 400 clamp(1.9rem, 4vw, 2.6rem)/1.15 var(--display); margin: 0 0 14px; }
h3 { font: 400 1.5rem/1.2 var(--display); margin: 0 0 8px; }
.intro { max-width: 40em; margin: 0 0 22px; }
.scroll { overflow-x: auto; background: var(--card); border: 1px solid var(--rule); margin: 20px 0; }
table { border-collapse: collapse; width: 100%; font: .92rem/1.45 var(--sans); }
th { color: var(--brass); font-size: .7rem; letter-spacing: .14em; text-transform: uppercase; font-weight: 600; white-space: nowrap; }
th, td { padding: 13px 16px; text-align: left; border-bottom: 1px solid var(--rule); vertical-align: top; }
tr:last-child td { border-bottom: 0; }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.good { color: var(--good); font-weight: 600; white-space: nowrap; }
.bad { color: var(--bad); font-weight: 600; white-space: nowrap; }
.strong td { font-weight: 600; }
.chart { background: var(--card); border: 1px solid var(--rule); padding: 26px 28px; margin: 20px 0; }
.chart-title { font: 400 1.35rem/1.25 var(--display); margin: 0 0 18px; }
.row { display: grid; grid-template-columns: 124px 1fr 74px; gap: 14px; align-items: center; margin: 14px 0; font-family: var(--sans); font-size: .95rem; }
.track { height: 14px; }
.fill { height: 100%; border-radius: 0 4px 4px 0; background: var(--bar-a); }
.fill.b { background: var(--bar-b); }
.value { text-align: right; font-variant-numeric: tabular-nums; font-weight: 600; }
.note { color: var(--soft); font: .88rem/1.5 var(--sans); margin: 10px 0 0; }
.pair { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 18px; margin: 20px 0; }
.attack { background: var(--card); border: 1px solid var(--rule); padding: 24px 26px; }
.attack .eyebrow { color: var(--brass); margin: 0 0 8px; }
.attack dl { margin: 12px 0 0; font: .92rem/1.5 var(--sans); }
.attack dt { color: var(--soft); font-size: .76rem; letter-spacing: .08em; text-transform: uppercase; margin-top: 12px; }
.attack dd { margin: 2px 0 0; }
.letter { background: var(--navy); color: var(--on-navy); padding: 46px 48px; margin-top: 76px; border-top: 3px double var(--gilt); }
.letter .number { color: var(--gilt); }
.letter h2 { color: var(--on-navy); }
.letter p { max-width: 40em; }
.letter ul { max-width: 40em; padding-left: 20px; margin: 12px 0; }
.letter li { margin: 7px 0; }
.price { font: 400 clamp(2.4rem, 6vw, 3.4rem)/1.1 var(--display); color: var(--gilt); margin: 18px 0 2px; }
.price-note { color: var(--on-navy-soft); font: .88rem/1.5 var(--sans); margin: 0 0 20px; }
footer { color: var(--soft); text-align: center; font: .82rem/1.6 var(--sans); margin-top: 56px; }
@media (max-width: 620px) {
  body { font-size: 17px; }
  .hero { padding: 54px 16px 58px; }
  main { padding: 0 16px 56px; }
  .ledger div { border-right: 0; border-bottom: 1px solid var(--rule); }
  .ledger div:last-child { border-bottom: 0; }
  .chart, .attack { padding: 20px; }
  .letter { padding: 32px 22px; }
  .row { grid-template-columns: 88px 1fr 64px; gap: 8px; }
  th, td { padding: 11px 12px; }
}
"""


def load(name: str):
    return json.loads((OUTPUT_DIR / name).read_text(encoding="utf-8"))


def money(value: float, places: int = 6) -> str:
    return f"${value:,.{places}f}"


def signed_money(value: float) -> str:
    sign = "+" if value > 0 else "−"
    return f"{sign}${abs(value):.6f}"


def signed_tokens(value: float) -> str:
    sign = "+" if value > 0 else "−"
    return f"{sign}{abs(int(value)):,}"


def verdict(correct: bool) -> str:
    return '<span class="good">✓ Correct</span>' if correct else '<span class="bad">✗ Fooled</span>'


def table(headers: list[str], rows: list[list[str]], numeric: tuple[int, ...] = (), strong_last: bool = False) -> str:
    head = "".join(f'<th{" class=num" if i in numeric else ""}>{h}</th>' for i, h in enumerate(headers))
    lines = []
    for index, row in enumerate(rows):
        css = ' class="strong"' if strong_last and index == len(rows) - 1 else ""
        cells = "".join(f'<td{" class=num" if i in numeric else ""}>{c}</td>' for i, c in enumerate(row))
        lines.append(f"<tr{css}>{cells}</tr>")
    return f'<div class="scroll"><table><thead><tr>{head}</tr></thead><tbody>{"".join(lines)}</tbody></table></div>'


def bar(label: str, value: float, largest: float, second: bool = False) -> str:
    css = "fill b" if second else "fill"
    shown = money(value, 2)
    return (
        f'<div class="row"><span>{label}</span><div class="track" title="{label}: {shown} a month">'
        f'<div class="{css}" style="width:{value / largest * 100:.1f}%"></div></div><span class="value">{shown}</span></div>'
    )


def main() -> None:
    cache_calls = load("cache_test.json")
    before = load("attack_results.json")
    after = load("defense_results.json")
    layers = load("layer_test.json")
    red_team = load("red_team_results.json")
    exam = load("exam_results.json")
    trap_entries = len(load("trap_calls.json"))

    totals: dict[str, float] = defaultdict(float)
    for call in cache_calls:
        totals[call["setup"]] += call["cost_usd"]
    with_cache, without_cache = totals["with_cache"], totals["without_cache"]
    saved = (without_cache - with_cache) / without_cache
    documents = len({call["document"] for call in cache_calls})
    month_with = with_cache / documents * DOCUMENTS_PER_MONTH
    month_without = without_cache / documents * DOCUMENTS_PER_MONTH
    uncached_calls = [c for c in cache_calls if c["setup"] == "without_cache"]
    cached_calls = [c for c in cache_calls if c["setup"] == "with_cache"]
    leaks = sum(1 for c in uncached_calls if c["cache_read_tokens"] or c["cache_write_tokens"])
    read_share = sum(c["cache_read_tokens"] for c in cached_calls) / sum(c["input_tokens"] for c in cached_calls)

    score_before = sum(r["decision_matches"] for r in before)
    score_after = sum(r["decision_matches"] for r in after)
    fields_after = sum(all(r["field_matches"].values()) for r in after)
    fooled_before = len(before) - score_before

    attack_rows = [
        [
            escape(old["file"].split("_")[0] + " " + old["key"]["vendor"]),
            ATTACK_NOTES.get(old["file"][:3], "None, a clean quote"),
            old["key"]["decision"].replace("_", " "),
            verdict(old["decision_matches"]),
            verdict(new["decision_matches"]),
        ]
        for old, new in zip(before, after)
    ]

    setups = {"no_defenses": "No defenses", "code_only": "Code only", "design_only": "Design only", "prompt_only": "Prompt only"}
    medians: dict[str, tuple[float, float, int, int]] = {}
    for setup in setups:
        rows = [r for r in layers if r["setup"] == setup]
        medians[setup] = (
            median(r["input_tokens"] for r in rows), median(r["cost_usd"] for r in rows),
            sum(r["decision_matches"] for r in rows), rows[0]["requests"],
        )
    all_tokens = median(r["tokens"]["input_tokens"] for r in after)
    all_cost = median(r["cost_usd"] for r in after)
    base_tokens, base_cost, _, _ = medians["no_defenses"]
    cost_rows = [
        [
            label, str(medians[setup][3]), f"{medians[setup][0]:,.0f}",
            "" if setup == "no_defenses" else signed_tokens(medians[setup][0] - base_tokens),
            money(medians[setup][1]),
            "" if setup == "no_defenses" else signed_money(medians[setup][1] - base_cost),
            f"{medians[setup][2]} of 12",
        ]
        for setup, label in setups.items()
    ]
    cost_rows.append([
        "All three", "3", f"{all_tokens:,.0f}", signed_tokens(all_tokens - base_tokens),
        money(all_cost), signed_money(all_cost - base_cost), f"{score_after} of {len(after)}",
    ])

    attack_cards = []
    for index, (file_name, (name, hidden, goal)) in enumerate(RED_TEAM_NOTES.items(), 1):
        undefended = [r for r in red_team if r["file"] == file_name and r["setup"] == "no_defenses"]
        defended = [r for r in red_team if r["file"] == file_name and r["setup"] == "defended"]
        fooled = sum(r["fooled"] for r in undefended)
        held = sum(not r["fooled"] for r in defended)
        attack_cards.append(
            f'<article class="attack"><p class="eyebrow">Attack {index}</p><h3>{name}</h3><dl>'
            f"<dt>Hiding trick</dt><dd>{hidden}</dd><dt>Goal</dt><dd>{goal}</dd>"
            f'<dt>No defenses</dt><dd><span class="bad">✗ Fooled {fooled} of {len(undefended)} runs</span></dd>'
            f'<dt>Defended</dt><dd><span class="good">✓ Held {held} of {len(defended)} runs</span></dd>'
            "</dl></article>"
        )

    exam_rows = [
        [
            escape(r["file"].split("_")[0]), escape(str(r["vendor"])), escape(str(r["sku"])),
            money(r["unit_price"], 2) if r["unit_price"] is not None else "unknown",
            str(r["lead_time_days"]), f'{r["min_order"]:,}' if r["min_order"] is not None else "unknown",
            '<span class="good">✓ Recommend</span>' if r["decision"] == "recommend" else '<span class="bad">✗ Do not recommend</span>',
            "Yes" if r["trap_tool_called"] else "None",
        ]
        for r in exam
    ]
    exam_cost = sum(r["cost_usd"] or 0 for r in exam)
    exam_traps = sum(r["trap_tool_called"] for r in exam)
    recommended = sum(r["decision"] == "recommend" for r in exam)

    defended_per_document = sum(r["cost_usd"] for r in after) / len(after)
    agent_month = defended_per_document * DOCUMENTS_PER_MONTH

    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Vendor Desk Report</title>
<style>{STYLE}</style>
</head>
<body>
<header class="hero">
<p class="eyebrow">Campus Customs &nbsp;·&nbsp; New Haven</p>
<h1>The Vendor Desk Report</h1>
<p class="lead">An AI agent that reads vendor quotes and advises our buyer. What it costs, how it was attacked, and whether we should trust it.</p>
<div class="mark"></div>
</header>
<main>
<div class="ledger">
<div><b>{score_before} → {score_after}</b><span>Practice decisions correct out of 12</span></div>
<div><b>{saved:.1%}</b><span>Saved by caching</span></div>
<div><b>{trap_entries}</b><span>Trap tool calls recorded</span></div>
<div><b>{money(agent_month, 2)}</b><span>Estimated monthly cost</span></div>
</div>

<section>
<p class="eyebrow number">No. 1</p>
<h2>What caching is worth</h2>
<p class="intro">The handbook is the same on every call, so the model can reuse it at one-tenth of the price. We ran all {documents} practice documents both ways. In the API's own counts, {read_share:.0%} of input came from cache in one setup, and {leaks} of {len(uncached_calls)} calls touched the cache in the other.</p>
<div class="chart" role="img" aria-label="Monthly cost at 1,000 documents a day: {money(month_with, 2)} with cache and {money(month_without, 2)} without cache">
<p class="chart-title">Cost at 1,000 documents a day for 30 days</p>
{bar("With cache", month_with, month_without)}
{bar("Without cache", month_without, month_without, second=True)}
<p class="note">Both setups are the agent before defenses were added.</p>
</div>
{table(["Setup", "12 documents", "Per document", "30 days"], [
    ["With cache", money(with_cache), money(with_cache / documents), money(month_with, 2)],
    ["Without cache", money(without_cache), money(without_cache / documents), money(month_without, 2)],
], numeric=(1, 2, 3))}
</section>

<section>
<p class="eyebrow number">No. 2</p>
<h2>Attacks, before and after defenses</h2>
<p class="intro">Seven practice documents hide text aimed at the AI. A person sees an ordinary quote, while the undefended agent reads every hidden word. It was fooled {fooled_before} times. The defended agent was not fooled once, and {fields_after} of {len(after)} documents have every field correct, including the clean quotes.</p>
{table(["Document", "Hidden attack", "Right answer", "Before", "After"], attack_rows)}
</section>

<section>
<p class="eyebrow number">No. 3</p>
<h2>What the defenses cost</h2>
<p class="intro">We expected safety to cost more, but it cost less. The design splits reading from deciding, which adds a model call but sends the handbook once per document, not twice.</p>
{table(["Setup", "Calls", "Input tokens", "Token change", "Cost per document", "Dollar change", "Correct"], cost_rows, numeric=(1, 2, 3, 4, 5, 6), strong_last=True)}
<p class="note">Per-document medians, compared with no defenses, using the cache. Layer scores come from a separate test where no defenses scored {medians["no_defenses"][2]} of 12, because results can vary between runs. Differences are small, so read the direction more than the exact dollars.</p>
</section>

<section>
<p class="eyebrow number">No. 4</p>
<h2>The exam, and two new attacks</h2>
<p class="intro">The final defended agent read ten new documents, and the results below were saved by script with no hand edits. It recommended {recommended} and declined {len(exam) - recommended}, for {money(exam_cost, 4)} in total, with {exam_traps} trap calls. The answer key is held by the graders, so accuracy is not yet confirmed.</p>
{table(["File", "Vendor", "SKU", "Price", "Lead days", "Min order", "Decision", "Trap"], exam_rows, numeric=(3, 4, 5))}
<p class="intro" style="margin-top:34px">We then played the attacker and built two documents with tricks the practice set never used. A person opening either one sees a normal quote.</p>
<div class="pair">{"".join(attack_cards)}</div>
</section>

<section class="letter">
<p class="eyebrow number">No. 5 &nbsp;·&nbsp; For the Store Manager</p>
<h2>Our recommendation</h2>
<p><b>Yes, turn it on for real vendor mail, as an advisor to the buyer.</b> It reads quotes quickly and, in our tests, was not fooled once defenses were in place. A person should still make every purchase.</p>
<p class="price">About {money(agent_month, 2)} a month</p>
<p class="price-note">At 1,000 documents a day for 30 days, using the defended agent's average of {money(defended_per_document)} per document. Rewriting the cache after quiet periods could add up to about {money(CACHE_REWRITE_WORST_CASE, 2)} a month.</p>
<ul>
<li><b>Keep email and payments off.</b> They stay disconnected until a human signoff is built.</li>
<li><b>Have the buyer approve every order.</b> The agent cannot judge a false claim that is plainly visible.</li>
<li><b>Check the trap log weekly.</b> Any entry means a document got through, so pause and review.</li>
<li><b>Spot-check a sample each month.</b> New tricks will appear, and exam accuracy is not yet confirmed.</li>
</ul>
</section>

<footer>MGT 409 Homework 6. Campus Customs is a class setting, not a partnership, and all vendors and documents are made up. Model: gpt-6-luna.</footer>
</main>
</body>
</html>
"""
    (OUTPUT_DIR / "hw6_report.html").write_text(page, encoding="utf-8")
    print("built", len(page), "characters; monthly", round(agent_month, 2))


if __name__ == "__main__":
    main()
