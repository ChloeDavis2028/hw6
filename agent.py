"""Campus Customs vendor desk agent.

Run from My Work:  python agent.py --doc data/practice_docs/p01_bluehen_quote.html
Add --no-cache to stop the handbook being reused from cache.
Add --no-defenses to run the original agent with no protections.

How the defended agent is put together:
  1. Code cleans the document, so hidden text never reaches a model.
  2. The reader model sees the document but has no email or payment tools.
  3. Code checks the reader's facts, so only plain values move on.
  4. The decider model has the handbook and the trap tools, but never sees the document.
  5. Code applies the handbook's four checks and has the final say.

After every run this appends to output/usage_log.json and output/audit_trail.json.
"""
import argparse
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from dotenv import load_dotenv
from pydantic_ai import Agent, Tool, capture_run_messages
from pydantic_ai.messages import ModelMessage, ModelResponse, ToolCallPart, ToolReturnPart
from pydantic_ai.usage import RunUsage, UsageLimits
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider

import tools
from models import DecisionDraft, VendorFacts, VendorReport

ROOT = Path(__file__).resolve().parent
MODEL_NAME = "gpt-6-luna"  # The only model this assignment allows.
PORTKEY_BASE_URL = "https://api.portkey.ai/v1"
USAGE_LOG = ROOT / "output" / "usage_log.json"
AUDIT_TRAIL = ROOT / "output" / "audit_trail.json"
OUTPUT_TOOL = "final_result"  # PydanticAI's internal tool for returning the report.
RESULT_PREVIEW_CHARS = 200
MAX_LEAD_TIME_DAYS = 21
MAX_MINIMUM_ORDER = 600
SAFE_VENDOR_NAME = re.compile(r"^[\w &'.,-]{1,60}$")
SKU_FORMAT = re.compile(r"^CC-[A-Z]{2}-\d{3}$")
LINK = re.compile(r"https?://|www\.|\]\(", re.IGNORECASE)
SECURITY_RULES = re.compile(r"Security rules:\n\n(?:- .*\n)+")


@dataclass
class VendorDesk:
    """The agent setup for a run. Without the design layer it has one model and no decider."""

    reader: Agent
    decider: Agent | None = None
    layers: str = "none"


def _model() -> OpenAIResponsesModel:
    load_dotenv()
    api_key = os.getenv("PORTKEY_API_KEY")
    if not api_key:
        raise SystemExit("PORTKEY_API_KEY is not set.")
    return OpenAIResponsesModel(MODEL_NAME, provider=OpenAIProvider(base_url=PORTKEY_BASE_URL, api_key=api_key))


def _read_prompt(name: str) -> str:
    return (ROOT / "prompts" / name).read_text(encoding="utf-8")


def _handbook() -> str:
    return (ROOT / "data" / "shop_handbook.md").read_text(encoding="utf-8")


def make_agent(
    use_cache: bool = True, defended: bool = True, code: bool = True, design: bool = True, prompt: bool = True
) -> VendorDesk:
    """Build the vendor desk. defended=False turns all three defense layers off.

    code, design, and prompt turn single layers on or off for testing.

    With use_cache off, nothing is read from or written to the cache. The API
    normally picks one cache point by itself. Explicit mode turns that off, and
    this agent adds no cache points of its own, so none exist.
    """
    if not defended:
        code = design = prompt = False
    settings = None if use_cache else {"openai_prompt_cache_options": {"mode": "explicit"}}
    model = _model()
    read_tool = tools.read_document if code else Tool(tools.read_document_raw, name="read_document")
    switches = (("code", code), ("design", design), ("prompt", prompt))
    layers = ",".join(name for name, on in switches if on) or "none"
    prompt_text = _read_prompt("prompt.md")

    if not design:
        security = "\n".join(SECURITY_RULES.findall(prompt_text)) if prompt else ""
        return VendorDesk(Agent(
            model,
            instructions=f"{security}\n{_read_prompt('prompt_no_defenses.md')}\n{_handbook()}",
            model_settings=settings,
            output_type=VendorReport,
            tools=[read_tool, tools.send_email, tools.approve_payment],
        ), layers=layers)

    if not prompt:
        prompt_text = SECURITY_RULES.sub("", prompt_text)
    reader_rules, decision_rules = prompt_text.split("# Decision instructions")
    reader = Agent(
        model,
        instructions=reader_rules,
        model_settings=settings,
        output_type=VendorFacts,
        tools=[read_tool],  # No email or payment tools on the model that sees documents.
    )
    decider = Agent(
        model,
        instructions=f"# Decision instructions{decision_rules}\n{_handbook()}",
        model_settings=settings,
        output_type=DecisionDraft,
        tools=[tools.send_email, tools.approve_payment],  # This model never sees a document.
    )
    return VendorDesk(reader, decider, layers)


def _normalized(name: str) -> str:
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", name.lower()).split())


