# Hand test — 20 real questions (Phase 1, last item)

ROADMAP Phase 1: "Connect to Claude / VS Code and try 20 real questions by hand."

Date: 7 October 2026. Client: Claude Code (desktop) with the `space-standards` MCP server, local `documents/`.

## Method

1. The 20 questions below were written **before** any of them was run, from domain knowledge only
   (no look at the parsed records or the source text), and are all new (none in `eval/questions.yaml`).
2. Each question is answered through the MCP tools only, the way a client would: `search_requirements`
   first, then `get_requirement` / `get_table` / `get_references` as needed.
3. The answer is then checked against the source documents (text extracted from the local PDFs/Word file,
   not from the parser), and graded:
   - **retrieval**: did the first search put the right clause in its top 5 (hit), only after a reformulated
     search or a follow-up call (late), or not at all (miss)?
   - **answer**: correct / partial / wrong / correctly "not covered".
   - **citation**: every requirement text in the answer carries a citation from the tools; no invented IDs.
4. Problems found go to "Findings", which feed Phase 2/3 work.

Mix: 5 numeric, 8 lookup, 2 classification, 2 ECSS vs NASA comparison, 4 "not covered" (one question is both
lookup and a probable partial: the requirement is loaded but its numbers live in a document that is not).

## Questions

| # | Type | Question |
| --- | --- | --- |
| H01 | numeric | What qualification and acceptance test factors does ECSS-E-ST-32-10 specify for launch vehicle structures? |
| H02 | numeric | What factor of safety does ECSS-E-ST-32-10 require against buckling of launcher structure? |
| H03 | lookup | How does ECSS-E-ST-32-10 build the design factor from the factors of safety, the model factor and the project factor? |
| H04 | numeric | Which additional factor does ECSS-E-ST-32-10 apply to joints, inserts and fasteners, and what is its value? |
| H05 | lookup | What checks must a structural finite element model pass under ECSS-E-ST-32 before it is delivered or used for coupled loads analysis? |
| H06 | lookup | What does ECSS-E-ST-32 require about the minimum natural frequencies of a structure? |
| H07 | lookup | What does ECSS-E-ST-32 require when correlating the structural mathematical model with modal survey or vibration test results? |
| H08 | lookup | What must be done under ECSS-E-ST-32-01 when NDT detects a crack-like defect in a PFCI? |
| H09 | numeric | What service life factor does NASA-STD-5019A apply in the damage tolerance (safe-life) analysis of fracture critical parts? |
| H10 | classification | Under NASA-STD-5019A, when can a part be classified non-fracture critical because it is contained or has low release mass? |
| H11 | lookup | When does NASA-STD-5019A accept a proof test instead of NDE to screen flaws in fracture critical hardware? |
| H12 | compare | Compare how ECSS-E-ST-32-01 and NASA-STD-5019A treat welds in fracture critical / safe-life metallic parts. |
| H13 | compare | Compare how ECSS-E-ST-32-01 and NASA-STD-5019A require fasteners in fracture critical / safe-life applications to be screened. |
| H14 | lookup | What does ECSS-Q-ST-70 require about stress corrosion cracking when selecting metallic materials? |
| H15 | lookup (probable partial) | What outgassing screening criteria (RML, CVCM) must materials meet under ECSS-Q-ST-70? |
| H16 | lookup | What does ECSS-E-ST-32-08 require for adhesive bonding and bonded joints? |
| H17 | not covered | What random vibration qualification level applies to a payload adapter (ECSS-E-ST-10-03)? |
| H18 | not covered | What margin over the maximum expected pyroshock environment does NASA-STD-7003 require for qualification of a fairing separation system? |
| H19 | not covered | What separation factor of safety does NASA-STD-5020 require for preloaded bolted joints? |
| H20 | not covered | What torque margin does ECSS-E-ST-33-01 require for a fairing mechanism? |

## Results

Retrieval: **hit** = right clause in the first search's top 5/6; **late** = needed a reformulated search or a
direct `get_requirement`; **n/a** = not-covered question. Answers are paraphrased here (no standards text).

