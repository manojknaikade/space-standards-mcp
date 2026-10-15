# Roadmap

Rough pace: evenings/weekends alongside a full-time job. Each phase ends with something usable.
Scope: launcher and payload-fairing structures ([ADR-0004](adr/0004-scope-launcher-structures.md)), then every ECSS and
NASA standard in waves ([ADR-0006](adr/0006-full-corpus-parse-tiers.md)).

## Phase 1 — Knowledge layer (MCP server) · weeks 1–5

- [x] Data model: `Document`, `Requirement` (doc ID, issue, requirement ID, clause path, text, notes, references)
- [x] Generic clause parser (numbered clauses, lettered requirements, NOTEs, NASA-style `[ABC-n]` tags, cross-references)
- [x] In-memory index with lookup by ID and keyword search
- [x] MCP tools: `list_documents`, `get_requirement`, `search_requirements`, `get_references`
- [x] Synthetic demo standards (software + structures) + unit tests + CI
- [x] Download v1 core into `documents/` — all in: ECSS-E-ST-32 Rev.1, 32-01 Rev.2 (docx + PDF), 32-10 Rev.2, 32-08 Rev.1 (extra), NASA-STD-5001B, NASA-STD-5019A; ECSS PDFs preferred (see PARSING_NOTES)
- [x] Real-document parser fixes from [PARSING_NOTES.md](PARSING_NOTES.md): tracked changes, auto-numbering, per-clause letters, PDF loader
- [x] Confirm each document's requirement-ID convention (ECSS clause + letter, DRD `A.2.1<5.2>a`; NASA `FSR n`, `FCR n`, FCR items `FCR 11 / 7.2.1.c`) and adjust parser
- [x] **Tables as structured data**: rows with columns, footnotes and merged-cell flags (32-10 Tables 4-1 to 4-6, 5001B Tables 1–7, hand-checked); `get_table` tool
- [x] `kind` field: requirement / recommendation / permission / guidance / deleted
- [x] PDF loader (ECSS and NASA); Word path kept for ECSS-E-ST-32-08C
- [x] Per-document parsing tests (requirement counts, spot checks on known clauses; skipped in CI without documents)
- [x] Search fixes from eval run 1: document filter from the question, BM25 length normalisation, index table rows (`tests/test_search.py`)
- [x] Re-run the retrieval eval on the real documents after the search fixes (run 2 in `eval/RESULTS.md`: recall@5 0.67, recall@20 0.93)
- [x] Connect to Claude / VS Code and try 20 real questions by hand (`eval/HAND_TEST.md`: 14 correct, 2 partial, 4 correctly "not covered"; findings F1–F7)

## Phase 2 — Evaluation · weeks 5–7 · closed 8 Oct 2026 (summary in [eval/RESULTS.md](../eval/RESULTS.md))

- [x] First 20 questions drafted from ECSS-E-ST-32-01C, ECSS-E-ST-32-08C and NASA-STD-5001B, IDs and numbers checked against source (`eval/questions.yaml`, review sheet `eval/REVIEW.md`)
- [x] Domain review of the 21 questions (domain owner, 7 Oct 2026: all ok)
- [x] Grow to 50–100 questions (57: 17 numeric, 17 lookup, 7 classification, 5 compare, 11 not covered; review of the 16 v2 additions waived by the domain owner, 8 Oct 2026), covering:
  - lookup ("what does ECSS-E-ST-32-10 require for …")
  - numeric (yield/ultimate/test factors, with conditions)
  - classification (fracture-critical, fail-safe, safe-life, low-risk parts)
  - ECSS vs NASA comparison
  - ≥ 10 "not covered"
