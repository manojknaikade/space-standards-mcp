# Plan to public release

Step-by-step checklist from today (catalogue done, 7 documents loaded) to a public repository. Everything runs
locally (ADR-0008): an Opus orchestrator session plans each round and dispatches parallel Sonnet workers for the
well-defined steps. Progress is logged in the round log `docs/PROGRESS.md` (private development repository only; on
`scripts/release_exclude.txt`); the orchestrator prompt is in
[SESSION_PROMPTS.md](SESSION_PROMPTS.md).

## Decisions taken (owner, 9 Oct 2026)

- **Licence: Apache-2.0** for the code (C1). Standards stay bring-your-own.
- **Switch ECSS-E-ST-32-10C to Rev.2 Corr.1** (B4), the issue in the October 2025 ECSS bundle.
- **Publish a fresh repository from one squashed commit** (C5). The current private repository keeps the full
  history and stays private. Force-pushing a squashed `main` into this repository is not enough: GitHub keeps
  every merged PR's commits reachable (`refs/pull/*`), so the old history would become public with it.
- **Go public at D2**, after the release gate passes.
- **10 Oct: all work local** (ADR-0008): Opus orchestrator + parallel Sonnet 5.5 workers (medium effort); no
  cloud sessions. Steps re-marked 🤖 / 🧠 / 👤 / 📄.
- **14 Oct: development stays on `space-standards-mcp-dev`** (private, full history, round log). The public
  `space-standards-mcp` only receives release commits, rebuilt from -dev's `main` (see "Release flow" under
  Stage D). Locally `origin` is -dev and `public` is the public repository.
- **11 Oct: B8 review decisions** (applied in round 4):
  - fs-024: widen the reference. ECSS-E-ST-32-10C Table 4-3 has glass and ceramic rows, so it becomes an expected
    table and the ECSS answer point names its factors next to ECSS-E-ST-32C's probabilistic allowables.
  - fs-033: make it a covered question (expected table ECSS-E-HB-32-26A Table 9-1, checked on the PDF first): no
    generic launcher-independent level; the handbook's Ariane 5 example as guidance. 4 not-covered questions remain.
  - `docs/PROGRESS.md` does not ship in the public tree; it stays in the private `-dev` repository (C10, D1a).

## Who does each step

| Mark | Who | What |
| --- | --- | --- |
| 🤖 | **Worker**: `step-worker` subagent, Sonnet 5.5, medium effort, own worktree | Well-defined steps: a spec, tests on invented fixtures or a scripted run with a clear acceptance check. Several run in parallel. |
| 🧠 | **Orchestrator**: the main Opus 5.5 session | Planning, review and merge of worker PRs, judgement-heavy work: debugging layouts on the real PDFs, triaging audit hits and eval failures, release mechanics |
| 👤 | **You decide** | Licence, history, visibility, domain judgement |
| 📄 | (added to one of the above) | Reads the real standards in `documents/`. Only one 📄 run parses at a time (shared parse cache and CPU). |

**The hard boundary:** the standards never leave the local machine (ADR-0002). Do not upload them to a bucket,
a gist or any remote service, not even temporarily. ECSS documents are licensed to the registered user. Commits
stay text-free (counts, IDs, scores, page numbers, never sentences from a standard); the orchestrator checks
every worker diff for this before merging.

**Rounds:** the orchestrator picks every ready step, runs the 🤖 ones in parallel, does the 🧠 ones itself, merges
each PR after CI passes, then closes the round with one tracking PR (checkboxes here and in the ROADMAP, one
round-log entry where `docs/PROGRESS.md` is present). Workers never edit the tracking files, so parallel PRs do not conflict.

Setup (also true in CI): `pip install -e ".[dev]" && pytest -q`. The tests that need real documents or
LibreOffice skip themselves when those are missing (CI, fresh worktrees without the `documents/` link).

---

## Stage A: groundwork for the full corpus

- [x] **A1 🤖 Parse health report code.** `python -m spacestd.health documents [--corpus all]` parses each
  catalogued document and records: record count by kind, share of records with a valid ID for its family,
  unparsed fragments, tables and tables with ragged rows, cover ID vs file-name ID, parse time, errors.
  Writes `eval/CORPUS_HEALTH.md` (counts and IDs only) plus a JSON next to the parse cache. Thresholds give
  `checked` / `unchecked`. Add tests with invented fixtures, including a deliberately broken one.
- [x] **A2 🤖📄 Run the health report on all 285 documents.** Long run: about 0.7 GB of PDFs, so start it in the
  background. Needs LibreOffice for the Word-only files. Commit `eval/CORPUS_HEALTH.md`.
  *Done 9 Oct: 284 active documents, 33 min, 0 errors; 7 verified, 129 checked, 148 unchecked. Patterns H1–H4
  in `docs/PARSING_NOTES.md`. Re-run 9 Oct after the H2–H4 fixes: 7 verified, 146 checked, 131 unchecked
  (17 NASA standards up); new pattern H5 (7001C tags after a dotted number).*