| # | Retrieval | Answer | Key citations returned | Notes |
| --- | --- | --- | --- | --- |
| H01 | hit | correct | 32-10 4.3.1a + Table 4-2; 4.1.4.4a | LV global flight loads: KQ 1.25 *corrected* (per 4.2.2 / Annex A), KA 1 or Jp (Jp 1.05–1.1 typical); local dynamic loads KQ 1.25, KA N/A; thermal 1/1; pressure per 32-02. Cell text "1,25corrected" (F4). |
| H02 | hit | correct | 32-10 4.3.2.3a + Table 4-5 | LV FOSU 1.25 (global and local), FOSY 1.1 local / N/A global, FOSU 2.0 if verified by analysis only; knock-down factors not included (note → HB-32-24). |
| H03 | late | correct | 32-10 4.1.4.1a, 4.2.1a + Table 4-1, 4.1.4.2a, 4.1.4.3a, 4.1.5.3a | First search returned the individual factors but not the combining clause/table; a reformulation ("DLL from LL") put 4.1.4.1a and 4.2.1a at ranks 1–2. LV: design factor KP×KM; yield coef FOSY×KMP×KLD; ultimate coef FOSU×KMP×KLD. |
| H04 | hit | **partial** | 32-10 4.1.5.2a/b (KLD), 4.3.2.2a/b + Table 4-4 | KLD (local design factor; 1.2 typical for satellites, must be justified) found. Table 4-4 values cannot be attributed to Failure vs Gapping/Sliding rows: sub-row labels lost (F2). |
| H05 | hit | correct | 32C I.2.1<13.3>a/b (MMDD model checks) | Checks are reporting duties (geometry, topology, rigid-body strain energy, static, thermo-elastic, normal modes); no numeric acceptance criteria in 32C (those are in ECSS-E-ST-32-03, not loaded). |
| H06 | hit | correct | 32C 4.3.5a, 4.6.2.4a | Stiffness/frequency requirements must be identified and verified by modal analysis; no frequency values in the loaded standards. |
| H07 | late | correct | 32C 4.6.2.2b, Annex O (TAC DRD) | First search top 5 had DRD clauses only; reformulated search put 4.6.2.2b first. No numeric correlation criteria (ECSS-E-ST-32-11, not loaded). |
| H08 | hit | correct | 32-01 10.7.1b, 10.7.2.1.1a, 10.7.2.2b/c, 10.7.3a | Customer approval to use; verify as crack-like + FM analysis or test; improved NDT (90/95) if origin not eliminated. |
| H09 | late | **partial** | 5019A 7.3 guidance 10, FCR 12, FCR 12 / 7.3.2.c, FCR 12 / 7.3.3 | Life factor 4 found, but rank 1 was guidance; the requirement came from a second search. FCR 12 / 7.3.2.c is missing its A/B sub-items, incl. the 1.4 factor alternative for single-event lives (F1). |
| H10 | hit | correct | 5019A FCR 8, FCR 8 / 6.2.1(.a/.b), FCR 8 / 6.2.2.b | Hazard-based criteria, no mass threshold; external released mass only within an agreed debris-field criterion. |
| H11 | late | correct | 5019A FCR 18 (via `get_requirement`), FCR 16, 8.1.3 guidance 4 | FCR 18 (proof test as flaw screening: rationale in FCP, RFCB approval) was not in the top 6 for "proof test … instead of NDE" (F5). |
| H12 | hit | correct | 32-01 8.3.2a–e, 11.2.2.8c; 5019A FCR 16, FCR 11 / 7.2.6 | ECSS: weldment properties, residual stresses, imperfections in FM analysis; reduced programme X-ray waiver conditions. NASA: post-proof NDE of welds. 7.2.6 record lost its "(1)" lead-in (F1). |
| H13 | hit | correct | 32-01 8.8b/f/g, 11.2.2.7a; 5019A FCR 11 / 7.2.8.a, FCR 7 / 6.1.1.4(.b), 6.1.1.5.b | Both: eddy current on safe-life/fracture-critical fasteners (ECSS also crack size 1.27 mm). FCR 7 / 6.1.1.4 record garbled (F1). |
| H14 | hit | correct | Q-70 5.1.10a/b | Structural metals per Q-ST-70-36 clauses; others tested per Q-ST-70-37 (neither loaded). |
| H15 | hit | correct (partial by design) | Q-70 5.1.4b/c/d | Screening per Q-ST-70-02; RML/CVCM limits not in loaded set — answer says so. |
| H16 | late | correct | 32C 4.6.2.12a, 4.5.12a; 32-01 8.4.1b | 32-08 has no bonding requirements; with "ECSS-E-ST-32-08" in the query the filter returned only weak 32-08 hits (top score 9.8). Without the doc name, 32C clauses rank 1–2 (F6). |
| H17 | n/a | correct: not covered | (32-01 6.4.3b mentions 10-03 DRDs only) | No vibration levels loaded. |
| H18 | n/a | correct: not covered | — | Trap: results include 5019A FCR 14 / 7.5.1 with a "1.4 × max expected flight load" test load for single-event fracture critical parts — must not be reused as a pyroshock margin. Formula in that record garbled (F4). |
| H19 | n/a | correct: not covered | 5001B FSR 27 | 5001B delegates threaded fasteners to NASA-STD-5020 (not loaded). |
| H20 | n/a | correct: not covered | — | All scores ≤ 6.5; no signal that ECSS-E-ST-33-01 is not loaded (F6). |

