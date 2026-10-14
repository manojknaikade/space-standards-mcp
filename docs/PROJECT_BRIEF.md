# Project brief

_Kickoff: 5 October 2026_

## Problem

Space projects work under ECSS (Europe) and NASA standards. Answering "what exactly does the standard require here?" means finding the right document and issue, the right clause, following its cross-references, and often mapping it to the other agency's equivalent. This is slow, and general-purpose AI assistants are unreliable at it: they paraphrase, invent clause numbers and mix up issues.

> Scope updated the same day to launcher and payload-fairing structures — see [ADR-0004](adr/0004-scope-launcher-structures.md).

## Goal

A tool that answers questions about ECSS and NASA standards with exact, verifiable, requirement-level citations — and says "not covered" when the sources don't support an answer.

## Users

- Structural and mechanical engineers on launch vehicles, upper stages and payload fairings
- Stress, loads and test engineers checking factors of safety, fracture control and qualification requirements
- Suppliers working to both ECSS and NASA (e.g. European hardware on US launchers or vice versa)
- Reviewers checking compliance and tailoring at design reviews

The evaluation set is written from launcher and fairing structures practice, which keeps the questions realistic and lets wrong answers be caught.

## Landscape (checked 5 Oct 2026)

Nothing found that combines ECSS and NASA with requirement-level, cited answers. Closest pieces, all early-stage:

| Project | What it does | Gap |
| --- | --- | --- |
| [aerospace-mcp-tools/ecss-mcp-server](https://github.com/aerospace-mcp-tools/ecss-mcp-server) | MCP server: list ECSS docs, summary/TOC, section text. User supplies .docx. Apache-2.0. Anonymous maintainer, not official. | ECSS only; section-level, not requirement-level; no NASA; no cross-standard mapping; no evaluation |
| [souzou-office/nasa-engineering-mcp](https://github.com/souzou-office/nasa-engineering-mcp) | NPR 7150.2D ch. 3–5 as 168 structured rules for coding agents | Narrow; rules enforcement, not Q&A |
| aero-agent-skills, systems-engineering-skills (GitHub topic `ecss`) | Prompt/skill packs for SE tasks | Not knowledge bases |
| [ginevracianci/ecss-mbse-framework](https://github.com/ginevracianci/ecss-mbse-framework) | ECSS + MBSE templates | Not Q&A |

Commercial requirements tools may have AI features not visible on GitHub — to be checked.

**Positioning:** don't rebuild what exists. Reuse ideas (and possibly code, Apache-2.0) from ecss-mcp-server for docx handling; differentiate on NASA coverage, requirement-level records, versions, cross-standard comparison and a published evaluation set.

## Key decisions

- [ADR-0001](adr/0001-mcp-server-first.md) — Build the MCP server first, thin agent second
- [ADR-0002](adr/0002-bring-your-own-documents.md) — Bring your own documents; no standards text in the repo
- [ADR-0003](adr/0003-python-mcp-sdk.md) — Python + official MCP SDK; framework-agnostic agent layer
- [ADR-0004](adr/0004-scope-launcher-structures.md) — Initial scope: launcher and payload-fairing structures
- [ADR-0005](adr/0005-agent-loop.md) — Phase 3 agent: plain tool-calling loop with a citation gate
- [ADR-0006](adr/0006-full-corpus-parse-tiers.md) — Full corpus: catalogue everything, load in waves, parse tiers

## Scope

**In (v1):** ECSS-E-ST-32, ECSS-E-ST-32-10, ECSS-E-ST-32-01, NASA-STD-5001, NASA-STD-5019; lookup by ID, keyword search, cross-references, structured tables (factors of safety); ECSS↔NASA comparison on factors of safety and fracture control; evaluation set of 50–100 questions written from launcher and fairing structures practice.

**Later:** loads analysis, mechanical shock, vibroacoustic and payload testing, fasteners, mechanisms, materials; NASA Lessons Learned; semantic search; agent with citation verification; tailoring support. Software standards (ECSS-E-ST-40, Q-ST-80, NPR 7150.2) remain possible since the code is standard-agnostic.

**Out:** hosting or redistributing standards text; compliance sign-off; export-controlled material.

## Risks

| Risk | Mitigation |
| --- | --- |
| Wrong or invented clause in an answer | Tools return verbatim records; agent must cite IDs that exist; citation checker rejects unknown IDs; eval set includes "not covered" questions |
| Parsing breaks clause structure (tables, notes, nested lists) | Requirement-level parser with tests per document; report unparsed fragments |
| Mixing issues/revisions | Issue is part of every record and every citation |
| Wrong number from a table (factor, test level, unit, condition) | Tables parsed into structured rows with units and conditions; numeric answers must quote the table row; dedicated numeric eval questions |
| Handbook guidance presented as a requirement | Records carry `kind` (requirement / recommendation / guidance); answers state which |
| ECSS licensing / redistribution | BYOD design, local-only processing; read ECSS terms before any public or commercial release |
| Export-controlled NASA content | Only ingest documents marked for public release |
| Framework churn | Concepts over frameworks; MCP as the stable interface |

## Success criteria (v1)

- ≥ 95 % of lookup-by-ID tests return the exact requirement text
- ≥ 85 % correct, fully-cited answers on the evaluation set
- 100 % of "not covered" eval questions answered as not covered (no fabricated citations)
- 100 % of numeric answers (factors of safety, test levels) match the source table row, including units and conditions
- Usable from at least one off-the-shelf MCP client
