# Evaluation results

## Phase 2 summary — closed 8 October 2026

The eval set has 57 questions (17 numeric, 17 lookup, 7 classification, 5 compare, 11 not covered). 46 are
scored for retrieval and 10 carry `expected_tables`. The first 21 passed domain review on 7 Oct; review of the
16 v2 additions (`fs-022`…`fs-037`) was waived by the domain owner. All numbers below were re-run on 8 Oct with the code on `main`.

| Measure | Value |
| --- | --- |
| retrieval recall@5 / @20 (46 questions) | 0.64 / 0.89 |
| table recall@5: row hit / reachable (10 questions) | 0.50 / 0.85 |
| answers: correct / partial / wrong (in-session, self-judged) | 53 / 4 / 0 |
| citation recall, answers | 0.97 |
| invented IDs, ungrounded numbers | 0 / 0 |
| not covered: declines with no numbers | 11 / 11 |

What Phase 2 showed, and what it means for Phase 3:

1. **Retrieval limits the answers.** All 4 partials are retrieval misses, not wrong statements. The remaining
   ranking misses are paraphrase gaps (fs-027 6.3.3c at rank 36, fs-026, hand-05, hand-09), so hybrid search
   (BM25 + embeddings) comes first in Phase 3.
2. **The grounding rules hold with an off-the-shelf client.** With the MCP tools and server instructions alone,
   the answers had no invented IDs or ungrounded numbers, and every not-covered question was declined. The agent
   should therefore add *enforcement* (run `citations.py` on each draft and revise or decline when it fails), not
   orchestration. See [ADR-0005](../docs/adr/0005-agent-loop.md).
3. **The answer baseline is optimistic.** It was answered and judged in the same session by the same model.
   It stands as the Phase 2 baseline. The agent comparison in Phase 3 should use a scripted `generate` run, with
   a judge that did not write the answers, for both the plain client and the agent.
4. **The checker needed real answers to calibrate it.** Its first pass on the baseline flagged 6 issues, and all
   6 were false positives (NASA guidance IDs, standards that are not loaded). Expect more of this as Phase 4
   adds documents. Every answer flagged by the checker should be looked at by hand before the rule is trusted.

## Run 13 — 14 October 2026 — round 6 (gate and citation fixes, three parser quirks)