- [x] **A3 🤖 Tier and page on every record and table row** in tool results. Values from tables below
  `verified` carry a flag ("check against the source, page N"). The citation gate counts flagged numbers as
  grounded only when the answer repeats the flag. Server instructions and the agent prompt say so. Tests on fixtures.
  *Done 10 Oct (round 1): one tier rule (`StandardsIndex.tier_of`, by doc ID and issue); `tools.annotate` puts
  `tier` on every record, table and row and `check` + `page` on tables and rows below `verified`; the gate puts
  table-only numbers without the flag or the page in the same sentence into `ungrounded` and `unflagged`; page
  references are not answer numbers. `tests/test_tier_flags.py`.*
- [x] **A4 🤖 Doc-ID pattern for parts, volumes and annexes** in `index.py` / `citations.py`
  (`ECSS-E-HB-32-20 Part 1A`, `NASA-HDBK-5010 Vol 1`, `NASA-STD-8719.24 Annex`): query detection, `not_loaded`,
  the invented-ID check. Invented fixtures.
  *Done 9 Oct (cloud): one `doc_pattern` for search and citation gate (`Part1A`, `Part 1`, `Volume 1`,
  `Vol. 1`; the bare number names all loaded parts unless it is a loaded document itself); unloaded parts,
  volumes, annexes and dotted / five-digit NASA numbers reach `not_loaded`; their IDs are external, not
  invented. `tests/test_part_ids.py`.*
- [x] **A2a 🤖 Health-report fixes from A2** (`docs/PARSING_NOTES.md` H1–H4), each with invented fixtures:
  ECSS level-4 headings without a number in the text layer (H1, 32 documents with duplicate IDs), NASA lead tags
  after a dotted paragraph number (H5, 7001C), NASA tagless
  lettered requirements and `[V2 nnnn]` tags (H2, 47 documents), the file-name check's false positives (H3, 27),
  thresholds and adoption notices (H4). Then re-run A2 📄.
  *H3 and H4 done 9 Oct (cloud): base-number name check; 20 records for standards, ragged ≤ 10 % or ≤ 1,
  adoption notices listed, not judged. H2 done 9 Oct (cloud): `[V2 nnnn]` tags; tagless NASA bodies give
  `4.2a` / `4.3(1)` / `4.4 req N` records. H5 done 9 Oct (cloud): lead tags after a dotted paragraph
  number (`4.4.1.1. [TAG n]`). H1 done 9 Oct (cloud): unnumbered level-4 headings before an `a.` list get
  the next free clause number, flagged `inferred clause number`. A2 📄 re-run next.*
- [x] **A5 🤖 Handbook-style fixtures and records.** Invented handbook text (numbered sections, no lettered
  requirements, long paragraphs). Records are made per section, `kind: guidance`, and standards rank above
  handbooks when both match. Tests.
  *Done 10 Oct (round 1): ECSS `-HB-` and NASA-HDBK prose gives one `guidance` record per numbered section
  (req_id = clause), prose resuming after a list, table or NOTE joins it; handbook records weigh 0.85 on top of
  the guidance weight. Wave-1 handbooks: E-HB-32-20 Parts 1A–7A, -21A, -23A–-26A 346–936 section records each,
  `checked`. Fixture `tests/fixtures/demo_handbook.txt`, `tests/test_handbook.py`.*
- [x] **A6 🤖 `search_requirements` / `compare_topic` know the catalogue.** A named standard that is present but
  not loaded is reported as "in your documents folder, not loaded", distinct from "not in the documents folder".
  *Done 9 Oct (cloud): `not_loaded` unchanged; with a catalogue it is split into `in_documents_folder` (name ->
  catalogued doc IDs with issue, title, status; active ones loadable through corpus.yaml, superseded never) and
  `not_in_documents_folder`, each with its own note. `tests/test_catalogue.py`.*

## Stage B: wave 1 (structures, mechanisms, testing)

Documents: ECSS-E-ST-32-02/-03/-11, E-ST-33-01, E-ST-10-03, E-HB-32-20 (Parts 1–8), -21, -22, -23, -24, -25,
-26; NASA-STD-5002, 5020, 7001, 7002, 7003, NASA-HDBK-7005 (if missing from the download, fetch it), and the
other NASA-5000 series from the catalogue.

- [x] **B1 🤖📄 Add the wave-1 patterns to `documents/corpus.yaml`** and run the health report for them.
  *Done 9 Oct: 42 documents load (7 verified + 35 wave 1): 7 verified, 24 checked, 11 unchecked, 0 errors
  (`eval/CORPUS_HEALTH_WAVE1.md`). NASA-STD-7003 and NASA-HDBK-7005 are not on standards.nasa.gov's listing
  (85 standards) and are still missing; NASA-HDBK-5010 baseline moved to `documents/superseded/` (5010A Vol 1
  supersedes it). Handbook bodies are dropped without counting as unparsed (H6); E-HB-32-24A
  needs H7 (headings at body size). Run with H1 and A4 merged.*
