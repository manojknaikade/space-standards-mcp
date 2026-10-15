"""Thin agent: a plain tool-calling loop with a citation gate (ADR-0005).

The loop is the one the answer eval uses (`eval/run_answer_eval.py --backend api` runs it with the gate off,
`--backend agent` with it on), so a comparison measures the gate and nothing else. The model sees the MCP
server's own tool definitions and calls `spacestd.tools` in-process.

Gate: each draft answer goes through `spacestd.citations.CitationChecker`, grounded in the records the loop
retrieved. Invented IDs or ungrounded numbers go back to the model for one revision; if the revision still
fails, the agent declines ("not covered") and says what it found. Exception: when the revision's only problem
is table numbers from below the verified tier without the flag (all of them in retrieved tables), the agent
returns the revision with status `flagged` and one appended line naming each such number with its document,
table and page.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from functools import lru_cache

from spacestd import tools
from spacestd.citations import CitationChecker, norm_key
from spacestd.index import StandardsIndex

MODEL = "claude-opus-5-5"
FALLBACK_BETA = "server-side-fallback-2026-07-01"
ANSWER_SYSTEM = (
    "You answer questions from launcher and payload-fairing structures engineers using the space-standards "
    "tools, which hold the loaded ECSS and NASA standards. Search before answering. Every search call carries "
    "search words; after an empty or unhelpful result, retry with different words or a named document instead "
    "of declining. Cite every requirement and "
    "table you use with the 'citation' field the tools return (document, issue, requirement or table ID). "
    "Only cite what the tools returned; never cite from memory. Take numbers only from tool results, with "
    "their conditions. Tables and rows from documents below the `verified` tier carry a `check` flag and a "
    "`page`: give every number taken from them with that flag, in the same sentence, as \"check against the "
    "source, page N\". State the record kind when it is not a requirement (table: a table with no owning record, cite the table). If the tools do not support an "
    "answer, say the loaded standards do not cover it, and do not give values from memory."
)
REVISE_PROMPT = (
    "An automatic check of your answer against the loaded standards found problems:\n{problems}\n\n"
    "Revise the answer: look up any record before citing it, drop or correct IDs that do not exist, and state "
    "only numbers printed in the records and tables you retrieved. A flagged number that is a clause or table "
    "reference, not a value, can stay: write it as 'clause 4.5' or 'Table 4-3'. If the tools do not support an "
    "answer, say the loaded standards do not cover it. Give the full revised answer."
)


@lru_cache(maxsize=1)
def tool_definitions() -> tuple[dict, ...]:
    """The MCP server's tools as Messages API tool definitions (same names, descriptions and schemas)."""
    from spacestd import server

    return tuple({"name": t.name, "description": t.description or "", "input_schema": t.input_schema}
                 for t in asyncio.run(server.mcp.list_tools()))


def run_tool(index: StandardsIndex, name: str, args: dict):
    if name not in {t["name"] for t in tool_definitions()}:
        raise ValueError(f"unknown tool {name}")
    return getattr(tools, name)(index, **args)


def gate_problems(check, retrieved: list[str]) -> list[str]:
    """What the gate rejects: IDs that exist in no loaded document, and numbers found in no record the
    answer cites or the loop retrieved."""
    out = []
    if check.invented:
        out.append("- IDs that exist in no loaded document: " + ", ".join(check.invented))
    if check.ungrounded:
        lost = [n for n in check.ungrounded if n not in check.unflagged]
        if lost:
            out.append("- numbers not found in any retrieved record or table: " + ", ".join(lost))
        if check.unflagged:
            out.append("- numbers from tables below the verified tier without the flag: " + ", ".join(check.unflagged)
                       + " (repeat \"check against the source, page N\" in the same sentence)")
    return out


def only_unflagged(check) -> bool:
    """The only gate findings are table numbers from below the verified tier without the flag: no invented
    IDs, and every ungrounded number sits in a retrieved table."""
    return bool(check.unflagged) and not check.invented and set(check.ungrounded) == set(check.unflagged)


def flag_note(check) -> str:
    """One deterministic line naming each unflagged number with its document, table and page."""
    items = [f"{n} ({'; '.join(check.unflagged_sources.get(n, [])) or 'table below the verified tier'})"
             for n in check.unflagged]
    verb = "comes" if len(items) == 1 else "come"
    noun = "a table" if len(items) == 1 else "tables"
    return f"Check against the source: {', '.join(items)} {verb} from {noun} below the verified tier."


@dataclass
class AgentResult:
    question: str
    answer: str
    status: str  # passed | revised | flagged | declined (gate) | ungated | error
    draft: str = ""  # first answer, when the gate changed it
    check: dict = field(default_factory=dict)  # CitationChecker result for the returned answer
    problems: list[str] = field(default_factory=list)  # gate findings on the first draft
    revision: str = ""  # the revised draft, when the gate declined it
    revision_problems: list[str] = field(default_factory=list)  # gate findings on that revision
    unretrieved: list[str] = field(default_factory=list)  # cited records no tool returned (not gated; for review)
    tool_calls: list[dict] = field(default_factory=list)
    retrieved: list[str] = field(default_factory=list)
    error: str = ""

    def to_record(self) -> dict:
        """Answer-eval record (eval/run_answer_eval.py answers.jsonl)."""
        rec = {"answer": self.answer, "tool_calls": self.tool_calls, "retrieved": self.retrieved}
        if self.status != "ungated":
            rec["gate"] = {"status": self.status, "problems": self.problems, "unretrieved": self.unretrieved,
                           **({"draft": self.draft} if self.draft else {}),
                           **({"revision": self.revision, "revision_problems": self.revision_problems}
                              if self.revision else {})}
        if self.error:
            rec["error"] = self.error
        return rec