Code: main after round 6 (#75, #76, #78). The changes:
- Gate: numbers inside launcher names ("Ariane 5", "Atlas V", "Long March 3B") are not answer values (#75).
- Citations: a paragraph number right after a document name ("NASA-STD-7003A, 4.3.1.1") is a citation when that
  document has the record (tagless NASA records, handbook paragraphs); an empty search query returns a message
  (#76).
- Parser: 7002B Table 1 group label, 10-03C Table 4-1 "1." group, 7003A 4.3 lead-in as guidance (#78). The
  uncached per-table snapshot changed exactly those three (10-03C Table 4-1 rows 36 → 35; 7002B Table 1 label
  column; 7003A records 68 → 69); the later 7003A 4.3 guidance numbers shift by one.

Corpus: 44 loaded documents, 26 verified, 17 checked, 1 unchecked. All 285 active documents: 26 verified, 166
checked, 93 unchecked (eval/CORPUS_HEALTH.md, regenerated for the current parser).

**Retrieval (run 13, BM25): identical to run 12.** All 63: recall@5 0.65 / neighbours 0.75 / @20 0.88. Tables
(23): @5 0.46 / 0.72, @20 0.59 / 0.87.

**Answers: no new generate run.** The r12 answers were replayed through the round-6 checker on the real index
(the main code before round 6 replays them unchanged):
- fs-033: the "unflagged" 5 (from "Ariane 5") is gone; no unflagged numbers left.
- hand-18 (r12): cites NASA-STD-7003A 4.3.1, 4.3.1.1, 4.3.2 and Table 1 (was Table 1 only); 0 ungrounded numbers
  (was 1). r12a's hand-18, which the scorer saw with no citation, cites 4.3.1 and 4.3.1.1.
- About ten other answers gain handbook-paragraph citations (e.g. NASA-HDBK-7005 4.6.7, ECSS-E-HB-32-20 Part 3A
  26.8.3.2); two checked by hand were real citations.

**Closed without merging:** #77 (matrix rows lift the records they name). It kept table recall but gained only
+0.01 records @20 (w1-009) and nothing @5, with its factor next to a cliff (≥ 0.55 drops tables @20 to 0.50–0.54:
the ownerless 7001C Table 1 falls out). A matrix caption and headers match the query and lift all its records at
once.

## Run 12 and answers — 12 October 2026 — round 5 (ownerless tables, 26 verified, gate fixes)

Code: main after round 5 (#69, #71–#73). The changes:
- Tables no record points to get a table-level owner (kind `table`), so they are searchable. The exception is
  requirements-matrix rows naming a record's tag, which are not indexed (#72).
- Lowercase "table 1" references count.
- 10-03C tables (H18), 7002B shading and 5020B Table 8 dropped (H19), plus the integration fixes.
- Gate: clause numbers (#71) and "TAG 43/44" shorthand (#73) are not values or invented IDs.

Corpus: 44 loaded documents, 26 verified, 17 checked, 1 unchecked (eval/CORPUS_HEALTH_WAVE1.md).

**Retrieval (run 12, BM25):** no record-recall regression, and table recall up.

| Subset | Questions | recall@5 | with `--neighbours` | recall@20 | table row hit / reachable @5 | @20 |
| --- | --- | --- | --- | --- | --- | --- |
| old 46 (run 11) | 46 | 0.63 | 0.75 | 0.88 | 0.50 / 0.85 (10) | 0.55 / 0.95 |
| old 46 (run 12) | 46 | 0.64 | 0.75 | 0.88 | 0.50 / 0.85 (10) | 0.55 / 0.95 |
| all (run 11) | 63 | 0.65 | 0.76 | 0.88 | 0.37 / 0.63 (23) | 0.41 / 0.70 |
| **all (run 12)** | 63 | **0.65** | **0.75** | **0.88** | **0.46 / 0.72 (23)** | **0.59 / 0.87** |

- **Tables:** NASA-STD-7003A Table 1 (hand-18, w1-010) is now reached at k = 5. NASA-STD-7001C Table 1 (w1-001,
  w1-003) is reached at k = 20 but not at k = 5, and fs-021 not at all.
- **Records, per question against run 11:** fs-017 @5 0.67 → 1.0. w1-002 @5 1.0 → 0.5: ECSS-E-ST-10-03C
  5.5.2.3f is at rank 6, below its own Table 5-2 hits.
- **Before #72**, the restored requirements-matrix tables (5019A Tables 2–7, 7001C Table 3) took rank 1 above the
  records they copy: all 63 fell to 0.64 / 0.74 / 0.86.
- **Not taken (follow-up):** letting a tagged matrix row be owned by its record gave 0.68–0.69 / 0.78–0.79 / 0.88,
  but table @20 fell to 0.50 / 0.78. The matrix row takes the record's best-row slot from the expected table.
- **A first run 12 (r12a) was discarded.** #69 had dropped ten requirements-matrix tables, which #71 restored. r12a
  scored 0.65 / 0.75 / 0.88 and 0.84 / 0.15 / 0.01.

**Answers (`cli-agent`, Sonnet 5.5, `--judge cli`, 68 questions; `eval/runs/r12-cli-agent`, code 87952fa,
gitignored):**

| Measure | r11 `cli-agent` | **r12 `cli-agent`** |
| --- | --- | --- |
| judge: correct / partial / wrong | 0.82 / 0.16 / 0.01 | **0.85 / 0.13 / 0.01** |
| answer-point coverage | 0.94 | 0.95 |
| citation recall (expected IDs) | 0.89 (63) | 0.90 (63) |
| table citation recall | 0.78 (23) | **0.89 (23)** |
| invented IDs | 0.00 | 0.00 |
| ungrounded numbers (covered) | 0.11 | 0.14 |
| not covered: declines, no numbers | 1.00 (4) | 1.00 (4) |
| covered: declines wrongly | 0 | 0 |
| gate: passed / revised / flagged / declined | 61 / 5 / 2 / 0 | 65 / 2 / 0 / 1 |

- **The one wrong answer, w1-002, was a gate false positive.** The draft wrote "PVTR 43/44", which the checker read
  as one invented ID, and the gate declined it. The answer was correct in r12a and r12b. #73 fixes this: replayed
  on the real index, the stored draft and revision pass. So does r12a's hand-05 decline (clause numbers, #71).
- **Grade changes across the three r12 runs** (r12a, r12b on 88a0b10, r12):
  - better: fs-016, fs-034, hand-15 partial → correct;
  - worse: fs-019 correct → partial;
  - unstable from run to run: fs-018, fs-021, hand-11, hand-18, hand-19, w1-003.
  - fs-021 was wrong in r12b. The agent made one search with an empty query, never searched NASA-STD-7001C, and
    then claimed a coverage gap. It is correct again in r12.
- **Ungrounded numbers 0.14:** 9 answers, mostly single small integers (counts of tests or axes, "100" as in
  percent) and the table answer fs-033. In fs-033 the scorer finds one value from ECSS-E-HB-32-26A Table 9-1
  (a `checked` table) given without its check flag, and the gate passed it. That gate miss is a follow-up.
- **r11's per-question answers are not kept** (`eval/runs/r11-cli-agent` no longer exists). Comparisons use r11's
  summary above and the three r12 runs (r12a, r12b and r12 are kept, all gitignored).

## Run 11 and answers — 11–12 October 2026 — round 4 (parser fixes, 23 verified, gate fix)

Code: main after round 4 (#54–#64): table fixes H16/H17, NASA italic/subscript lines, citation-gate follow-up (#55:
flag in the next sentence or after `;` in brackets, clause numbers and tag ranges are not values, `flagged` instead of
declining when only the flag is missing), fs-024 / fs-033 references (#63). Corpus: 44 loaded documents, 23 verified,
18 checked, 3 unchecked (eval/CORPUS_HEALTH_WAVE1.md; ECSS-E-ST-10-03C drops to `unchecked`: ragged tables 2 of 14).

**Retrieval (run 11, BM25):** no regression. fs-033 is now a table question (23 table questions); fs-024 expects
ECSS-E-ST-32-10C Table 4-3 too.

| Subset | Questions | recall@5 | with `--neighbours` | recall@20 | table row hit / reachable @5 | @20 |
| --- | --- | --- | --- | --- | --- | --- |
| old 46 (run 10) | 46 | 0.63 | 0.75 | 0.88 | 0.50 / 0.85 (10) | 0.55 / 1.00 |
| old 46 (run 11) | 46 | 0.63 | 0.75 | 0.88 | 0.50 / 0.85 (10) | 0.55 / 0.95 |
| all (run 10) | 63 | 0.65 | 0.76 | 0.88 | 0.41 / 0.66 (22) | 0.43 / 0.75 |
| **all (run 11)** | 63 | **0.65** | **0.76** | **0.88** | **0.37 / 0.63 (23)** | 0.41 / 0.70 |

- Per question, only tables moved: hand-17 row hit 1.0 → 0.5 (ECSS-E-ST-10-03C Tables 5-2 / 6-2 changed shape;
  both still reachable), fs-024's added Table 4-3 is not reached (@20 reachable 1.0 → 0.5), fs-033 (new) not reached.
- Still unreached at k = 5: NASA-STD-7001C Table 1 (fs-021, w1-001, w1-003) and NASA-STD-7003A Table 1 (hand-18,
  w1-010): these tables have no owner record, so their rows are never indexed (32 of 268 tables in the corpus).
  NASA-STD-5020B Table 3 (fs-034) and ECSS-E-ST-33-01C Table 4-2 (hand-20) have owners and are ranking misses.

**Answers (`cli-agent`, Sonnet 5.5, `--judge cli`, 68 questions; `eval/runs/r11-cli-agent`, gitignored):**

| Measure | r10 `cli-agent` (B8) | **r11 `cli-agent`** |
| --- | --- | --- |
| judge: correct / partial / wrong | 0.76 / 0.19 / 0.04 | **0.82 / 0.16 / 0.01** |
| answer-point coverage | 0.91 | 0.94 |
| citation recall (expected IDs) | 0.90 (63) | 0.89 (63) |
| table citation recall | 0.80 (22) | 0.78 (23) |
| invented IDs | 0.00 | 0.00 |
| ungrounded numbers (covered) | 0.13 | 0.11 |
| not covered: declines, no numbers | 1.00 | 1.00 (4) |
| covered: declines wrongly | 3 questions | 0 |
| gate: passed / revised / flagged / declined | — | 61 / 5 / 2 / 0 |

- The three wrong declines are gone: fs-027 wrong → correct, w1-005 wrong → correct, fs-034 wrong → partial.
  fs-024 and fs-033 (new references) partial → correct, fs-019 partial → correct.
- One loss: fs-016 correct → wrong. The gate passed it; the agent made one search and answered from the
  neighbouring safe-life clause instead of the reduced-programme clause (run-to-run variance, not the gate).
- The stored B8 answers re-checked with the new checker: all four declined revisions pass; `cli` answers with an
  ungrounded number 0.11 → 0.05 (the rest are unflagged table values). fs-024 / fs-033 with `--backend cli`
  (r11-fs024-033-cli): both correct.

## Answers — 10 October 2026 — B8: wave 1, 68 questions, `cli` and `cli-agent`

Code: main at the round-3 close (parser fixes H8–H17, 15 verified standards), 44 loaded documents, BM25 with
neighbours. `run_answer_eval.py generate --backend cli` (plain client: MCP tools + server instructions) and
`--backend cli-agent` (the same plus the citation gate), both answered by a logged-in Claude Code (Sonnet 5.5), judged
with `score --judge cli` (a separate judge session). No `ANTHROPIC_API_KEY`, so the `agent` vs `api` pair is still open.
A session limit cut both generate runs at fs-032 / fs-033; the 17 / 16 failed answers were regenerated and every
answer re-judged (0 errors left). Answers stay in `eval/runs/r10-cli*` (gitignored).

| Measure | cli-bm25 (run 9 set, 57) | r10 `cli` (68) | r10 `cli-agent` (68) |
| --- | --- | --- | --- |
| judge: correct / partial / wrong | 0.91 / 0.07 / 0.02 | 0.85 / 0.12 / 0.03 | 0.76 / 0.19 / 0.04 |
| answer-point coverage | 0.97 | 0.95 | 0.91 |
| citation recall (expected IDs) | 0.96 (46) | 0.92 (63) | 0.90 (63) |
| table citation recall | 1.00 (10) | 0.80 (22) | 0.80 (22) |
| invented IDs | 0.00 | 0.00 | 0.00 |
| ungrounded numbers (covered) | 0.09 | 0.21 | 0.13 |
| not covered: declines, no numbers | 1.00 (11) | 0.60 (5) | 0.80 (5) |
| gate: revised / declined | – | – | 0.12 / 0.06 |

Same 57 questions as cli-bm25 (six of them rewritten in round 2): `cli` 48 / 7 / 2 (was 52 / 4 / 1), `cli-agent`
44 / 11 / 2; the 11 new w1 questions: `cli` 10 / 1 / 0, `cli-agent` 8 / 2 / 1. One run each, so a few verdicts are
judge noise.

Hand review of the failures:

- **fs-024 (`cli` wrong) is a stale reference, not a wrong answer.** The answer gives the glass and ceramic rows of
  ECSS-E-ST-32-10C Table 4-3 (2,5 / 3,0 / 5,0), which exist; the reference was written when only ECSS-E-ST-32C was
  considered ("no factor table"). Owner to decide whether to widen the reference (👤).
- **fs-022 (`cli` wrong)** says ECSS-E-ST-32 gives no scatter factor; 4.5.18a / 4.6.2.8c do. A real answer error.
- **The gate over-declines.** `cli-agent` is wrong on fs-027, fs-034 and w1-005 because a revision ended in "not
  covered" for questions the loaded standards answer; 4 of its 6 % declines are wrong. Before relying on the agent,
  the gate's decline path needs a look (does an unflagged-number failure push it to decline?).
- **Unflagged table numbers.** Most `cli` ungrounded numbers are table values below `verified` given without the A3
  flag ("check against the source, page N"), e.g. w1-005, w1-002, fs-034, hand-20; the gate fixes most of them
  (0.21 → 0.13). The rest are false positives of the number check (`100` as in per cent, `1`, clause numbers
  `4.4`, `10.2`).
- **Not covered.** Only 5 not-covered questions remain after wave 1. fs-033's `cli` answer gives a spectrum from
  NASA-STD-7001C / E-HB-32-26A Table 9-1 (judged partial): wave 1 may now cover part of it, so the question needs an
  owner look too.
- Partials cluster where retrieval misses (fs-009, fs-018, hand-04, hand-05, hand-07; run 10 list).

## Run 10 — 10 October 2026 — wave 1, 63 scored questions (B6)

Code: main at d2b43f7 (no search change since the round-1 check). Corpus: 44 loaded documents (wave 1 plus
NASA-STD-7003A and NASA-HDBK-7005): 15 verified, 27 checked, 2 unchecked (eval/CORPUS_HEALTH_WAVE1.md). 68 questions,
63 scored. "Old" = the 46 questions scored before 10 Oct round 2; "new" = the other 17 (w1-001…w1-011 and the six
rewritten ones: fs-021, fs-034, hand-17…hand-20). The three `run_retrieval_eval.py --docs documents` runs (default k,
`--neighbours`, `--k 20`) took about 5 s each on the warm parse cache; the split below comes from a throwaway script
(not committed) that applies the same scoring per question.

| Subset | Questions | recall@5 | with `--neighbours` | recall@20 | table row hit / reachable (table questions) |
| --- | --- | --- | --- | --- | --- |
| old 46 | 46 | 0.63 | 0.75 | 0.88 | 0.50 / 0.85 (10) |
| new 17 | 17 | 0.71 | 0.78 | 0.90 | 0.33 / 0.50 (12) |
| **all 63** | 63 | **0.65** | **0.76** | **0.88** | **0.41 / 0.66 (22)** (@20: 0.43 / 0.75) |

- **No regression on the old 46:** identical to the round-1 check (0.63, 0.75, 0.50 / 0.85). The 63-question
  figures equal the preview (0.65, 0.41 / 0.66). Fixture eval recall@5 1.00.
- **The new questions are not easier.** Their recall@5 is higher (0.71), but table reachability is low (0.50): the
  new table questions point at NASA-STD-7001C Table 1 (fs-021, w1-001, w1-003), NASA-STD-7003A Table 1 (hand-18,
  w1-010), NASA-STD-5020B Table 3 (fs-034) and ECSS-E-ST-33-01C Table 4-2 (hand-20); none is reached in the top 5.
- **Misses at k = 5** (expected ID, rank in the full ranking; 31 questions, 24 with neighbours, 11 at k = 20):
  - old, as before: fs-006 (NASA-STD-5001B FSR 53: 16, FSR 55: 17), fs-008 (ECSS-E-ST-32-01C 11.2.2.1a: 17), fs-009
    (6.3.2c: 12, 7.2.8c: 133), fs-012 (6.3.5.2a: 15, 6.3.5.2b: 7), fs-013 (8.4.4.2g: 6), fs-017 (ECSS-E-ST-32-08C
    4.4.1a: 7), fs-018 (4.5.2a: 6, 4.5.2c: 10), fs-019 (ECSS-E-ST-32-01C 6.3.2c: 50, 6.3.2e: 42, 6.3.3e: 12),
    fs-020 (ECSS-E-ST-32-10C 4.1.5.3a: 13, 4.3.2.1a: 9; Table 4-3), fs-024 (FSR 32: 7; Table 3), fs-026 (6.2.2a: 6),
    fs-027 (6.3.3b: 16, 6.3.3c: 26, NASA-STD-5019A FCR 8 / 6.2.3.a: 15), fs-030 (ECSS-Q-ST-70C 5.1.12a: 32), hand-03
    (4.1.4.1a: 9), hand-04 (4.1.5.2a: 8), hand-05 (ECSS-E-ST-32C I.2.1<13.1>a: 33, <13.3>a: 37), hand-07
    (4.6.2.2b: 19), hand-08 (ECSS-E-ST-32-01C 10.7.1b: 7), hand-09 (FCR 12 / 7.3.2.c: 24), hand-10 (FCR 8 / 6.2.2: 15),
    hand-11 (FCR 18: 6), hand-12 (ECSS-E-ST-32-01C 8.3.2e: 20, FCR 16: 13), hand-13 (8.8f: 46, FCR 11 / 7.2.8.c: 31),
    hand-16 (ECSS-E-ST-32C 4.5.12a and 4.6.2.12a: not in the restricted ranking; both are in `elsewhere`).
  - new: fs-021 (NASA-STD-7001C PVTR 2: 80, PVTR 43: 38; Table 1), fs-034 (NASA-STD-5020B TFSR 7: 15; Table 3),
    hand-18 (NASA-STD-7003A 4.3.1.1: 18, 4.3.2: 9; Table 1), hand-19 (NASA-STD-5020B 4.2.2 guidance 10: 8, 4.2.3
    guidance 3: 13, TFSR 10: 7, TFSR 4: 9), hand-20 (ECSS-E-ST-33-01C 4.7.5.3.1b: 64, 4.7.5.3.1d: 6; Table 4-2),
    w1-001 (PVTR 2: 8, PVTR 43: 20; Table 1), w1-009 (NASA-STD-5002B LAR 2: 40); table only: w1-003 (7001C Table 1),
    w1-010 (7003A Table 1).
  - hand-11 stays at rank 6 (round-1 check); at k = 20 only 11 questions still miss: fs-009, fs-019, fs-021, hand-05,
    hand-09, hand-13, hand-16, hand-20, fs-027, fs-030, w1-009.

### Dilution diagnostic (for B7)

Method (throwaway script): for the 58 scored questions whose text names a loaded document (114 expected IDs), the
rank of each expected ID in three rankings. **Full**: the normal search (restricted to the named documents, corpus-wide
BM25 statistics). **Oracle**: `--oracle-doc` logic (restricted to the expected documents, interleaved). **Per-doc**:
a separate index built from only the named documents, so IDF and average length are per document. Rankings and ranks
are over the whole restricted document, not just the top k.

- Full and oracle ranks are the same for almost every ID (differences of 1 where a second document is involved), so
  document choice is not what loses recall: the named-document restriction already picks the right documents.
- Per-doc against full, over 112 IDs found in both: 30 rank better, 39 worse, 43 equal; the median rank ratio is 1.0.
  Into the top 5: fs-012 6.3.5.2b 7 → 4, hand-11 FCR 18 6 → 2, hand-12 FCR 16 13 → 5, hand-19 4.2.2 guidance 10
  8 → 1, w1-001 PVTR 2 8 → 4. Out of the top 5: fs-002 FSR 14 5 → 7, fs-007 FSR 16 3 → 15, fs-009 6.3.2b 4 → 9,
  fs-012 6.3.5.2c 5 → 6, hand-18 NASA-STD-7003A 4.3.1 2 → 11. Largest gains in the long tail: hand-13 8.8f 46 → 28,
  hand-20 4.7.5.3.1b 64 → 51, w1-009 LAR 2 40 → 28, hand-12 8.3.2e 20 → 10. Largest losses: hand-18 4.3.1 2 → 11,
  fs-007 FSR 16 3 → 15, fs-019 6.3.2c 50 → 84.
- Verdict: **no systematic dilution.** Per-document statistics move ranks both ways, and the five questions
  they would rescue are balanced by five they would lose; none of the 31 misses is explained by corpus-wide IDF. The
  misses are within-document ranking (long, split or low-overlap records; tables not reached by their requirements),
  as in runs 8 and 9. **B7 (two-stage retrieval) is not needed on these numbers.** Per-document IDF would only
  remove the rank-6 sensitivity of hand-11 and similar one-position swaps. The open retrieval problems are table
  reachability for the new table questions and hand-16 (named ECSS-E-ST-32C annex records not retrieved).

## Check — 10 October 2026 — round 1: tier flags (A3), handbook sections (A5), new thresholds

44 loaded documents (wave 1 + NASA-STD-7003A, NASA-HDBK-7005). `run_retrieval_eval.py --docs documents` on the
46 scored questions:

| Code | recall@5 | with `--neighbours` | recall@20 | table row hit / reachable |
| --- | --- | --- | --- | --- |
| before round 1 (3729af2, 44 documents) | 0.65 | 0.76 | – | 0.50 / 0.85 |
| round 1 merged (A3, A5, handbook fix) | 0.63 | 0.75 | 0.87 | 0.50 / 0.85 |

One question differs: hand-11 (`NASA-STD-5019A|FCR 18`) moves from rank 5 to 6, behind FCR 15, by about 2 %
of score. The search is restricted to 5019A; the swap comes from corpus-wide BM25 statistics (IDF, average
length) shifting when thousands of handbook section records join the index. Leaving the handbooks out, or
weighting them 0 or 0.6, gives the same 0.63, so handbook records do not outrank standard records. hand-11 also
flipped the other way when wave 1 was loaded (B1 check). B6 (run 10) measures this with the B5 questions;
per-document IDF or two-stage retrieval (B7) would remove the sensitivity. Fixture eval recall@5 1.00.
Real-document pytest 243 passed.

## Check — 9 October 2026 — text audit paraphrases (C4; no search change)

Three `reference_answer`s (fs-009, fs-011, fs-016) were reworded so that no run of 12 words matches
ECSS-E-ST-32-01C ([TEXT_AUDIT.md](TEXT_AUDIT.md)); questions, expected IDs, numbers and answer points are
unchanged. `run_retrieval_eval.py --docs documents` (42 loaded documents): recall@5 0.65 over 46 questions,
table row hit 0.50, reachable 0.85, as in the B1 check. Fixture eval recall@5 1.00.

## Check — 9 October 2026 — wave 1 loaded (B1; no search change, not run 10)

`documents/corpus.yaml` now loads the 7 verified standards plus 35 wave-1 documents (ECSS-E-ST-32-*,
E-ST-33-01C, E-ST-10-03C, E-HB-32-*, NASA-STD/HDBK/SPEC-50*, NASA-STD-7001/7002). Re-ran
`run_retrieval_eval.py --docs documents` on the existing 46 questions, none of which cites a wave-1 document:

| Corpus | recall@5 | with `--neighbours` | table row hit / reachable |
| --- | --- | --- | --- |
| 7 verified (B4a check) | 0.64 | 0.74 | 0.50 / 0.85 |
| + wave 1 (42 documents) | 0.65 | 0.76 | 0.50 / 0.85 |

Per question: hand-11 0.00 → 1.00, fs-017 1.00 → 0.67 (`ECSS-E-ST-32-08C|4.4.1a` to rank 6); other misses
moved a few ranks either way (fs-030 rank 6 → 14, hand-12 rank 7/10 → 13/14, hand-13 22/27 → 32/29; fs-026
12 → 7). Small net change because most wave-1 handbooks give few records yet (H6 in
`docs/PARSING_NOTES.md`); the dilution test proper is B6 (run 10) with the B5 questions. Health report for the
loaded set: [CORPUS_HEALTH_WAVE1.md](CORPUS_HEALTH_WAVE1.md), 42 documents, 7 verified, 24 checked,
11 unchecked, 0 parse errors. Numbers are with H1 and A4 merged (same recall; hand-09 rank 22 → 21).

## Check — 9 October 2026 — ECSS-E-ST-32-10C Rev.2 Corr.1 loaded (B4a; no search change)

Re-ran `run_retrieval_eval.py --docs documents` with the Corr.1 PDF in place of Rev.2 (same 28 requirement IDs,
texts and pages; machine IDs on 4.3.2.1e / 4.3.2.2b; one Table 4-4 cell printed once). Same numbers as run 9:
recall@5 0.64 over 46 questions (0.74 with `--neighbours`), table row hit 0.50, reachable 0.85. Not a new run
number. The A2 re-run with the H2–H4 fixes is in [CORPUS_HEALTH.md](CORPUS_HEALTH.md): 284 documents, 7 verified,
146 checked, 131 unchecked, 0 parse errors (was 129 / 148).

## Check — 9 October 2026 — after the A2 health report (no search change)

Re-ran `run_retrieval_eval.py --docs documents` on `main` + the A2 branch (the loaded set is unchanged, the
health report only reads). Same numbers as run 8 and run 9's baseline: recall@5 0.64 over 46 questions, table
row hit 0.50, reachable 0.85. Not a new run number. The health report itself is in
[CORPUS_HEALTH.md](CORPUS_HEALTH.md): 284 documents, 7 verified, 129 checked, 148 unchecked, 0 parse errors.

## Run 9 — 8 October 2026 — neighbouring records shown with each hit

Same 46 scored questions. Each search hit now carries `neighbours`: the records directly before and after it in the
same clause (`NEIGHBOURS = 1`; deleted placeholders skipped), as full records with citations, unless another hit
already shows them. The ranking is unchanged, so this is scored with `run_retrieval_eval.py --neighbours`: an expected
ID counts as found when it is a top-5 hit or a neighbour of one.

| Variant | recall@5 | v1 @5 | hand @5 | v2 @5 | median / max response (bytes) |
| --- | --- | --- | --- | --- | --- |
| BM25 | 0.637 | 0.754 | 0.438 | 0.725 | 4,353 / 8,682 |
| **BM25 + neighbours (default)** | **0.743** | **0.846** | **0.594** | 0.775 | 6,748 / 15,794 |
| BM25 + neighbours, window 2 | 0.766 | | | | 7,923 / 23,152 |
| hybrid (weight 2) | 0.687 | 0.792 | 0.469 | 0.825 | |
| hybrid + neighbours | 0.732 | 0.809 | 0.562 | 0.850 | |

- **+0.11 recall@5 with no losses.** Gained at k = 5: fs-009 (6.3.2c), fs-012 (6.3.5.2b), fs-013, fs-018, hand-04,
  hand-07, hand-08, hand-13 (8.8f), and fs-027 0.25 → 0.75. The ranking does not change, so no question can get
  worse. Most of the misses this fixes are requirements split over sibling letters, where one letter shares no
  word with the question.
- **fs-027 is mostly fixed.** 6.3.3d ranks 2nd and shows 6.3.3c (no fragment release, rank 36). NASA FCR 8 / 6.2.3
  shows FCR 8 / 6.2.3.a. 6.3.3b (remaining structure, limit loads × 1.0 / 1.15) is still missing at rank 16.
- **fs-016 is not a neighbour problem.** The question itself puts 11.2.2.6a at rank 4. The answer runs missed it
  because the client's own query ("initial crack size low-risk safe-life metallic parts reduced fracture control",
  filtered to 32-01) ranks it 11th: the 1,433-character record is length-penalised, and only its heading
  ("11 Reduced fracture control programme") says "reduced". A heading-match bonus (idf of query words found in the
  heading path) was tried. It lifts recall@5 to 0.69–0.71 at weights 0.5–1, but it loses fs-009 and hand-03, and
  it moves 11.2.2.6a only to rank 8–16 for that query. Not adopted. A separate tuning question.
- **Window 1 is the default.** Window 2 adds 0.02 recall for 17 % more bytes, and up to 23 KB per response.
- **Hybrid gains less from neighbours** (+0.045) than BM25 does (+0.106), and ends below BM25 + neighbours. BM25
  stays the default.
- Answer-level effect not measured yet: it needs a new `cli` run (fs-016 is unaffected; fs-027 and the partials
  from run 1 are where to look).

## Scripted answer run 2 — 8 October 2026 — the agent's citation gate around the same client

`generate --backend cli-agent`: the same `claude -p` client as run 1 (Sonnet 5.5, BM25, MCP tools only), with the
ADR-0005 gate. Each draft is checked against the records the tools returned. Invented IDs or ungrounded numbers
get one revision in the same session; if the revision still fails, the agent declines. It was judged like run 1
(Opus 5.5) and scored with the checker as of this run, so the run-1 column below was re-scored with it.
`--backend agent` against `api` (Messages API loop) needs `ANTHROPIC_API_KEY` and was not run. See the ADR-0005
addendum.

| Metric | plain client (run 1, BM25) | gated client |
| --- | --- | --- |
| judge: correct / partial / wrong | 52 / 4 / 1 | 49 / 7 / 1 |
| judge: answer-point coverage | 0.97 | 0.96 |
| citation recall (46) / table citation recall (10) | 0.96 / 1.00 | 0.94 / 1.00 |
| invented IDs (checker) | 0 | 0 |
| ungrounded numbers, covered (checker; all false positives after review) | 4 | 2 |
| not covered: declines, no numbers | 11 / 11 | 11 / 11 |
| gate: passed / revised / declined | — | 53 / 4 / 0 |
| tool calls per answer | 3.4 | 3.5 |

- **The gate changed 4 of 57 answers, and all 4 are judged correct.** fs-014 wrote "100 %" where 32-01 8.4.4.3c
  says "all". This is the same slip as hybrid run 1, by the same model, so it recurs. The gate caught it and the
  revision removed it. In fs-017, fs-024 and fs-031 the flagged numbers were clause or table references ("4.5",
  "36"), and the revision rewrote them as "clause 4.5" (the revision prompt asks for this).
- **The quality difference is sampling, not the gate.** All 5 answers whose verdict differs from run 1 (fs-007,
  fs-018, fs-019, fs-020, fs-027) passed the gate unchanged. With one run of each, 52 against 49 correct is
  within noise. The one wrong answer is fs-016 again: the reduced-programme clause 11.2.2.6a was not retrieved
  (a retrieval miss, see run 1).
- **First pass: 3 declines, now 0.** In the first generation the gate declined fs-014, hand-05 and hand-12.
  - fs-014: the same "100 %" slip, which survived the revision.
  - hand-05: a checker false positive. "I.2.1<13>", a DRD clause, was read as the number 13; the checker is now
    fixed.
  - hand-12: the draft named a clause that does not exist ("8.3.2h onward").

  The gate record did not yet keep the revised draft, so it was added (`revision`, `revision_problems`) and the
  three were re-generated. fs-014 was then revised successfully, and hand-05 and hand-12 passed. The first-pass
  answers are kept in `eval/runs/cli-agent-bm25/answers.first.jsonl`.
- **What the gate is worth here.** The client already follows the grounding rules, so the gate rarely acts: 4 of
  57 answers, at the cost of one resumed turn each. It turns the one real slip into a corrected answer. Its risk
  is wrong declines from checker false positives (1 in 57 on the first pass). Every new checker rule needs a
  regression case, as hand-05 showed.

## Scripted answer run 1 — 8 October 2026 — off-the-shelf client, BM25 vs hybrid, independent judge

`generate --backend cli`: `claude -p` (Sonnet 5.5) with the space-standards MCP server and nothing else. There
is no project CLAUDE.md, and only the MCP tools plus `ANSWER_SYSTEM` are available. All 57 questions were run
twice: BM25 (default) and hybrid (`SPACESTD_EMBED=default`, dense weight 2, see run 8).
`score --judge cli --judge-model claude-opus-5-5`: the judge is a different model from the one that answered
(Phase 2 finding 3). Answers are in `eval/runs/cli-bm25/` and `eval/runs/cli-hybrid/` (gitignored). Every
checker flag was reviewed by hand (Phase 2 finding 4), and the table shows both counts.

| Metric | BM25 | hybrid | Phase 2 baseline (in-session, self-judged) |
| --- | --- | --- | --- |
| judge: correct / partial / wrong | 52 / 4 / 1 | 49 / 8 / 0 | 53 / 4 / 0 |
| judge: answer-point coverage | 0.97 | 0.96 | 0.97 |
| citation recall (46) / table citation recall (10) | 0.96 / 1.00 | 0.98 / 1.00 | 0.97 / 1.00 |
| invented IDs: checker / after hand review | 0 / 0 | 2 / 0 | 0 |
| ungrounded numbers, covered: checker / after hand review | 8 / 0 | 5 / 1 | 0 |
| not covered, clean decline: checker / after hand review | 10 / 11 of 11 | 9 / 11 of 11 | 11 |
| tool calls per answer | 3.4 | 3.7 | 1.8 |

Verdicts by type (correct/partial/wrong). BM25: classification 7/0/0; compare 5/0/0; lookup 16/1/0;
not_covered 10/1/0; numeric 14/2/1. Hybrid: 7/0/0; 4/1/0; 15/2/0; 10/1/0; 13/4/0.

- **The scripted off-the-shelf client matches the Phase 2 baseline.** A different, smaller model answered, and an
  independent judge graded it: 52 correct, against 53 in-session. The grounding rules hold: after review there
  are no invented IDs and no ungrounded numbers with BM25, and all 11 not-covered questions are declined without
  values. The four that ask about a standard that is not loaded name it (ECSS-E-ST-10-03, NASA-STD-7003,
  NASA-STD-5020, ECSS-E-ST-33-01). The client uses more tool calls than the in-session baseline (3.4 against 1.8).
- **The one wrong answer is a retrieval miss.** BM25 fs-016: the model's query never surfaced 32-01 11.2.2.6a
  (reduced fracture control programme). It gave the standard-programme initial crack sizes from 6.3.5.x instead.
  The numbers are grounded, but they answer a different programme. Hybrid retrieved 11.2.2.6a and answered it
  correctly.
- **Hybrid does not help at answer level.** It has 3 fewer correct answers, and fs-007 is partial because of the
  run-8 retrieval loss: FSR 15 and FSR 16 were cited, but the points that the no-test option is metallic-only
  and that higher factors alone are not sufficient were missed. Its other extra partials (fs-004, fs-019, fs-020)
  are small omissions. With one run of each, a difference of three answers is within judge and sampling noise.
  So hybrid stays opt-in.
- **One real grounding slip (hybrid fs-014).** The cited 32-01 8.4.4.3c gives no percentage (it says "all"), but
  the answer wrote close visual testing of "100 %" of the item before each flight. This is the kind of number the agent's gate should catch.
- **Checker fixes from the hand review** (`src/spacestd/citations.py`, `index.py`; tests added). All of these
  were false positives:
  - A NASA clause written next to its tag ("FSR 13 (requirement, 4.1.2.2a)") was flagged as invented in 4 BM25
    answers. The index now also finds a record by its clause when exactly one record in the document has that
    clause, so `get_requirement` accepts "4.1.2.2a" too.
  - "the Table 9-1 values in ECSS-Q-ST-70-15" is now external. Up to two words may now stand between the ID and
    "of / in / from / per".
  - Declines written with contractions ("don't give", "isn't loaded", "isn't one of the loaded") were not detected
    in 9 of the 11 answers.
- **Flags still left after the fixes, all false positives except fs-014:** bare clause numbers in prose
  ("section, 4.5", "(4.4)"); table ranges ("Tables 1–7", "Tables 4-3 to 4-6"); shorthand standard names
  ("32-08C, 32-10C"); a numbered list heading; a clause cited without its letter ("clause 8.4.4.3" for 8.4.4.3f,
  hybrid fs-012); "Table 9-1 … it belongs to ECSS-Q-ST-70-15" (hybrid hand-08); and fs-017 saying correctly that
  "4.4.4b returned nothing". The checker rates are therefore pessimistic. They are a screen for hand review,
  not a final score.
- **Still to do:** `generate --backend agent` against `--backend api` needs `ANTHROPIC_API_KEY`, which this machine
  does not have. The agent's loop is the API loop (ADR-0005), so it cannot run through `claude -p`.

## Answer baseline (in-session, Claude Code + MCP tools) — 8 October 2026

**Not a scripted run.** `generate` was not used (no API key or CLI login was available). In one Claude Code
session (Opus 5.5), the 57 questions were answered through the space-standards MCP tools only
(`search_requirements`, `get_requirement`, `get_table`), the way a client would. The answering was blind: only
the `id | question` lines were read from `eval/questions.yaml`; that file, `REVIEW.md` and `HAND_TEST.md` were
opened only after `answers.jsonl` was complete. The same session then graded each answer point with the
`JUDGE_PROMPT` rubric. That makes the judge the same model that answered, so treat the verdicts as optimistic.
`tool_calls` are the calls the session logged per question, and several calls were reused across neighbouring
questions, so 1.8 understates the real retrieval effort. Answers and scores are in `eval/runs/baseline/`
(gitignored).

`python eval/run_answer_eval.py score --run eval/runs/baseline --judge none --markdown` (judge grades written
into `scores.json` by hand, kept because the answer hashes match):

| Metric | Value | n |
| --- | --- | --- |
| judge: correct | 0.93 | 57 |
| judge: partial | 0.07 | 57 |
| judge: wrong | 0.00 | 57 |
| judge: answer-point coverage | 0.97 | 57 |
| citation recall (expected IDs cited) | 0.97 | 46 |
| table citation recall | 1.00 | 10 |
| answers with an invented ID | 0.00 (0.04 before the checker fix) | 57 |
| answers with an ungrounded number (covered) | 0.00 (0.09 before the checker fix) | 46 |
| not covered: declines, no numbers | 1.00 | 11 |
| covered: declines wrongly (cites nothing) | 0.00 | 46 |
| tool calls per answer | 1.8 | 57 |

Verdicts by type (correct/partial/wrong): classification 7/0/0; compare 4/1/0; lookup 15/2/0; not_covered
11/0/0; numeric 16/1/0.

- **Partials (4), all retrieval misses, no wrong statements:** fs-009 (32-01 7.2.8c, "spectrum applied 4 times",
  never surfaced); fs-027 (32-01 6.3.3c, no fragment release, which is the known rank-36 retrieval miss from run 7);
  hand-08 (32-01 10.7.1b, customer approval, not retrieved); fs-007 (missed the guidance point that higher factors
  alone do not justify no-test). Missing citations: 7.2.8c, 6.3.2e (fs-019, where 6.3.3f was cited for the same
  composite point), 10.7.1b, 6.3.3c.
- **Checker fix (same day, `src/spacestd/citations.py`):** the first scoring flagged 2 invented IDs and 4 ungrounded
  numbers, and all 6 were false positives.
  - NASA guidance records ("NASA-STD-5001B …, 4.1.1 guidance 3") are now parsed as citations. Before, their numbers
    (0.65, 16-01) and the "3" in "guidance 3" counted as ungrounded (fs-002, fs-003, fs-006, fs-007).
  - An ID attached to a standard that is not loaded ("Table 9-1 of ECSS-Q-ST-70-15", "ECSS-Q-ST-70-71 … 4.3.10c") is
    now *external*: it cannot be checked, so it is neither resolved nor invented (hand-08, fs-029). This also stops a
    silent mis-attribution: "ECSS-Q-ST-70-36 Table 5-1" used to be credited to ECSS-Q-ST-70C's own Table 5-1
    (fs-012, fs-015, fs-016, hand-14).
  - Citation recall and the CI demo (one planted invented ID, one wrong number) are unchanged.
- Not-covered questions: all 11 decline and state no values. Where the search reported `not_loaded`, the answer
  names the missing standard.

## Answer eval — method (7 October 2026)

`eval/run_answer_eval.py` answers each question through the MCP tools (`generate`: Anthropic API with the
tools in-process, or `claude -p` with the MCP server as an off-the-shelf client), then scores the answers
(`score`). Answers stay in the gitignored `eval/runs/`; only summaries go here.

Deterministic checks (`src/spacestd/citations.py`, tests in `tests/test_citations.py`):

- **invented IDs**: requirement IDs (ECSS clause + letter, DRD IDs, NASA-style tags) and `Table n` references
  that exist in no loaded document. Each ID is attributed to the nearest standard named before it, else to
  the one loaded document that has it;
- **citation recall**: share of `expected_ids` (and `expected_tables`) the answer cites;
- **ungrounded numbers**: numbers in the answer (outside IDs, standard names and clause references) that
  appear neither in the question nor in the records or tables the answer cites;
- **not covered**: the answer says the loaded standards do not cover it and states no ungrounded number.

LLM judge (Claude, model set with `--judge-model`): each answer point yes / partial / no against the reference
answer, factual errors, and a verdict correct / partial / wrong.

**Scripted run (optional, for Phase 3 comparisons):** at the time, this machine has no `ANTHROPIC_API_KEY` and the `claude` CLI login had expired.
The baseline above was produced in-session instead. To run it scripted, with an independent judge:

```
pip install -e ".[eval]"            # anthropic SDK, for --backend api / --judge api
python eval/run_answer_eval.py generate --run eval/runs/baseline --backend api
python eval/run_answer_eval.py score --run eval/runs/baseline --judge api --markdown
```

CI scores five invented demo answers (`eval/demo_answers.jsonl`, `--judge none`), which plant one invented ID
and one wrong number.

## Run 8 — 8 October 2026 — hybrid search and reranking measured

Same 46 scored questions as run 7. Hybrid = BM25 + `BAAI/bge-small-en-v1.5` fused by RRF; rerank =
`Xenova/ms-marco-MiniLM-L-6-v2` over the hybrid top 30. Groups: v1 = `fs-001`…`fs-021` (21), hand = `hand-*`
(15 scored), v2 = `fs-022`…`fs-037` (10 scored).

| Variant | recall@5 | recall@20 | v1 @5 | hand @5 | v2 @5 | tables @5 row hit / reachable |
| --- | --- | --- | --- | --- | --- | --- |
| BM25 (default) | 0.637 | 0.890 | 0.754 | 0.438 | 0.725 | 0.50 / 0.85 |
| hybrid, weight 0.25 | 0.637 | 0.911 | 0.754 | 0.438 | 0.725 | 0.70 / 0.85 |
| hybrid, weight 0.5 | 0.623 | 0.906 | 0.746 | 0.406 | 0.725 | 0.70 / 0.85 |
| hybrid, weight 0.75 | 0.658 | 0.895 | 0.775 | 0.469 | 0.725 | 0.75 / 0.90 |
| hybrid, weight 1 | 0.665 | 0.895 | 0.742 | 0.469 | 0.825 | 0.75 / 0.90 |
| hybrid, weight 1.5 | 0.680 | 0.895 | 0.775 | 0.469 | 0.825 | 0.75 / 0.90 |
| **hybrid, weight 2** | **0.687** | **0.895** | **0.792** | 0.469 | 0.825 | 0.75 / 0.90 |
| hybrid, weight 3 | 0.687 | 0.862 | 0.792 | 0.469 | 0.825 | 0.75 / 0.90 |
| hybrid, weight 5 | 0.671 | 0.841 | 0.792 | 0.438 | 0.800 | 0.75 / 0.90 |
| hybrid weight 1 + rerank | 0.632 | 0.890 | 0.709 | 0.500 | 0.692 | 0.55 / 0.70 |

- **Weight 2 is the best fusion.** At k = 5, against BM25, it gains fs-009, fs-012, fs-013, fs-018, fs-020, hand-03
  and fs-026, and loses fs-007 and fs-017. Weight 1 loses the same two and gains fewer. Above 2, recall@20 drops.
  `DENSE_WEIGHT` (index, `SPACESTD_DENSE_WEIGHT`, `--dense-weight`) now defaults to 2.
- **Tables gain most:** row hits at k = 5 go from 0.50 to 0.75 (fs-020's Table 4-3 row now ranks in the top 5).
- **Not made the default.** The bar was "recall@5 improves without hurting the v1 questions". v1 recall@5 rises
  (0.754 → 0.792), but fs-007 drops from 1.0 to 0.0: NASA-STD-5001B FSR 15 and FSR 16 fall to ranks 17–18 (both
  are in the top 5 with BM25). fs-017 loses ECSS-E-ST-32-08C 4.4.1a to rank 7. Hybrid stays opt-in
  (`SPACESTD_EMBED=default`) until the answer eval shows whether these two losses matter more than the gains.
- **The reranker hurts.** The MS MARCO cross-encoder lowers recall@5 (0.632) and table reachability (0.70), and pushes
  fs-027's NASA FCR 8 from rank 11 to 38. Not recommended with this model.
- **fs-027 is still unsolved.** ECSS-E-ST-32-01C 6.3.3c (no fragment release) is at rank 36 with BM25 and 70 with
  hybrid. This is not a paraphrase that embeddings bridge. It probably needs a parent/sibling expansion (6.3.3 b–c
  with 6.3.3a) rather than better ranking.

## Run 7 — 7 October 2026 — eval set grown to 57 questions; tables scored

**Questions:** 16 added (`fs-022`…`fs-037`, review pending): 10 covered (fatigue and thermal-cycling scatter
factors, glass/ceramics and fail-safe ECSS vs NASA comparisons, FCI and NHLBB classification, rotating
machinery, hydrogen embrittlement, galvanic corrosion, venting) and 6 not covered (payload clearance,
under-fairing acoustics, bolt preload scatter, MMPDS values, molecular contamination limits, lightning
waveform). The set is now 57 questions: 46 scored for retrieval, 11 not covered.

**Tables:** 10 questions carry `expected_tables`. A table counts as found when a top-k hit matched one of its
rows (*row hit*) or a top-k hit's requirement points to it (*reachable*: the client calls `get_table`).

No search change since run 6.

| Metric | 36 run-6 questions | 10 new | All 46 |
| --- | --- | --- | --- |
| recall@5 | 0.613 (unchanged) | 0.725 | 0.64 |
| recall@20 | 0.866 (unchanged) | 0.975 | 0.89 |
| recall@5, `--no-doc-detect` | — | — | 0.63 |

| Tables (10 questions) | row hit | reachable |
| --- | --- | --- |
| @5 | 0.50 | 0.85 |
| @20 | 0.55 | 1.00 |

- Table misses at k = 5: fs-020 (32-10 Table 4-3 behind 4.3.2.1a at rank 12) and fs-024 (5001B Table 3 behind
  FSR 32 at rank 7). Both are reachable at k = 20.
- New-question misses at k = 5: fs-026 (6.2.2a at rank 12), fs-027 (32-01 6.3.3c at rank 36: the
  no-fragment-release item does not share the question's words), fs-024 and fs-030 (rank 6–7).

## Run 6 — 7 October 2026 — search fixes F5/F6, eval set grown to 36 questions

**Questions:** `eval/questions.yaml` now holds the 21 v1 questions plus the 20 hand-test questions
(`hand-01`…`hand-20`, 16 scored, 4 not-covered; expected IDs checked against the source PDFs, review waived by the
domain owner). The hand-test questions are full sentences and harder for keyword search: on the run-5 code they
score recall@5 0.44 (v1 set: 0.75), so the 36-question baseline is **0.61 / 0.79** (recall@5 / @20).

**Changes** (`src/spacestd/index.py`, tests in `tests/test_search.py`):

1. **Light stemming** (F5): plural, -ing and -ed stripped ('proof testing' meets 'proof test'); words with digits or
   hyphens, short words and a few nouns ('fairing', 'bearing') are kept.
2. **Kind weight** (F5): guidance scores × 0.8 (deleted × 0.5), so explanatory text no longer outranks the requirement.
3. **`not_loaded`** (F6): standard IDs in the query that match no loaded document are reported with a note.
4. **`elsewhere`** (F6): when the named document's best match is below 0.75 × the best match in other documents
   (topic words only), the response adds the top 3 hits from the other documents. The filtered `results` are unchanged.

| Variant (36 questions) | recall@5 | recall@20 | v1 recall@5 | hand recall@5 |
| --- | --- | --- | --- | --- |
| baseline (run-5 code) | 0.611 | 0.794 | 0.750 | 0.438 |
| guidance × 0.8 | 0.625 | 0.822 | 0.750 | 0.469 |
| stemming | 0.600 | 0.852 | 0.729 | 0.438 |
| **stemming + guidance × 0.8 (adopted)** | **0.613** | **0.866** | 0.754 | 0.438 |
| stemming + guidance × 0.6 | 0.613 | 0.894 | 0.754 | 0.438 |

- recall@5 is flat (± half a question); recall@20 gains 0.07. Stemming moves the diagnosed misses up (hand-11
  FCR 18 rank 86 → 6, hand-07 45 → 18, hand-08 17 → 7, fs-002 FSR 14 15 → 5) and costs others a few places
  (fs-019 6.3.3e 4 → 10, fs-020 4.3.2.1a 6 → 12, hand-09 19 → 26). Guidance × 0.6 adds recall@20 only; 0.8 was
  kept as the milder change.
- hand-16 (names ECSS-E-ST-32-08, which has no bonding requirements) still scores 0 in the ranking, but both
  expected ECSS-E-ST-32C clauses are returned in `elsewhere`; the runner now prints that.
- `elsewhere` fires on 2 of the 36 questions (hand-16 and fs-011, whose named standard does cover the topic:
  3 extra hits, harmless). `not_loaded` fires on the four not-covered hand questions.
- `--no-doc-detect`: 0.62. Fixtures: recall@5 1.00.

Next for ranking: the remaining misses are mostly paraphrase gaps (hand-05 "checks" vs "MMDD … dedicated checks",
hand-09 "service life factor" vs "4 lifetimes") — the Phase 3 embedding/hybrid search target.

## Run 5 — 7 October 2026 — parser fixes from the hand test

Same questions and search settings as run 4. Two changes since run 4:

1. **ECSS-Q-ST-70C Rev.2 added to `documents/`** (281 records) after run 4. This alone moves recall@5 from 0.71 to
   0.75 on `main` (fs-018 0.33 → 0.67: 4.5.2c back in the top 5 as the corpus statistics change).
2. **Parser fixes** from `eval/HAND_TEST.md` (F1–F4): 5019A nested list items, 32-10 Table 4-4 sub-row labels,
   Q-ST-70C Table 5-1, subscript spacing. No requirement IDs removed; 7 lettered items now citable
   (FCR 8 / 6.2.5.b, FCR 12 / 7.3.3.a–f); 37 5019A records changed text (items moved to their owner).

| Metric | Run 4 | Run 5 (main + Q-ST-70C) | Run 5 (parser fixes) |
| --- | --- | --- | --- |
| recall@5 | 0.71 | 0.75 | 0.75 |
| recall@20 | 0.93 | — | 0.93 |
| recall@5, `--no-doc-detect` | 0.59 | — | 0.56 |

- The parser fixes do not change recall@5 on this question set; ranks of missing IDs move by at most 2
  (fs-006, fs-009, fs-012, fs-019). Their effect is on answers: the right record now carries the full item
  list (H04, H09 in the hand test), which retrieval recall does not measure — the answer-level eval in Phase 2 will.
- `--no-doc-detect` 0.59 → 0.56 comes with the extra document (more competition without the filter).

## Run 4 — 7 October 2026 — duplicate ECSS-E-ST-32-08C removed

Same questions, documents folder and search settings as run 3. Only change: document identity (`src/spacestd/loaders.py`).

Runs 1–3 indexed ECSS-E-ST-32-08C twice. Both the `.doc` and the `.docx` download are in `documents/`; the
`.docx` was identified as ECSS-S-ST-00-01, because its own number is printed once (Word page header) and the
foreword cites the glossary twice, so the most-frequent-ID rule picked the glossary. The `.doc` (no cover read,
file name used) was loaded as ECSS-E-ST-32-08C. Now a Word file's page header decides the document ID; both
files resolve to ECSS-E-ST-32-08C Rev.1 and only the `.docx` is loaded (77 records, identical to the `.doc` parse).

| Metric | Run 3 | Run 4 |
| --- | --- | --- |
| recall@5 | 0.72 | 0.71 |
| recall@20 | 0.93 | 0.93 |
| recall@5, `--no-doc-detect` | 0.59 | 0.59 |

- **fs-018** 0.67 → 0.33: 4.5.2c moves from rank 5 to 6. The record text is unchanged; removing 77 duplicate
  records changed the BM25 corpus statistics (IDF, average length). Runs 1–3 were scored on the duplicated corpus,
  so run 4 is the baseline to compare against from now on.
- Other questions: ranks of missing IDs move by at most 2; no other change at k = 5 or k = 20.

## Run 3 — 7 October 2026 — BM25 b = 0.5

Questions: `eval/questions.yaml` v1, domain-reviewed (all 21 ok) — runs 1–3 used the same, unchanged questions.

Only change: BM25 `b` 0.75 → 0.5 (`k1` stays 1.2), to stop over-penalising long ECSS clauses (run 2 regressions).

| Metric | Run 2 | Run 3 |
| --- | --- | --- |
| recall@5 | 0.67 | **0.72** |
| recall@20 | 0.93 | 0.93 |
| recall@5, `--no-doc-detect` | 0.56 | 0.59 |

- **fs-016 fixed** (0.00 → 1.00); no other question changes at k = 5.
- **fs-013 not fixed** (still 0.50; 8.4.4.2g at rank 10). It is outranked by its sibling clauses 11.2.2.5a–c and
  short permissions; only b = 0.3 brings it into the top 5, and that costs fs-018 and fs-019.
- Sweep over k1 ∈ {0.9, 1.2, 1.5} × b ∈ {0.3 … 0.75}: recall@5 between 0.675 and 0.725 and not monotonic in
  either parameter. With 20 scored questions, differences of one question are noise; b = 0.5 was chosen
  because it fixes a diagnosed cause and loses nothing, not as a tuned optimum. Re-check when the question
  set grows.

## Run 2 — 7 October 2026 — search fixes from run 1

Same questions and documents as run 1. Commands: `python eval/run_retrieval_eval.py --docs documents`
(recall@5), the same with `--k 20` (recall@20) and with `--no-doc-detect` (recall@5 without the document filter).

Changes since run 1 (`src/spacestd/index.py`, tests in `tests/test_search.py`):

1. **Document filter from the question.** Standards named in the question (full ID, or ID without its issue
   letter, as a whole word) restrict the search; a query naming only "ECSS" or only "NASA" is restricted to
   that family. Several named documents → their rankings are interleaved (as `--oracle-doc` does). Checked
   on the question texts: all 20 questions with expected IDs detect their document(s); fs-013 and fs-020
   ("ECSS" only) fall back to the four ECSS documents. An explicit `doc_id` still wins.
2. **BM25** (k1 = 1.2, b = 0.75) replaces term overlap × IDF, so long records no longer win by length.
3. **Table rows indexed** (caption, column headers, row labels, cell text, the row's footnotes). A row match
   is credited to the requirement(s) whose text points to the table (deleted records excluded), and the
   search result carries `matched_table_row` with the table citation and the row.
4. Tokeniser: hyphenated words also yield their parts ("non-discontinuity" → "discontinuity"); a few more
   question stopwords.

Not changed: guidance records still rank like requirements (cause 5); vocabulary gap (cause 4) waits for
hybrid search.

| Metric | Run 1 | Run 2 |
| --- | --- | --- |
| recall@5 | 0.44 | **0.67** |
| recall@20 | 0.58 | **0.93** |
| recall@5, `--no-doc-detect` | — | 0.56 |

Split of the recall@5 gain: BM25 + table rows alone 0.44 → 0.56; the document filter adds 0.56 → 0.67.
Without the filter fs-005 drops to 0.00 (FSR 29 at rank 6) and fs-017/fs-018 fall back to run-1 scores.

Recall@20 now beats run 1's oracle-document upper bound (0.85); only fs-009, fs-019 and fs-020 miss at k = 20.

### Run 2 per question (recall@5)

| Question | Run 1 | Run 2 | Missing ID (rank in full ranking) |
| --- | --- | --- | --- |
| fs-001 | 1.00 | 1.00 | |
| fs-002 | 0.00 | 0.50 | FSR 14 (17) |
| fs-003 | 0.00 | 1.00 | |
| fs-004 | 0.00 | 1.00 | |
| fs-005 | 1.00 | 1.00 | |
| fs-006 | 0.33 | 0.33 | FSR 53 (12), FSR 55 (14) |
| fs-007 | 0.00 | 1.00 | |
| fs-008 | 0.50 | 0.50 | 32-01 11.2.2.1a (14) |
| fs-009 | 0.00 | 0.00 | 32-01 6.3.2b (7), 6.3.2c (30), 7.2.8c (126) |
| fs-010 | 0.50 | 1.00 | |
| fs-011 | 1.00 | 1.00 | |
| fs-012 | 0.00 | 0.00 | 32-01 6.3.5.2a (17), 6.3.5.2b (9), 6.3.5.2c (8) |
| fs-013 | 1.00 | **0.50** | 32-01 8.4.4.2g (10) |
| fs-014 | 1.00 | 1.00 | |
| fs-015 | 0.50 | 1.00 | |
| fs-016 | 1.00 | **0.00** | 32-01 11.2.2.6a (17) |
| fs-017 | 0.33 | 1.00 | |
| fs-018 | 0.33 | 0.67 | 32-08 4.5.2a (10) |
| fs-019 | 0.00 | 0.50 | 32-01 6.3.2c (42), 6.3.2e (22) |
| fs-020 | 0.25 | 0.50 | 32-10 4.1.5.3a (24), 4.3.2.1a (6) |

### Observations

- **Table rows fixed the table questions**: fs-003 and fs-004 (FSR 29 via 5001B tables) go from 0.00 to 1.00.
- **The document filter fixed the predicted questions**: fs-007, fs-010, fs-017 go to 1.00; fs-018 improves.
- **Regressions: fs-013 (1.00 → 0.50) and fs-016 (1.00 → 0.00).** Both also regress with `--no-doc-detect`,
  so the cause is the scorer, not the filter. Both missing records are long (indexed length 8.4.4.2g 160,
  11.2.2.6a 180 tokens; average 44): BM25 length normalisation. See run 3.
- fs-008 still at 0.50 but now misses 11.2.2.1a instead of 5.1e.
- Remaining misses at k = 20 (fs-009, fs-019, fs-020 4.1.5.3a) are vocabulary-gap questions (cause 4) — wait for hybrid search.

## Run 1 — 5 October 2026 — first run on the real documents

- **Questions:** `eval/questions.yaml` (21 questions, draft, pending domain review); 20 have `expected_ids`, fs-021 is "not covered" and is judged at answer level.
- **Documents:** ECSS-E-ST-32C Rev.1 (PDF), ECSS-E-ST-32-01C Rev.2 (PDF), ECSS-E-ST-32-10C Rev.2 (PDF), ECSS-E-ST-32-08C Rev.1 (Word), NASA-STD-5001B w/Change 3 (PDF), NASA-STD-5019A w/Change 4 (PDF). 1,795 records in total (incl. NASA guidance paragraphs and ECSS deleted placeholders).
- **Search:** v0 keyword scorer in `src/spacestd/index.py` (term overlap × IDF, no length normalisation, no document filter, tables not indexed).
- **Command:** `python eval/run_retrieval_eval.py --docs documents` (k = 5).

### Result

**Mean recall@5 = 0.44** (7 of 20 questions fully retrieved). Recall@20 = 0.58.

Every expected ID exists in the index (checked by `tests/test_real_documents.py::test_eval_expected_ids_resolve`), so **all misses are search misses, not parser misses**.

| Question | Type | recall@5 | Missing ID (rank in full ranking) |
| --- | --- | --- | --- |
| fs-001 | numeric | 1.00 | |
| fs-002 | numeric | 0.00 | FSR 14 (41), FSR 24 (104) |
| fs-003 | numeric | 0.00 | FSR 29 (98) |
| fs-004 | numeric | 0.00 | FSR 29 (24) |
| fs-005 | classification | 1.00 | |
| fs-006 | lookup | 0.33 | FSR 53 (47), FSR 55 (49) |
| fs-007 | lookup | 0.00 | FSR 15 (12), FSR 16 (21) |
| fs-008 | classification | 0.50 | 32-01 5.1e (8) |
| fs-009 | numeric | 0.00 | 32-01 6.3.2b (92), 6.3.2c (41), 7.2.8c (512) |
| fs-010 | numeric | 0.50 | 32-01 8.4.4.2e (6) |
| fs-011 | numeric | 1.00 | |
| fs-012 | classification | 0.00 | 32-01 6.3.5.2a (191), 6.3.5.2b (63), 6.3.5.2c (95) |
| fs-013 | numeric | 1.00 | |
| fs-014 | classification | 1.00 | |
| fs-015 | lookup | 0.50 | 32-01 8.8a (12), 8.8b (6) |
| fs-016 | numeric | 1.00 | |
| fs-017 | lookup | 0.33 | 32-08 4.4.1a (123), 4.4.1b (29) |
| fs-018 | lookup | 0.33 | 32-08 4.5.2a (6), 4.5.2c (12) |
| fs-019 | compare | 0.00 | FSR 51 (28), 32-01 6.3.2c (105), 6.3.2e (49), 6.3.3e (24) |
| fs-020 | numeric | 0.25 | 32-10 4.1.5.3a (54), 4.3.2.1a (41), 4.3.2.1d (14) |

By type: numeric 0.47 (10 questions), classification 0.62 (4), lookup 0.30 (5), compare 0.00 (1).

### Diagnostic: search restricted to the right document

`--oracle-doc` restricts each search to the document(s) of the expected IDs (an upper bound for "detect the document named in the question", not a fair score): **recall@5 = 0.60, recall@20 = 0.85**. Questions fixed by the filter alone: fs-007, fs-010, fs-017, fs-018.

### Why the misses happen

1. **No document filter** (fs-007, fs-017, fs-018, fs-010 and part of most others). Almost every question names its standard, but search ranks all 1,795 records together; NASA-STD-5019A (491 records) and ECSS-E-ST-32 (750) crowd out the smaller documents.
2. **Long records win** (all questions). The scorer has no length normalisation, so a few long records (32-01 11.2.2.8c is in the top 5 of 10 of the 20 questions, 5019A "FCR 11 / 7.2.2" of 7, 32-01 6.2.2a of 6, 32-01 8.4.4.2g of 5). BM25 length normalisation is the direct fix.
3. **The numbers are in tables, the requirement only points to them** (fs-002, fs-003, fs-004, fs-020). FSR 24 / FSR 29 / 32-10 4.3.2.1a say "as specified in Table n"; the words of the question (protoflight, yield, discontinuity, launch vehicle, metallic) are in the table rows, which search does not index. Fix: index table rows (caption, row labels, column headers) and return the owning requirement plus the `get_table` row.
4. **Vocabulary gap** (fs-006, fs-009, fs-012, fs-019). Questions use practitioner words ("fairing cylinder", "interstage", "life factor", "fitting", "stress limit") that the standards phrase differently ("thin-walled shell", a loading spectrum "imposed four times", "low risk fracture item", a stress "percent of the ultimate tensile strength"). Needs synonyms/embeddings (Phase 3 hybrid search).
5. **Guidance records compete with requirements** (minor). NASA italic guidance paragraphs are useful context but sometimes outrank the FSR they explain (e.g. fs-002, fs-004 top hit is 5001B "4.1.1 guidance 3"). Consider ranking requirements above guidance, or returning guidance attached to the nearest requirement.

### Parser check during this run

No expected ID was missing or mis-numbered. Checks that support this: requirement counts match the machine IDs (32-01: 331 of 340 IDs on requirements, 1 on a table, 8 on figures/deleted items; 32-10: 26 of 33 on requirements, 6 on tables, 1 on a figure), 61/61 FSRs, 26/26 FCRs, and the 32-08 change-log IDs all land on records.

### Next

Recommended order: document filter from the question (doc IDs are explicit in almost every question) → BM25 with length normalisation → index table rows → hybrid search. Re-run this file's table after each step.