- [x] **B2 🧠📄 / 🤖 Parser fixes.** Layout problems need the real PDF to debug (🧠📄). When a problem can be
  reproduced with invented text (e.g. a heading pattern, an ID convention), write it up in
  `docs/PARSING_NOTES.md` and hand the fix with its fixture to a worker (🤖).
  *H6 and H7 done 9 Oct (cloud): ECSS prose paragraphs come back as unparsed fragments; a NASA body starts at
  `4.0 Title`, else the first numbered heading, else the whole text; the health report adds coverage (words in
  records + unparsed ÷ body words, `min_coverage` 50 %, untuned); bold heading-font lines at body size whose number
  is the next free child become headings (H7). Not yet re-run on the real documents: the wave-1 health
  report 📄 shows the effect (expect E-HB-32-20 Parts 1A–4A to drop to `unchecked`, E-HB-32-24A's duplicates to go).*
  *Re-run 10 Oct (round 1), before and after A5: H6 dropped 9 documents to `unchecked` by the unparsed share
  (handbook prose, ECSS descriptive paragraphs), H7 removed E-HB-32-24A's 32 duplicates. Thresholds tuned on it:
  `min_coverage` 75 % (standards 78–99 %), the unparsed-share gate no longer applies to ECSS standards. With A5:
  44 documents, 7 verified, 32 checked, 5 unchecked (`eval/CORPUS_HEALTH_WAVE1.md`). Still unchecked:
  E-HB-32-20 Part 8A (0 records), E-HB-32-22A (ragged tables), NASA-HDBK-5010 Vol 1 (valid IDs 92 %),
  NASA-HDBK-5026 (ragged tables), NASA-HDBK-7005 (98 % unparsed, H8).*
- [x] **B3 👤📄 Hand-check each wave-1 standard:** requirement count, 5–10 spot-checked IDs, and every table you
  rely on. Add them to `tests/test_real_documents.py` and to `VERIFIED` in `catalogue.py`. Handbooks can stay
  `checked`.
  *Prepared 10 Oct (round 2): `eval/HAND_CHECK_WAVE1.md` (`scripts/hand_check_list.py`) lists the 19 `checked`
  wave-1 standards with counts, spot-check IDs and pages, parser flags and tables. Owner check pending; also
  check H11 (NASA-STD-5020B 4.2.3 text).*
  *Checked 10 Oct (Claude for the owner, against the PDFs; results ticked in `eval/HAND_CHECK_WAVE1.md`): spot
  checks 146/152 right; requirement counts right for 6 of 19 (32-11C, 33-01C, 5005D, 5018, 5023, 7003A); 34 of 63
  tables right. Only ECSS-E-ST-32-11C is ready for `VERIFIED`; the rest wait for parser fixes H12–H17
  (`docs/PARSING_NOTES.md`; most urgent: 5012C Table 1 numbers wrong, 10-03C tables lose their continuation pages,
  10-03C / 5005D wrong IDs). H11 answered: the values are only in Figure 1. Still open here: tests + `VERIFIED`.*
  *Round 3 (10 Oct): parser fixes H8, H9, H12–H17 (#46–#49) re-checked on the PDFs; 8 standards now `VERIFIED` with
  real-document tests (#45, #50): ECSS-E-ST-32-03C, -32-11C, NASA-SPEC-5022, NASA-STD-5002B, 5005D, 5006A, 5018,
  5023 (15 verified in all). 32-03C has 43 requirements (5.4.2b, after an equation, was lost too). Still `checked`:
  10-03C (counts and IDs right now; tables to re-check after H15), 32-02C (Table 4-8 labels), 33-01C (Tables 4-6/4-7),
  5008B (318 of 319 tags), 5009C / 5012C / 5017B / 5020B / 7002B (H17 table defects; 5012C Table 1 values to re-check
  after the superscript fix), 7001C (Table 2), 7003A (new paragraph IDs need a fresh hand check).*
  *Round 4 (11 Oct): layouts measured on the PDFs, then table fixes H16/H17 (#56–#60; `tests/pdfgen.py` builds invented
  test PDFs), NASA italic / subscript line fixes (#61, #62), each re-checked on the real tables: 8 more `VERIFIED` with
  tests (#62): ECSS-E-ST-32-02C, -33-01C, NASA-STD-5008B, 5009C, 5012C, 5017B, 7001C, 7003A (23 verified in all).
  Still open: ECSS-E-ST-10-03C (counts and IDs right; 14 tables need a table-by-table pass, 2 now ragged:
  `unchecked`), NASA-STD-5020B (Table 8, the Appendix example), NASA-STD-7002B (Table 1 marks required tests by
  shading). Wave-1 health: 23 verified, 18 checked, 3 unchecked (#64).*
  *Round 5 (12 Oct): all wave-1 standards verified. Layouts measured on the PDFs, then table fixes:
  - H18: 10-03C group rows in column 0, false sub-rows, row-number columns, rows carried over a page break.
  - H19: 7002B shaded cells and their legend; 5020B Table 8 (an appendix example) dropped as degenerate.
  - Integration fixes found by diffing every table against round 4 (#69, #71).
  ECSS-E-ST-10-03C, NASA-STD-5020B and NASA-STD-7002B are now `VERIFIED` with tests (26 verified in all).
  `test_verified_tables_unchanged` pins the table IDs and row counts of every verified document. Wave-1 health:
  26 verified, 17 checked, 1 unchecked (a handbook).*
- [x] **B4 👤 Decided: switch to ECSS-E-ST-32-10C Rev.2 Corr.1.**
- [x] **B4a 🧠📄 Do the switch.** Teach identification to read the corrigendum (`Rev.2 Corr.1`; the cover and
  file name show it), remove or move the top-level `ECSS-E-ST-32-10C_Rev.2.pdf` so the bundle copy is used,
  re-check every 32-10 table value and requirement count against the Corr.1 PDF, update
  `tests/test_real_documents.py`, `VERIFIED` and any eval question that cites Rev.2. Then re-run the retrieval eval.
  *Done 9 Oct: issues read as `Rev.2 Corr.1` (4 corrigenda in the corpus); Rev.2 moved to
  `documents/superseded/`, `documents/corpus.yaml` names the 7 loaded standards. Corr.1 = Rev.2 plus machine
  IDs on 4.3.2.1e / 4.3.2.2b and one Table 4-4 cell printed once; retrieval eval unchanged.*
- [x] **B5 👤📄 About 10 new eval questions** for wave 1 (loads, shock, vibroacoustics, fasteners, pressurised
  hardware), with IDs and numbers checked against the source and answer points as paraphrases.
  *Drafted 10 Oct (round 2): w1-001…w1-011 plus six not-covered questions that wave 1 made stale, rewritten
  (fs-021, fs-034, hand-17…hand-20); fs-021 and hand-19 reviewed by the owner, the rest `review: pending`.
  68 questions, 63 scored for retrieval.*
  *Reviewed 10 Oct (Claude for the owner, IDs and numbers checked on the PDFs): all 30 pending questions `ok`, after
  four edits: hand-18 (dropped an answer point not in the source), fs-025 (+11.2.2.4a), fs-033 (point reworded now that
  test standards are loaded), w1-003 (false record `PVTR 12 / 4.3.3.5` → PVTR 12).*
- [x] **B6 🤖📄 Retrieval eval.** It must not regress on the existing 46 scored questions: recall@5 0.64 (0.74 with
  neighbours), table row hits 0.50. Record it as run 10 in `eval/RESULTS.md`.
  *Done 10 Oct (round 3, run 10, #51): old 46 recall@5 0.63 (0.75 with neighbours), recall@20 0.88, table row
  hit 0.50 / 0.85, identical to the round-1 check: no regression. All 63: 0.65 / 0.76 / 0.88, table row hit 0.41 /
  reachable 0.66 over 22 table questions; the new table questions (7001C, 7003A, 5020B, 33-01C tables) are not reached.*
- [x] **B7 🧠 If B6 shows dilution: two-stage retrieval** (pick candidate documents from the query, discipline,
  titles and headings, then search their records). Tune it on numbers that B6 commits. Then repeat B6 📄.
  *Not needed (10 Oct, run 10): per-document BM25 statistics move 30 expected IDs up and 39 down (median rank ratio
  1.0); oracle-document ranks equal the full index. Revisit with wave 2.*
- [x] **B8 🤖📄 → 🧠 Answer run** with neighbours and wave 1 (`--backend cli`, logged-in Claude Code), plus the
  `--backend agent` vs `api` pair if an `ANTHROPIC_API_KEY` is available. Hand-review new failures, then record the results.
  *Done 10 Oct (round 3; `eval/RESULTS.md`): `cli` 0.85 / 0.12 / 0.03 correct / partial / wrong over 68, citation
  recall 0.92, 0 invented IDs, ungrounded numbers 0.21 (mostly table values without the A3 flag); `cli-agent` 0.76 /
  0.19 / 0.04, ungrounded 0.13, but its gate declines three covered questions. fs-024's reference is stale (32-10C
  Table 4-3 has glass and ceramic rows): 👤. The `agent` vs `api` pair waits for an API key.*
  *Round 4 (11–12 Oct): owner decisions applied to fs-024 / fs-033 (#63). Gate over-declines diagnosed: checker false
  negatives (flag in the next sentence or after `;` in brackets, "hundred per cent", clause numbers, tag ranges),
  fixed in #55, plus status `flagged` (the gate appends the flag instead of declining). r11 `cli-agent`: 0.82 / 0.16 /
  0.01, 0 wrong declines, 0 invented IDs (`eval/RESULTS.md`).*

## Stage C: make the repository publishable

- [x] **C1 👤 Decided: Apache-2.0**, code open source, standards bring-your-own.
- [x] **C1a 🤖 ADR-0007** (open-source the code under Apache-2.0, BYOD, fresh squashed public repository). Closes
  the roadmap's "Decide: stay private / open-source / product".
  *Done 9 Oct (cloud): [ADR-0007](adr/0007-open-source-apache-byod.md) records C1 and C5 (options, why Apache-2.0
  over MIT, why a new repository rather than a squashed `main`) and makes ADR-0002's pre-release checks part of D2.*
- [x] **C2 🤖 Licence and policy files:** `LICENSE`, `NOTICE`, and a disclaimer in the README (not affiliated with
  or endorsed by ESA, the ECSS Secretariat or NASA; ECSS and NASA names are their owners'; answers are aids, not a
  substitute for the applicable standard and its issue; verify against the source). Also `CONTRIBUTING.md`
  (the no-standards-text rule, invented fixtures, how to run tests), `SECURITY.md`, and PR/issue templates with
  a "contains no standards text" checkbox.
  *Done 9 Oct (cloud): Apache-2.0 `LICENSE` (verbatim), `NOTICE`, README disclaimer + licence section,
  `CONTRIBUTING.md`, `SECURITY.md` (GitHub private vulnerability reporting, enabled at D2), PR template and
  issue forms (bug, parsing problem, feature) with a required "no standards text" box. pyproject licence
  metadata is left to C9.*
- [x] **C3 🤖 Text-audit script:** `scripts/audit_standards_text.py` compares every file of the release tree
  (history does not matter: the public repository starts from one squashed commit) against the parsed documents. It reports any run of ≥ 12 consecutive words that
  also appears in a standard, plus table rows copied whole. It writes only file:line and the length of the match.
  *Done 9 Oct (cloud): `python scripts/audit_standards_text.py [--docs documents] [--tree .] [--out FILE]`;
  tracked files vs every catalogued document (superseded ones too); the report adds the matched document /
  table ID. Exit 1 on a hit or a document that did not parse. Not yet run on the real documents (C4).*
- [x] **C4 🤖📄 → 🧠 Run the text audit** on the release tree. Review the hits: `eval/REVIEW.md`, `eval/HAND_TEST.md`,
  `eval/RESULTS.md`, `eval/questions.yaml` and `docs/PARSING_NOTES.md` are the likely places. Numbers from tables
  (factors, test levels) are facts and can stay; sentences should be paraphrases.
  *Done 9 Oct: 285 documents, 0 parse failures, 20 min cold. 10 hits: 3 ECSS-E-ST-32-01C sentences in
  `eval/questions.yaml` / `eval/REVIEW.md` paraphrased; the NASA-STD-5001 title in both READMEs and two
  numbers-only table rows in `tests/test_real_documents.py` kept. Record: `eval/TEXT_AUDIT.md`.*
- [x] **C5 👤 Decided: fresh repository from one squashed commit** (see D1a).
- [x] **C6 🤖 Secret scan** of the release tree (gitleaks or trufflehog), plus a CI job that fails on committed
  `.pdf`, `.doc`, `.docx`, `.pkl`, or anything under `documents/` except the README.
  *Done 10 Oct (round 1): gitleaks 8.30.1 on the tracked tree, no leaks; `scripts/check_release_tree.py` and
  a CI `guard` job (tree check + pinned, checksum-verified gitleaks); `scripts/audit_allowlist.yaml` holds
  the accepted hits so the text audit exits 0 on them; real run 10 Oct: 287 documents, 0 new hits, 4 accepted
  (two titles in `documents/README.md` that A5's handbook records now repeat; `eval/TEXT_AUDIT.md`).*
- [x] **C7 🤖 NASA download script.** Copy `documents/download_nasa_standards.py` into `scripts/` (it is
  gitignored where it is now), then: honest User-Agent, rate limiting, robots.txt
  check, no bulk re-download by default, manifest format documented. Leave ECSS out (registration required).
  Local part done 2026-10-09: `scripts/download_nasa_standards.py` (unchanged copy). Cloud part done 2026-10-09:
  project User-Agent (`--contact`), one request at a time ≥ 2 s apart (or robots.txt Crawl-delay), robots.txt
  checked first and per URL, PDFs already in the folder not fetched again (`--force`, `--only`, `--dry-run`),
  manifest schema 2 documented in the script docstring; tests in `tests/test_download_script.py`.
- [x] **C8 🤖 Public README:** what it is, the 60-second demo with the invented fixtures, bring-your-own-documents
  setup (where to get ECSS and NASA documents, `catalogue`, `corpus.yaml`), MCP client config (Claude Code,
  Claude Desktop, VS Code), tools, parse tiers, eval summary and its limits, roadmap link.
  *Done 10 Oct (round 1); the client snippets are untested against live clients.*
- [x] **C9 🤖 Packaging and CI:** pyproject metadata (licence, URLs, classifiers), version 0.2.0, `CHANGELOG.md`,
  `uvx space-standards-mcp` / `pipx` instructions, CI on Python 3.11–3.13, ruff lint.
  *Done 10 Oct (round 1): PEP 639 licence fields, URLs, classifiers; `uv build` and a clean 3.13 install work;
  ruff E/F/W/I (E501 not enforced).*
- [x] **C10 🤖 Tidy internal docs:** `docs/PROJECT_BRIEF.md` (the personal "secondary goal" line, owner
  details), `CLAUDE.md` (keep; it documents the hard rules), and dated notes that read as private.
  *Done 10 Oct (round 1): owner and career lines out of the brief and ADR-0004/0006/0008.*
  *Decided 11 Oct (👤): `docs/PROGRESS.md` (27 private-repo PR links, cloud history) stays out of the release tree.
  Round 4 adds a release-exclude list (used by D1a, checked by `scripts/check_release_tree.py`) and rewords the
  references in CLAUDE.md, SESSION_PROMPTS, this plan, ADR-0007/0008 and the worker definition.*
  *Done 11 Oct (round 4, #54 + this plan): `scripts/release_exclude.txt` (`docs/PROGRESS.md`); `check_release_tree.py`
  fails on a stale entry (CI), `--release` fails on an excluded file or a markdown link into one, `--print-excluded`
  feeds D1a's `git rm --cached`.*

## Stage D: release

- [x] **D1 🤖📄 Final local run:** `pytest` with the real documents, retrieval eval, catalogue summary, text audit
  on the release tree.
  *Done 12 Oct (round 5, on main after #73):
  - real-document pytest: 410 passed;
  - retrieval run 12 and r12 answers (`eval/RESULTS.md`);
  - catalogue: 287 documents (285 active), 44 loaded, 26 verified / 17 checked / 1 unchecked;
  - text audit: 0 new hits, 24 accepted (`eval/TEXT_AUDIT.md`), after replacing one copied fixture row.*
- [x] **D1a 🧠👤 Fresh repository.** Rename this repository to `space-standards-mcp-dev` (stays private: the full
  history). Create a new **private** `space-standards-mcp`, push one commit holding the release tree
  (`git checkout --orphan release && git commit -m "space-standards-mcp v0.2.0"`, authored by you), tag `v0.2.0`.
  Check the new repository has exactly one commit, no PRs, no `eval/runs/`, nothing under `documents/` but
  the README. Point the local checkout's `origin` at the new repository. Creating and pushing the repository waits for your "go".
  Files on the release-exclude list (at least `docs/PROGRESS.md`, decided 11 Oct) are left out of that commit:
  after `git checkout --orphan release`, `git rm --cached $(python scripts/check_release_tree.py --print-excluded)`,
  commit, then `python scripts/check_release_tree.py --release` must pass.
  *Done 14 Oct (round 6, owner's "go"): this repository renamed to `space-standards-mcp-dev` (private); new private
  `space-standards-mcp` with one commit "space-standards-mcp v0.2.0" (ba86d9c, authored by the owner), tag
  `v0.2.0`, 0 PRs, 106 files, no `eval/runs/` or `docs/PROGRESS.md`, `documents/` holds only the README; CI green.
  The first push's `guard` failed on the stale-entry check (PROGRESS.md is left out by design); fixed on -dev
  (#80: a tree with no excluded file runs the release checks) and the release commit rebuilt from it.
  Local checkout (owner decision 14 Oct: develop on -dev): `origin` = -dev, `public` = the new repository; `main`
  tracks `origin/main`, `release` tracks `public/main`; `gh repo set-default` is -dev.*

**Release flow (after D1a).** Work and PRs stay on -dev. Each release is one new commit on the public `main`
whose tree is -dev's `main` minus the release-exclude list, with the previous release commit as its parent (no
force-push once the repository is public), tagged with the `pyproject.toml` version:

```bash
git fetch origin && git fetch public
git worktree add --detach ../release-build origin/main && cd ../release-build
git rm -q --cached $(python scripts/check_release_tree.py --print-excluded)
python scripts/check_release_tree.py --release
python scripts/audit_standards_text.py --docs ../space-standards-mcp/documents   # 0 new hits
c=$(git commit-tree "$(git write-tree)" -p public/main -m "space-standards-mcp vX.Y.Z")
git tag vX.Y.Z "$c" && git push public "$c":refs/heads/main && git push public vX.Y.Z
cd - && git worktree remove --force ../release-build && git branch -f release public/main
```

Check afterwards: the public CI is green, `git diff --stat origin/main public/main` lists only the excluded files,
and the public repository has no PRs and nothing under `documents/` but the README.
- [x] **D2 👤 Go public:** first the ADR-0002 / ADR-0007 checks: read the current ECSS terms of use on ecss.nl and
  re-check the distribution statement of every NASA document the docs or evals name. Then flip the new repository's visibility (`gh repo edit --visibility public
  --accept-visibility-change-consequences`, or in the GitHub settings). Then enable branch protection on `main`,
  Dependabot, secret scanning and private vulnerability reporting.
  *Done 15 Oct (round 7, owner's "go"):
  - ECSS License agreement/Disclaimer on ecss.nl (from ECSS-P-00C clause 5.8): copyright with ESA; no
    reproduction without ESA's consent; quotations identified with reference and version. Nothing on local
    processing. The repository holds no standards text; eval answer points are paraphrases with IDs.
  - NASA: the local PDFs of 18 named documents carry "approved for public release" on their first pages; seven
    named ones (HDBK-7005, 5012C, HDBK-5026, 3001 Vol 2, 2818, 8719.24 and its Annex) carry no statement and were
    confirmed public by the owner (all from standards.nasa.gov). The Annex's export-control wording is a
    fill-in template, not a marking.
  - `space-standards-mcp` made public at v0.2.1. Branch protection on `main`: CI checks `test (3.11–3.13)` and
    `guard` required, one approving review, linear history, no force-push or deletion; admins are not enforced, so
    the release push below goes through as the owner. Dependabot alerts, secret scanning with push protection and
    private vulnerability reporting enabled; `parsing` label created for the issue form.
  - Dependabot PRs go to -dev, where development happens: security updates are on there and off on the public
    repository (it keeps its alerts and stays free of PRs), and `.github/dependabot.yml` (weekly pip and Actions
    updates) is on the release-exclude list.*
- [ ] **D3 🤖 Optional:** publish to PyPI, list the server in an MCP registry, write an announcement post.
  *Prepared 15 Oct (round 8, owner chose all three; #88, #90): PyPI name `space-standards-mcp` free; Trusted
  Publishing workflow `publish.yml` (public repository only, runs on a published GitHub Release or by hand, not on
  the release flow's tag push); sdist limited to source and metadata; `server.json` for the official MCP registry
  (`io.github.manojknaikade/space-standards-mcp`, version tested against `pyproject.toml`) and the README ownership
  marker; `docs/PUBLISHING.md` (one-time setup and steps); `docs/ANNOUNCEMENT_DRAFT.md` (-dev only). Shipped in
  v0.2.2. Open, 👤: PyPI account + pending trusted publisher, `pypi` environment on the public repository, a GitHub
  Release for v0.2.2, then `mcp-publisher publish`, then the post.*
  *PyPI done 15 Oct (round 9): owner set up the pending publisher and the `pypi` environment (owner as reviewer);
  GitHub Release v0.2.2 published the package (0.2.2 on PyPI, `mcp-name` marker present, clean install checked).
  README install section from PyPI (#94) shipped in v0.2.3 (release commit 65c7f33, GitHub Release v0.2.3; 0.2.3 on PyPI after the owner's approval). MCP registry: owner
  logged in (`mcp-publisher login github`), `io.github.manojknaikade/space-standards-mcp` 0.2.3 published from the
  public tag v0.2.3, listed as active. Open, 👤: the post (docs/ANNOUNCEMENT_DRAFT.md).*

## After going public

Waves 2–4 from ADR-0006 follow the same loop as stage B (B1 🤖📄 → B2 🧠📄/🤖 → B3 👤📄 → B5–B6 👤📄/🤖📄 → B7 🧠): rest
of ECSS-E and the NASA engineering series; ECSS-Q and NASA 87xx; ECSS-M/-U/-S and the remaining handbooks.
Then issue diffing and tailoring matrices (ROADMAP Phase 4).

- [x] **Wave 2 B1 🤖📄** patterns in `documents/corpus.yaml` and health report (`eval/CORPUS_HEALTH_WAVE2.md`, #89).
  *Done 15 Oct (round 8): all ECSS-E-ST / -HB / -AS and NASA STD / HDBK / SPEC numbered 1000–7999 (87xx is wave 3;
  NASA-STD-10001 / 10002 and 7919.1 left out). 167 documents load (44 + 123): 26 verified, 100 checked, 41
  unchecked (7 adoption notices), 0 parse errors. Retrieval on the 63 scored questions: recall@5 0.65 → 0.67,
  neighbours 0.75, @20 0.88 → 0.89, tables unchanged; no question left the top 5.*
- [ ] **Wave 2 B2 🧠📄 / 🤖** parser fixes for the 33 unchecked wave-2 standards and handbooks (list in round 8's
  PROGRESS entry and the health report): low valid-ID share (E-HB-10-02A, E-HB-40A, E-ST-50-11C, E-ST-40C,
  NASA-STD-3001 Vol 1), ragged tables (E-HB-31-01 parts, E-ST-70-31C, E-ST-50-13C), NASA documents that parse
  to almost nothing (HDBK-2203, 4007A, 6024, 1005, 4002B, 1004; STD-2818, 2821, 2822, 6033).
  *Round 9: NASA near-empty parses diagnosed on the PDFs (PARSING_NOTES H20–H24). H20 contents-page body bounds
  fixed (#95): 6024 / 4002B / 1005 now `checked`; wave 2 26 / 103 / 38. Open: H21 4007A unnumbered display-font
  headings, H22 3001 Vol 1 generic font names, H23 2203 stub, H24 28xx out of scope (owner), 6033; then the ECSS
  valid-ID and ragged-table groups.*
- [ ] **Wave 2 B5 👤** about 10 new eval questions for wave 2.
  *Drafted 15 Oct (round 9, #93): w2-001 … w2-010 (`review: pending`), wave-2 `checked` sources, IDs and tables
  checked with the tools; w2-006 trimmed to no record-text numbers. Retrieval on the 9 scored: recall@5 0.91,
  @20 0.94; the old 63 unchanged. Open, 👤: owner review.*

## Order at a glance

Done steps are kept for the record. Each line is one round; steps on a line run in parallel.

1. A1 🤖 → A2 🤖📄 (health report) → A2a 🤖 (fixes) → A2 📄 again
2. A3, A4, A5, A6 🤖 (parallel)
3. B1–B3, B4a → B5–B6 → B7 🧠 if needed → B8
4. C1a, C2, C3, C6, C8, C9, C10 🤖 (parallel) → C4 → C7
5. D1 🤖📄 → D1a 🧠👤 → D2 👤 → D3 🤖

Open work from 10 Oct, as rounds:

- **Round 1 (done 10 Oct):** A3 🤖, A5 🤖, C6 🤖, C8 🤖, C9 🤖, C10 🤖 in parallel (fixture-only) + the one 📄 run: wave-1 health
  re-run with H6/H7 (B1/B2 check, tune `min_coverage`) 🤖📄; the orchestrator reviews and merges.
- **Round 2 (done 10 Oct):** B3 👤📄 hand checks (orchestrator prepared the lists; the check itself was done by Claude for the owner), B5 👤📄 questions.
- **Round 3 (done 10 Oct):** parser fixes from B3 (H17 5012C superscripts, H15 table continuation, H13 headings, H12 false NASA records, H14, H16; 🤖 with invented fixtures, 🧠📄 re-check on the PDFs) → B3 close: tests + `VERIFIED` (32-11C now, the rest after the fixes) → B6 🤖📄 → B7 🧠 if dilution → B6 again → B8 🤖📄 → 🧠 review.
- **Round 4 (done 12 Oct):** B3 rest (H16/H17 table fixes, 8 more verified), the gate's wrong declines (#55),
  fs-024 / fs-033, release-exclude list (C10), run 11 (no retrieval regression; `cli-agent` 0.82 correct), text audit.
- **Round 5 (done 12 Oct):** B3 closed (10-03C, 5020B, 7002B verified; 26 in all), ownerless tables searchable
  (#66 → #69; matrix rows not indexed, #72), the regression from #69 found by B6 and fixed (#71), gate fixes (#71,
  #73), run 12 (record recall as run 11, table recall 0.37 → 0.46 @5; `cli-agent` 0.85 correct), D1 local run.
- **Round 6 (14 Oct):** gate: launcher-name numbers (#75); citations: NASA paragraph numbers, empty-query message
  (#76); parser: 7002B / 10-03C / 7003A quirks (#78); matrix-row lift tried and closed (#77); run 13 (as run 12);
  D1a done (fresh private repository, v0.2.0; guard fix #80).
- **Round 7 (15 Oct):** D2 checks and go public (branch protection, Dependabot, secret scanning, private
  vulnerability reporting); `cli-agent` answer run r13 on the round-6 code.
- **Round 8 (15 Oct):** fs-021 required search arguments (#87); D3 prepared (#88); wave 2 B1 (#89); Dependabot
  Actions v7 (#85, #86); v0.2.2 released to the public repository.
- **Round 9 (15 Oct):** PyPI live (0.2.2, 0.2.3) and MCP registry listing (0.2.3); wave 2 B5 drafted (#93); B2 diagnosis and H20 (#95);
  README PyPI install (#94); v0.2.3 (#96).
- **Next:** the post (owner), B5 review (owner), wave 2 B2 continued.