class StandardsAgent:
    def __init__(self, index: StandardsIndex, client=None, model: str = MODEL, gate: bool = True,
                 effort: str | None = None, max_turns: int = 12, max_tokens: int = 16000):
        if client is None:
            import anthropic  # optional dependency: pip install -e ".[agent]"

            client = anthropic.Anthropic()
        self.index, self.client, self.model, self.gate = index, client, model, gate
        self.effort, self.max_turns, self.max_tokens = effort, max_turns, max_tokens
        self.checker = CitationChecker(index)

    def _create(self, messages: list):
        extra = {"output_config": {"effort": self.effort}} if self.effort else {}
        return self.client.beta.messages.create(
            model=self.model, max_tokens=self.max_tokens, system=ANSWER_SYSTEM, tools=list(tool_definitions()),
            messages=messages, cache_control={"type": "ephemeral"}, betas=[FALLBACK_BETA], fallbacks="default",
            **extra)

    def _loop(self, messages: list, calls: list, retrieved: list) -> tuple[str, str]:
        """Run tool calls until the model answers. Returns (answer text, error)."""
        for _ in range(self.max_turns):
            msg = self._create(messages)
            if msg.stop_reason == "refusal":
                return "", "refusal"
            messages.append({"role": "assistant", "content": msg.content})
            uses = [b for b in msg.content if b.type == "tool_use"]
            if not uses:
                return "".join(b.text for b in msg.content if b.type == "text").strip(), ""
            results = []
            for u in uses:
                try:
                    out = run_tool(self.index, u.name, dict(u.input))
                except Exception as e:  # report tool errors to the model, as an MCP client would
                    out = {"error": f"{type(e).__name__}: {e}"}
                calls.append({"name": u.name, "input": dict(u.input)})
                retrieved += tools.record_keys(out)
                results.append({"type": "tool_result", "tool_use_id": u.id, "content": json.dumps(out)})
            messages.append({"role": "user", "content": results})
        return "", "max_turns"

    def ask(self, question: str) -> AgentResult:
        messages: list = [{"role": "user", "content": question}]
        calls: list[dict] = []
        retrieved: list[str] = []

        def result(answer, status, **kw):
            return AgentResult(question, answer, status, tool_calls=calls, retrieved=list(dict.fromkeys(retrieved)),
                               **kw)

        draft, error = self._loop(messages, calls, retrieved)
        if error:
            return result("", "error", error=error)
        if not self.gate:
            return result(draft, "ungated")

        def check(answer):
            chk = self.checker.check(answer, question, list(dict.fromkeys(retrieved)))
            got = {norm_key(k) for k in retrieved}
            unretrieved = sorted(k for k in chk.cited_keys if norm_key(k) not in got)
            return chk, gate_problems(chk, retrieved), unretrieved

        chk, problems, unretrieved = check(draft)
        if not problems:
            return result(draft, "passed", check=chk.to_dict(), unretrieved=unretrieved)

        messages.append({"role": "user", "content": REVISE_PROMPT.format(problems="\n".join(problems))})
        revised, error = self._loop(messages, calls, retrieved)
        if error:
            return result("", "error", draft=draft, problems=problems, error=error)
        chk2, problems2, unretrieved2 = check(revised)
        if not problems2:
            return result(revised, "revised", draft=draft, check=chk2.to_dict(), problems=problems,
                          unretrieved=unretrieved2)

        if only_unflagged(chk2):
            # all numbers are in retrieved tables; only the flag is missing: add it instead of declining
            flagged_answer = revised.rstrip() + "\n\n" + flag_note(chk2)
            chk3, problems3, unretrieved3 = check(flagged_answer)
            if not problems3:
                return result(flagged_answer, "flagged", draft=draft, check=chk3.to_dict(), problems=problems,
                              revision_problems=problems2, unretrieved=unretrieved3)

        found = sorted({k for k in chk2.cited_keys} | {k for k in chk.cited_keys})
        # the decline repeats no invented ID or ungrounded number; the findings stay in the gate record
        decline = ("Not covered: no verified answer could be given from the loaded standards (the draft cited "
                   "IDs that do not exist or numbers not found in the retrieved records, twice)."
                   + (("\nRecords it relied on (check them directly): " + "; ".join(k.replace("|", ", ") for k in found))
                      if found else ""))
        return result(decline, "declined", draft=draft, check=self.checker.check(decline, question).to_dict(),
                      problems=problems, unretrieved=unretrieved2, revision=revised, revision_problems=problems2)
