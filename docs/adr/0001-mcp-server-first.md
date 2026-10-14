# ADR-0001: MCP server first, thin agent second

Status: accepted · 2026-10-05

## Context

Two options: build an end-to-end agent (chat app) or an MCP server exposing the standards as tools.

## Decision

Build the MCP server first. Add a thin agent on top in Phase 3 for what tools alone can't do.

## Reasons

- The value is in the knowledge layer: requirement-level parsing, versions, cross-references, exact citations. That part is reusable; the chat layer is not.
- Any MCP client (Claude, VS Code Copilot, Cursor) can use the server immediately — no UI to build before getting feedback.
- Tools like `get_requirement(doc, id)` are deterministic and testable without an LLM.
- Local server + user-supplied documents avoids redistributing standards text (ADR-0002).

## The agent will add

- multi-step questions and ECSS↔NASA comparisons
- citation verification against the index and "not covered" refusals
- end-to-end evaluation of the whole system