- [x] Retrieval eval: does the right requirement appear in top-k? Tables too (`expected_tables`: row hit / reachable)
- [x] Answer eval: correct + cited + numbers match source + no invented IDs (`eval/run_answer_eval.py`: deterministic checks in `src/spacestd/citations.py` + LLM judge)
- [x] Baseline retrieval numbers in `eval/RESULTS.md` (run 1: recall@5 0.44; run 7: 0.64 on 46 questions)
- [x] Answer-level baseline: recorded in `eval/RESULTS.md` (in-session Claude Code + MCP tools, self-judged; 53/4/0 correct/partial/wrong). Accepted as the Phase 2 answer baseline

## Phase 3 — Agent · weeks 7–10

Carried over from Phase 2:

- [x] Agent design decided: [ADR-0005](adr/0005-agent-loop.md) accepted (plain tool-calling loop + citation gate)

- [x] Hybrid search (BM25 + embeddings, RRF) and cross-encoder reranking, opt-in (`".[embed]"`, `SPACESTD_EMBED` /
  `SPACESTD_RERANK`, `run_retrieval_eval.py --embed/--rerank`); coverage stays on BM25 scores
- [x] Measure hybrid / rerank on the real documents (run 8 in `eval/RESULTS.md`): hybrid at dense weight 2 (now the
  weight default) lifts recall@5 0.64 → 0.69 and table row hits 0.50 → 0.75, but fs-007 (v1) drops out of the top 5,
  so hybrid stays opt-in; the reranker lowers recall@5 and is not recommended
- [x] `compare_topic` tool: one topic searched per standard, grouped ECSS / NASA, `coverage: ok|weak|none` per standard
- [x] Thin agent (`src/spacestd_agent`, `python -m spacestd_agent`): the eval's loop + citation gate (ADR-0005): one
  revision on invented IDs or ungrounded numbers, then decline; `run_answer_eval.py --backend agent`
