# ADR-0005: Phase 3 agent = plain tool-calling loop with a citation gate

Status: accepted · 2026-10-08 · settles the open choice in [ADR-0003](0003-python-mcp-sdk.md)

## Context

ADR-0003 left the agent framework open until after Phase 2: Claude Agent SDK, LangGraph, or a plain loop.
Phase 2 ([eval/RESULTS.md](../../eval/RESULTS.md)) found:

- An off-the-shelf client using only the MCP tools answers 53/57 correctly, with about 2 tool calls per question.
  The 4 partials are retrieval misses. Multi-step orchestration is not what is missing.
- What is missing is a guarantee. Today, citing only real IDs and taking numbers from tables is a prompt
  instruction. The deterministic checks in `src/spacestd/citations.py` already detect a violation, but only
  after the run, during the eval.
- `eval/run_answer_eval.py` (`ApiBackend`) already contains a working plain tool-calling loop of about 30 lines.

## Decision

- Build the agent as a **plain tool-calling loop** against the Anthropic Messages API. It is a new package
  (`src/spacestd_agent/`, or `agent/`) that depends on `spacestd`, never the other way round.
- Add a **citation gate** after each draft answer: run the `citations.py` checks against the records the loop
  retrieved. When an ID is invented or a number is ungrounded, send the findings back for one revision; if
  the revision still fails, return "not covered" with what was found. The gate is the agent's reason to exist.
- `compare_topic` stays a knowledge-layer tool, not an agent workflow.
- Revisit the decision if Phase 3 needs subagents (per-standard researchers for comparisons) or durable
  multi-turn state. The Claude Agent SDK is the first candidate then; LangGraph only if non-Claude models are needed.

## Reasons

- The data shows the agent needs a gate, not a planner. A framework adds churn and dependencies without fixing
  the failure that matters.
- Reusing the eval's loop keeps the agent and the eval backend identical, so the Phase 3 comparison measures
  the gate and not differences between frameworks.
- This follows ADR-0003's reasoning: build the first loop without a framework to see which problems a framework
  would actually solve.

## Addendum — 8 October 2026

No API key was available for the Phase 3 comparison, so the gate was also put around Claude Code (`claude -p`
with the MCP tools; the revision resumes the session) as `ClaudeCodeAgent` (`src/spacestd_agent/claude_code.py`).
The gate is unchanged. Only the loop differs, so `cli-agent` against `cli` measures the gate in the same way as
`agent` against `api`.
