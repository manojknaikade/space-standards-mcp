# ADR-0002: Bring your own documents

Status: accepted · 2026-10-05

## Context

ECSS standards are free to download after registration on ecss.nl, but redistribution terms must be respected. Most NASA standards are publicly available; some NASA material is export-controlled.

## Decision

- No standards text is committed to this repository. `documents/` is gitignored.
- Users download documents from official sources; the server parses them locally.
- Tests use an invented demo standard (`tests/fixtures/`), never real standards text.
- Evaluation questions reference requirement IDs and paraphrased expectations, not verbatim text.
- Only NASA documents marked for public release are ingested.

## Before any public or commercial release

- Read the current ECSS terms of use on ecss.nl.
- Re-check NASA distribution statements for every ingested document.