- [x] First scripted agent run on the real documents, independent judge: `--backend cli-agent` against `cli` ("Scripted
  answer run 2" in `eval/RESULTS.md`); the API-loop pair (`agent` vs `api`) is left for when an API key is available
- [x] Scripted off-the-shelf client run (`--backend cli`, Sonnet 5.5, Opus 5.5 judge; "Scripted answer run 1" in
  `eval/RESULTS.md`): BM25 52/4/1, hybrid 49/8/0, no invented IDs or ungrounded numbers after hand review
  (one hybrid slip); checker false positives fixed (NASA clause aliases, contractions in declines)
- [x] Re-run eval with the agent; compare against the off-the-shelf client above: gated 49/7/1 against plain 52/4/1
  (the difference is sampling: the gate revised 4 answers, all correct); 0 invented IDs, 11/11 declines

## Phase 4 — Breadth & polish · weeks 10+

- [x] `get_section_outline` tool: a document's heading tree with record counts by kind; for one clause, its record IDs
  and tables (no text), so a client can browse a section instead of guessing search terms
- [x] Neighbouring records with each search hit (same clause, ±1): recall@5 0.64 → 0.74 with no losses; fs-027
  mostly fixed (run 9 in `eval/RESULTS.md`). fs-016 is a ranking problem (long record, "reduced" only in its heading)
- [x] Answer run with neighbours (`--backend cli`), to see whether the retrieval gain reaches the answers (B8, 10 Oct: 0.85 correct over 68 with wave 1)
- [ ] API-loop answer pair (`--backend agent` vs `--backend api`), when `ANTHROPIC_API_KEY` is available

Full corpus ([ADR-0006](adr/0006-full-corpus-parse-tiers.md)): every ECSS and NASA standard and handbook,
catalogued at once, loaded in waves gated by the eval, with a parse tier on each document.

- [x] ADR-0006 accepted: catalogue everything, load in waves, parse tiers (verified / checked / unchecked)
- [x] Catalogue (`python -m spacestd.catalogue documents`): recursive discovery, one source per doc_id (top-level
  copy, then PDF over Word), parts / volumes / NASA annexes as separate documents, NASA download manifest for
  titles and dotless file names; 285 documents (199 ECSS, 85 NASA, 1 superseded), loaded set unchanged
- [x] `documents/corpus.yaml` selects what is loaded; `list_documents` filters by family, type, discipline and
  title, and `include_not_loaded` lists catalogued documents that are not loaded
- [x] Parse health report over all documents (record count, valid-ID share, orphan text, ragged tables, cover vs
  file-name ID) -> `checked` tier (`python -m spacestd.health`, A1; run on all 284 documents 9 Oct, A2: 7 verified, 129 checked, 148 unchecked;
  fixes for the patterns found are A2a, H1–H5 done; re-run after H2–H4: 7 / 146 / 131)
- [x] Parse tier and page on every record and table row; unverified table numbers flagged; citation gate aware (A3, 10 Oct)
- [x] Doc-ID pattern in `index.py` / `citations.py` learns part and volume suffixes (`… Part 1A`, `… Vol 1`) (A4, 9 Oct)
- [x] Wave 1 — structures, mechanisms, testing: ECSS-E-ST-32-02/-03/-11, E-ST-33-01, E-ST-10-03,
  E-HB-32-20…26 (loads -26, shock -25), NASA-STD-5002/5020/7001/7002/7003, NASA-HDBK-7005; ~10 new eval
  questions; no regression on the existing ones. Moved to ECSS-E-ST-32-10C Rev.2 Corr.1 (B4a, 9 Oct); patterns in
  `documents/corpus.yaml` and wave-1 health report done (B1, 9 Oct); parser fixes H6 (coverage, ECSS unparsed
  text, NASA body start) and H7 (body-size headings) done (B2, 9 Oct); health re-run with A5 and tuned
  thresholds: 44 documents, 7 verified, 32 checked, 5 unchecked (10 Oct); round 3: parser fixes H8–H17, 15 verified,
  27 checked, 2 unchecked; retrieval run 10 shows no regression (B6), answers B8; round 4 (11–12 Oct): table fixes H16/H17,
  23 verified, retrieval run 11 unchanged, gated answers 0.82 correct with no wrong declines; round 5 (12 Oct):
  H18/H19 table fixes, every wave-1 standard verified (26 in all), ownerless tables searchable, run 12 table
  recall 0.37 → 0.46 @5 with record recall unchanged, gated answers 0.85 correct
- [x] Handbooks: section-level records (no lettered requirements), ranked below standards (A5, 10 Oct)
- [ ] Two-stage retrieval (pick documents, then records) once a wave shows dilution (wave 1 does not: run 10, B7)
- [ ] Wave 2 — rest of ECSS-E and NASA engineering (B1 15 Oct: 167 documents load, 41 unchecked, no retrieval
  regression; parser fixes and questions next); wave 3 — ECSS-Q, NASA 87xx; wave 4 — ECSS-M/-U/-S, remaining handbooks
- [ ] NASA Lessons Learned on fairings, separation events and structural failures (public LLIS records)
- [ ] Issue/version diffing, tailoring support (load a project tailoring matrix)
- [x] Decide: open-source the code under Apache-2.0, bring your own documents, fresh squashed public repository
  (owner, 9 Oct 2026; [ADR-0007](adr/0007-open-source-apache-byod.md), release plan C1a)

## Phase 5 — Public release

Step-by-step checklist, with each step marked worker / orchestrator / your decision (ADR-0008, all local): [PUBLIC_RELEASE_PLAN.md](PUBLIC_RELEASE_PLAN.md).
Release gate: stage A (health report, parse tiers), wave 1 loaded and evaluated, licence and text audit clean.
Waves 2–4 can follow after going public.

- [x] Public repository live: `space-standards-mcp` v0.2.1, branch protection and security features on (15 Oct 2026, release plan D2)
- [x] v0.2.2 released (15 Oct 2026): required tool arguments, PyPI workflow and MCP registry `server.json` prepared
- [ ] On PyPI and in the MCP registry; announcement posted (D3, owner)
