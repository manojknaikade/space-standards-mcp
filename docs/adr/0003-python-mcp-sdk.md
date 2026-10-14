# ADR-0003: Python + official MCP SDK; agent framework decided later

Status: accepted · 2026-10-05 · agent choice settled in [ADR-0005](0005-agent-loop.md)

## Decision

- Python 3.11+, official `mcp` Python SDK v2 (`MCPServer`, formerly `FastMCP`), stdio transport.
- No agent framework in Phase 1–2. The knowledge layer stays framework-free.
- Agent framework chosen at the start of Phase 3, between:
  - **Claude Agent SDK** — strong for tool loops/subagents, tied to Claude models
  - **LangGraph** — most adopted for stateful multi-step workflows, model-agnostic
  - plain tool-calling loop against a model API — minimal, good baseline

## Reasons

- MCP is the closest thing to a stable standard in the agent ecosystem; frameworks churn.
- Building the first loop without a framework shows which problems a framework actually solves.
- Python fits the document-parsing ecosystem (python-docx, pdfplumber).