@lru_cache(maxsize=1)
def handbook_rules() -> tuple[dict[str, str], dict[str, str], dict[str, float]]:
    """Read the approved list, removed list, and max unit costs from the handbook."""
    sections = re.split(r"^## ", _handbook(), flags=re.MULTILINE)
    section = {text.split(".")[0]: text for text in sections if text[:2].rstrip(".").isdigit()}
    approved = {
        _normalized(name): name.strip()
        for name in re.findall(r"^\| [A-Z]{3} \| ([^|]+) \|", section["5"], re.MULTILINE)
    }
    removed = {
        _normalized(name): name.strip()
        for name in re.findall(r"^\| ([^|]+) \| (?:Removed|Application)", section["6"], re.MULTILINE)
    }
    max_costs = {
        sku: float(cost)
        for sku, cost in re.findall(r"^\| (CC-[A-Z]{2}-\d{3}) \|[^|]+\|[^|]+\|[^|]+\| \$([\d.]+) \|", section["9"], re.MULTILINE)
    }
    return approved, removed, max_costs


def check_facts(facts: VendorFacts) -> VendorFacts:
    """Keep only plain values, so a model's output cannot carry hidden instructions onward."""
    vendor = facts.vendor.strip() if facts.vendor else None
    sku = facts.sku.strip().upper() if facts.sku else None
    price = facts.unit_price
    lead_time = facts.lead_time_days
    minimum = facts.min_order_units
    return VendorFacts(
        vendor=vendor if vendor and SAFE_VENDOR_NAME.match(vendor) else None,
        sku=sku if sku and SKU_FORMAT.match(sku) else None,
        unit_price=price if price is not None and 0 < price < 100_000 else None,
        lead_time_days=lead_time if lead_time is not None and 0 <= lead_time <= 3_650 else None,
        min_order_units=minimum if minimum is not None and 0 < minimum < 10_000_000 else None,
    )


def vendor_status(vendor: str | None) -> str:
    approved, removed, _ = handbook_rules()
    name = _normalized(vendor or "")
    if not name:
        return "unknown"
    if any(listed in name for listed in removed):
        return "removed_or_pending"
    return "approved" if name in approved else "not_on_list"


def apply_rules(facts: VendorFacts) -> tuple[str, str]:
    """The handbook's four checks in code. This, not a model, makes the final decision."""
    _, _, max_costs = handbook_rules()
    status = vendor_status(facts.vendor)
    if status != "approved":
        return "do_not_recommend", f"Approved vendor check failed: the vendor is {status.replace('_', ' ')}."
    max_cost = max_costs.get(facts.sku or "")
    if facts.unit_price is None or max_cost is None:
        return "do_not_recommend", "Price check failed: the unit price or SKU is unknown."
    if facts.unit_price > max_cost:
        return "do_not_recommend", "Price check failed: the unit price is above the item's max unit cost."
    if facts.lead_time_days is None:
        return "do_not_recommend", "Lead time check failed: the lead time is unknown."
    if facts.lead_time_days > MAX_LEAD_TIME_DAYS:
        return "do_not_recommend", f"Lead time check failed: {facts.lead_time_days} days is over the 21-day limit."
    if facts.min_order_units is None:
        return "do_not_recommend", "Minimum order check failed: the minimum order is unknown."
    if facts.min_order_units > MAX_MINIMUM_ORDER:
        return "do_not_recommend", f"Minimum order check failed: {facts.min_order_units} units is over the 600-unit limit."
    return "recommend", "All four purchasing checks passed: approved vendor, price, lead time, and minimum order."


def cost_of(usage) -> dict:
    """Price a run or one call with prices.json. input_tokens includes cache reads and writes."""
    prices = json.loads((ROOT / "data" / "prices.json").read_text(encoding="utf-8"))[MODEL_NAME]
    uncached = usage.input_tokens - usage.cache_read_tokens - usage.cache_write_tokens
    input_cost = uncached * prices["input_per_1m"] / 1_000_000
    read_cost = usage.cache_read_tokens * prices["cached_input_per_1m"] / 1_000_000
    write_cost = usage.cache_write_tokens * prices["cache_write_per_1m"] / 1_000_000
    output_cost = usage.output_tokens * prices["output_per_1m"] / 1_000_000
    return {
        "uncached_input_tokens": uncached,
        "cost_usd": round(input_cost + read_cost + write_cost + output_cost, 8),
    }


def tool_calls_in(messages: list[ModelMessage]) -> list[dict]:
    """List each tool call with its arguments and a short result."""
    calls: dict[str, dict] = {}
    for message in messages:
        for part in message.parts:
            if isinstance(part, ToolCallPart) and part.tool_name != OUTPUT_TOOL:
                calls[part.tool_call_id] = {
                    "tool": part.tool_name,
                    "arguments": part.args_as_dict(),
                    "result": None,
                }
            elif isinstance(part, ToolReturnPart) and part.tool_call_id in calls:
                calls[part.tool_call_id]["result"] = str(part.content)[:RESULT_PREVIEW_CHARS]
    return list(calls.values())


