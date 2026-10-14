# ADR-0004: Initial scope = launcher and payload-fairing structures

Status: accepted · 2026-10-05 · supersedes the software-standards scope in the kickoff brief

## Context

The kickoff scope (ECSS-E-ST-40 / Q-ST-80 vs NPR 7150.2) was chosen as a generic, well-known comparison. The project's domain expertise is hardware development for launch vehicles and payload-fairing structures. Building where the answers can be judged is worth more than a generic pairing: evaluation questions get better, wrong answers get caught, and the result is credible to aerospace users.

## Decision

Phase 1–2 cover structural and mechanical standards relevant to launcher and fairing hardware:

| Topic | ECSS | NASA |
| --- | --- | --- |
| Structural general requirements | ECSS-E-ST-32 | — |
| Factors of safety | ECSS-E-ST-32-10 | NASA-STD-5001 |
| Loads analysis | ECSS-E-HB-32-26 (handbook) | NASA-STD-5002 |
| Fracture control | ECSS-E-ST-32-01 | NASA-STD-5019 |
| Pressurised hardware | ECSS-E-ST-32-02 | — |
| FE models / modal survey | ECSS-E-ST-32-03, ECSS-E-ST-32-11 | — |
| Mechanical shock (separation, pyro) | ECSS-E-HB-32-25 (handbook) | NASA-STD-7003 |
| Vibroacoustic / payload test | ECSS-E-ST-10-03 | NASA-STD-7001, NASA-STD-7002, NASA-HDBK-7005 |
| Threaded fasteners | — | NASA-STD-5020 |

Exact current issues/revisions to be confirmed when downloading; the table is a starting list, not a commitment to all of them in v1.

v1 core (smallest set that answers the most common cross-agency questions): **ECSS-E-ST-32, ECSS-E-ST-32-10, ECSS-E-ST-32-01, NASA-STD-5001, NASA-STD-5019.**

Later candidates: ECSS-E-ST-33-01 (mechanisms, for separation systems), ECSS structural materials handbook parts (composites, sandwich), NASA-STD-6016 (materials and processes), US Space Force SMC-S-016 (test requirements for launch and space vehicles), NASA Lessons Learned on fairings and separation events.

## Consequences

- **Tables and numbers matter.** Factors of safety, test levels and margins live in tables. The parser must extract table rows as structured data with units and conditions, not flatten them into text. This moves table parsing into Phase 1.
- **Handbooks are guidance, not requirements.** Records carry a `kind` (requirement / recommendation / guidance) so answers never present handbook text as a "shall".
- **Comparison questions are the core use case** (e.g. "yield and ultimate factors for a metallic fairing, ECSS vs NASA"), so the `compare_topic` tool moves up in priority.
- The software-standards pairing is dropped from v1; the code is standard-agnostic, so it can be added later.
