# ADR-0006: Full corpus: catalogue everything, load in waves, mark parse tiers

Status: accepted · 2026-10-09 · extends [ADR-0004](0004-scope-launcher-structures.md) (the scope becomes the first wave)

## Context

The goal is now every ECSS and NASA standard, handbooks included. The owner has downloaded all of them locally:
the ECSS active-standards bundle (PDF and Word, October 2025), the ECSS handbooks bundle (October 2023, with a
`superseded HBs/` folder) and the 85 NASA technical standards and handbooks from standards.nasa.gov, with a download
manifest. That is about 285 distinct documents and 700 MB of files, against 7 documents loaded so far.

Compute is not the constraint. The in-memory BM25 index and the per-file parse cache handle this size. The
constraints are:

1. **Trust.** Every loaded document so far has per-document tests: requirement counts, spot-checked IDs and every
   table value checked by hand. An automatic parse of 285 documents will produce wrong IDs and broken table rows
   in some of them. A confident citation to a wrongly parsed record is the worst failure this tool can have.
2. **Retrieval dilution.** A query like "factor of safety" matches dozens of documents once everything is loaded.
   Recall on the 57 eval questions will drop, and only the eval can say by how much.
3. **Handbooks drown out standards.** Handbooks are long and descriptive, so BM25 favours them, and answers would
   start citing guidance where a binding requirement exists.
4. **Identity.** The bundles hold the same document in two or three formats, duplicate downloads (`… (2).pdf`),
   superseded issues, multi-part handbooks (ECSS-E-HB-32-20 Parts 1–8, ECSS-E-HB-31-01 Parts 1–16), NASA volumes
   and annexes, and NASA file names without the dot (`nasa-std-87394a…`).

## Decision

**Catalogue everything, load in waves, mark how far each document's parse can be trusted.**

1. **Catalogue** (`spacestd.catalogue`, `python -m spacestd.catalogue documents`): recursive discovery of the
   documents folder. Each file is identified the way a loaded document is (sidecar, Word page header, cover page,
   file name, then a download manifest next to the file). Files are grouped by doc_id, one source per document:
   files nearer the top of the folder win over bundle copies, then PDF over Word. Copies of one download in
   several formats share the identity read from the preferred format. Parts, volumes and NASA annexes are part
   of the doc_id (`ECSS-E-HB-32-20 Part 1A`, `NASA-HDBK-5010 Vol 1`, `NASA-STD-8719.24 Annex`). Family, type
   (standard, handbook, adoption notice, specification) and discipline follow from the number: the ECSS
   discipline tree (`E-32` structures, `Q-70` materials, …) and the NASA number series (`NASA-5000` structures and
   mechanical, …). Files under a `superseded…` folder are catalogued as superseded and never loaded. Identities
   are cached in `.spacestd-cache/catalogue.json`.
2. **Selection.** `documents/corpus.yaml` lists doc-ID patterns to load (`load: [ECSS-E-ST-32*, …]`, `"*"` for
   everything active), plus an optional `exclude:` list dropped from that selection (round 10). Without it, only files directly in `documents/` are loaded, as before.
3. **`list_documents` covers the whole catalogue.** Filters: family, doc_type, discipline, words in the ID or
   title. `include_not_loaded` lists documents that are present but not loaded, so a client can say which
   standard would cover a question without answering from it.
4. **Parse tiers**, in `list_documents` now and in every citation once unchecked documents are loaded:
   - `verified`: per-document tests, hand-checked against the source (the 7 v1 documents; keyed by doc_id and
     issue, so a new issue is not verified).
   - `checked`: passes the automatic health checks (next step: record count, share of records with a valid ID,
     orphan text, tables with ragged rows, cover ID matching the file name).
   - `unchecked`: parsed, not checked.
   A table row from a document below `verified` is returned with a flag and its page, so the agent states the
   number with "check against the source" and the citation gate does not treat it as authoritative. This keeps
   the "numbers only from source tables" rule honest at scale.
5. **Load in waves by discipline, gated by the eval.** Each wave adds about 10 eval questions, and the existing
   questions must not regress (recall@5 and table row hits, with and without neighbours):
   1. Structures, mechanisms and testing: the rest of ADR-0004's table (ECSS-E-ST-32-02/-03/-11, E-ST-33-01,
      E-ST-10-03, E-HB-32-25/-26, NASA-STD-5002/5020/7001/7002/7003, NASA-HDBK-7005), plus the E-HB-32 handbooks.
   2. The rest of ECSS-E and the NASA engineering series.
   3. ECSS-Q (product assurance) and NASA 87xx (safety and mission assurance).
   4. ECSS-M, -U, -S and the remaining handbooks.
6. **Two-stage retrieval as the corpus grows**: narrow to candidate documents (named in the query, then
   discipline and document-level relevance from titles, scope clauses and headings), then search records within
   them. Rank standards above handbooks by default; handbook records stay `guidance`. Built when wave 1 shows
   the dilution, not before.

## Consequences

- The loaded set did not change: 7 documents, retrieval eval unchanged (recall@5 0.64; 0.74 with neighbours).
- Handbooks need section-level chunking (they have no lettered requirements) and table handling for long,
  figure-heavy PDFs; NASA volumes and annexes need checks on their requirement-ID conventions.
- The doc-ID pattern in `index.py` (query detection, citation checks) does not yet know part and volume
  suffixes. Fix it in wave 1, before a multi-part document is loaded.
- Issue tracking: the bundle holds a corrected issue of one loaded document (ECSS-E-ST-32-10C Rev.2 Corr.1; the
  bundle copies of 32-01C, 5001B and 5019A are byte-identical to the loaded files). The catalogue reports
  issue conflicts; moving a verified document to a new issue means re-running its per-document tests.
- Answering scope widens beyond launcher structures, but the eval stays the arbiter of each wave. ADR-0004's
  reasoning (build where the answers can be judged) still orders the waves.