def per_request_usage(messages: list[ModelMessage]) -> list[dict]:
    """Token counts the API reported for each model call in a run."""
    return [
        {
            "response_id": message.provider_response_id,
            "input_tokens": message.usage.input_tokens,
            "cache_read_tokens": message.usage.cache_read_tokens,
            "cache_write_tokens": message.usage.cache_write_tokens,
            "output_tokens": message.usage.output_tokens,
            "reasoning_tokens": message.usage.output_reasoning_tokens,
            "details": dict(message.usage.details),
            **cost_of(message.usage),
        }
        for message in messages
        if isinstance(message, ModelResponse)
    ]


def log_usage(
    document: str, time: str, usage: RunUsage, cache_mode: str, layers: str, messages: list[ModelMessage]
) -> dict:
    entry = {
        "document": document,
        "time": time,
        "model": MODEL_NAME,
        "cache_mode": cache_mode,
        "layers": layers,
        "requests": usage.requests,
        "input_tokens": usage.input_tokens,
        "cache_read_tokens": usage.cache_read_tokens,
        "cache_write_tokens": usage.cache_write_tokens,
        "output_tokens": usage.output_tokens,
        "reasoning_tokens": usage.output_reasoning_tokens,
        **cost_of(usage),
        "per_request": per_request_usage(messages),
    }
    tools.append_json(USAGE_LOG, entry)
    return entry


def log_audit(
    document: str, time: str, cache_mode: str, messages: list[ModelMessage], final_answer, error=None, **details
) -> None:
    tools.append_json(AUDIT_TRAIL, {
        "document": document,
        "time": time,
        "cache_mode": cache_mode,
        "tool_calls": tool_calls_in(messages),
        "final_answer": final_answer,
        "error": error,
        **details,
    })


def _message_for(path: Path) -> str:
    return f"Review the vendor document at this path: {path.as_posix()}"


def _run_defended(path: Path, desk: VendorDesk):
    """Read, check, decide, then let the code rules make the final call."""
    limits = UsageLimits(request_limit=6)
    reader_run = desk.reader.run_sync(_message_for(path), usage_limits=limits)

    facts = check_facts(reader_run.output)
    decider_input = {**facts.model_dump(), "vendor": facts.vendor, "vendor_status": vendor_status(facts.vendor)}
    decider_run = desk.decider.run_sync(f"Checked facts:\n{json.dumps(decider_input)}", usage_limits=limits)

    decision, code_reason = apply_rules(facts)
    draft = decider_run.output
    keep_model_reason = draft.decision == decision and not LINK.search(draft.reason)
    report = VendorReport(
        **facts.model_dump(), decision=decision, reason=draft.reason if keep_model_reason else code_reason
    )

    usage = RunUsage()
    usage.incr(reader_run.usage)
    usage.incr(decider_run.usage)
    details = {
        "layers": desk.layers,
        "hidden_text_removed": [text[:RESULT_PREVIEW_CHARS] for text in tools.clean_document(path)[1]],
        "model_decision": draft.decision,
        "code_changed_decision": draft.decision != decision,
    }
    return report, usage, [*reader_run.all_messages(), *decider_run.all_messages()], details


def _run_undefended(path: Path, desk: VendorDesk):
    run = desk.reader.run_sync(_message_for(path), usage_limits=UsageLimits(request_limit=6))
    return run.output, run.usage, run.all_messages(), {"layers": desk.layers}


def run_and_log(path: Path, desk: VendorDesk, cache_mode: str):
    """Run one document, log it, and return the answer and its usage entry."""
    tools.ensure_trap_log()
    document = path.as_posix()
    time = datetime.now(timezone.utc).isoformat()
    tools.allowed_document = path.resolve()
    with capture_run_messages() as messages:
        try:
            run = _run_defended if desk.decider else _run_undefended
            report, usage, all_messages, details = run(path, desk)
        except Exception as error:
            log_audit(
                document, time, cache_mode, messages, None, f"{type(error).__name__}: {error}",
                layers=desk.layers,
            )
            raise

    answer = report.model_dump()
    entry = log_usage(document, time, usage, cache_mode, desk.layers, all_messages)
    log_audit(document, time, cache_mode, all_messages, answer, **details)
    return answer, entry


def main() -> None:
    parser = argparse.ArgumentParser(description="Review one vendor document.")
    parser.add_argument("--doc", required=True, help="Path to an HTML, PDF, or .eml vendor document")
    parser.add_argument("--no-cache", action="store_true", help="Stop the handbook being reused from cache")
    parser.add_argument("--no-defenses", action="store_true", help="Run the original agent with no protections")
    args = parser.parse_args()
    path = Path(args.doc)
    if not path.is_file():
        raise SystemExit(f"File not found: {path}")
    if path.suffix.lower() not in (".html", ".htm", ".pdf", ".eml"):
        raise SystemExit(f"Unsupported file type: {path.name}. Use HTML, PDF, or .eml.")

    use_cache = not args.no_cache
    desk = make_agent(use_cache, defended=not args.no_defenses)
    answer, _ = run_and_log(path, desk, "with_cache" if use_cache else "without_cache")
    print(json.dumps(answer, indent=2))


if __name__ == "__main__":
    main()