**Totals:** retrieval 11 hit / 5 late (of 16 covered questions); answers 14 correct, 2 partial, 4 correctly
"not covered". No invented IDs; every quoted requirement came with a tool citation. Both partials are caused
by parsing defects, not by retrieval.

## Findings

Checked against the source text extracted from the local PDFs.

- **F1 — NASA-STD-5019A nested items misplaced (parser, high).** Third-level items labelled `A.`/`B.` and
  `i.`/`ii.` under a `(n)` item are not kept with their `(n)` item: they end up in the clause-level record
  (FCR 11 / 7.2.1, FCR 11 / 7.2.2, FCR 7 / 6.1.1.4, FCR 11 / 7.2.6) or in a following guidance record
  (6.1.1.4 guidance 6 contains item "(4)"), with lead-in lines lost. FCR 12 / 7.3.2.c ends at "one of the
  following:" — the two alternatives (incl. the 1.4 factor) are not in that record. Answers lose numbers.
- **F2 — ECSS-E-ST-32-10 Table 4-4 row labels (parser, high).** The three sub-rows (Failure;
  Gapping/Sliding safety critical; Gapping/Sliding other) all carry the same merged label, so FOSY/FOSU
  values can't be attributed. Needs per-sub-row labels and a hand-check like Tables 4-1…4-6 had.
- **F3 — ECSS-Q-ST-70C bimetallic-couples table unusable (parser, high).** Indexed as "Table 5" with
  caption "1 Compatible couples…" (should be Table 5-1); rotated column headers come out reversed
  ("syolla reppoC-muinimulA"); every cell holds the legend text. It also pollutes search results
  (shown as `matched_table_row` for an unrelated moisture clause in H14).
- **F4 — Cell/formula text (parser, low).** 32-10 Table 4-2 "1,25corrected b" (missing space; the
  "corrected" qualifier matters for launch vehicles). 5019A FCR 14 / 7.5.1 has a garbled math run.
- **F5 — Guidance outranks requirements; vocabulary gaps (search, medium).** H09 ranked guidance above the
  FCR; H11 missed FCR 18 for "instead of NDE" (source says "flaw screening technique"). Candidates for
  Phase 3 hybrid search; also consider a small boost for `kind = requirement`.
- **F6 — Named-document handling (search, medium).** A query naming a loaded document with no relevant
  content (H16) returns weak hits from that document only; a query naming a document that is not loaded
  (H18, H20, earlier Q-ST-70-71) silently falls back to all documents. Suggest: return a
  `not_loaded: [...]` field, and fall back to all documents when the filtered top score is low.
- **F7 — Coverage.** Standards repeatedly referenced and not loaded: ECSS-Q-ST-70-71, -70-15, -70-36,
  -70-02, ECSS-E-ST-32-03, -32-11, -10-03, NASA-STD-5009, -5020, -7003. Inputs for Phase 4 ordering.

Earlier the same day, four ad-hoc questions (7075 surface treatment, black anodizing, NDT for steel,
cadmium) were asked in the same session; they surfaced the ECSS-Q-ST-70-71 gap (F7) and are not counted.

## Status of findings (7 October 2026, branch `parser-fixes-hand-test`)

- F1 fixed: `A.`/`ii.` items stay with their `(n)` item; list items after a guidance paragraph go back to the
  requirement; `b.` at an unusual indent is a letter item. FCR 12 / 7.3.2.c now holds both alternatives;
  FCR 7 / 6.1.1.4.b holds items (1)–(7) (item (3) was missing before); FCR 8 / 6.2.5.b and
  FCR 12 / 7.3.3.a–f are new citable records.
- F2 fixed: Table 4-4 rows labelled per sub-row, 11 rows (man-rated failure is one row).
- F3 fixed: Table 5-1 with its ID and caption, 18 named columns, 18 rows, legend as `Key 0`–`Key 3`.
- F4 partly fixed: "1,25 corrected b". The garbled formula in FCR 14 / 7.5.1 is not fixed.
- F5, F6: addressed on branch `search-fixes-f5-f6` (light stemming, guidance weight, `not_loaded`,
  `elsewhere`; eval run 6 in `eval/RESULTS.md`). FCR 18 now ranks 6th for H11. Paraphrase gaps stay for Phase 3.
- F7 (coverage) is open.
