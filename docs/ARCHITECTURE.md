# Architecture

```
 official sources (ecss.nl, NASA NODIS/standards)
            │  user downloads
            ▼
   documents/  (.pdf / .docx / .doc / .txt / .md, gitignored)
            │
   loaders  ──►  layout lines (text, font, size, bold/italic, position)
            │    + tables (ruled grid → rows, footnotes)
            │
   parser   ──►  Requirement records (one per requirement)
            │
   index    ──►  lookup by ID · BM25 search (requirements + table rows) + neighbours · references · compare_topic · section outline
            │    optional: + embeddings (RRF fusion) + cross-encoder rerank (embeddings.py, ".[embed]")
            │
   tools.py ──►  the seven tool functions (shared by server and agent)
            │
   ├── MCP server (stdio)  ◄──  any MCP client (Claude, VS Code, Cursor…)
   └── agent (spacestd_agent) ── tool loop ─► draft ─► citations.py gate ─► pass / revise once / decline
            │
   eval/               ◄──  question set, retrieval + answer metrics
```

## Catalogue and corpus (ADR-0006)

`catalogue.py` walks the documents folder recursively and keeps one source per doc_id (top-level copy first, then
PDF over Word; copies of one download share the identity of the preferred format). Each entry carries family, type,
discipline (from the ECSS discipline tree or the NASA number series), title, status (active / superseded) and parse
tier (verified / checked / unchecked). `health.py` parses each catalogued document and checks it automatically
(records by kind, valid-ID share, unparsed fragments, ragged tables, file-name vs identity, errors); a document that
meets every threshold is `checked`, recorded in `.spacestd-cache/health.json` (stale once the parser changes) and
summarised text-free in `eval/CORPUS_HEALTH.md`. `corpus.yaml` selects what is loaded; `list_documents` reads the whole
catalogue, so a client can name a standard that is present but not loaded.

## Data model

`Requirement`

| Field | Example |
| --- | --- |
| `doc_id` | `ECSS-Q-ST-80C` |
| `issue` | `Rev.1` |
| `req_id` | `5.2.1a` (ECSS clause + letter) or `SWE-033` (NASA) |
| `clause` | `5.2.1` |
| `heading_path` | `["5 Software product assurance programme", "5.2 …", "5.2.1 …"]` |
| `text` | verbatim requirement text |
| `notes` | verbatim NOTEs attached to the requirement |
| `references` | `["ECSS-E-ST-40", "ECSS-Q-ST-80 clause 6.2.3"]` |
| `kind` | requirement / recommendation / permission / guidance / deleted |
| `machine_id` | `ECSS-E-ST-32-10_0110020` (ECSS documents from 2009 on) |
| `parent` | `FCR 11` for an FCR item such as `FCR 11 / 7.2.1.c` |
| `tables` | tables the text points to, e.g. `["Table 4-3"]` |
| `flags` | parser warnings, e.g. a stale Word cross-reference |

`Table`: table ID, caption, clause, machine ID, label columns, value columns, rows of
`{labels, cells}` where each cell is `{text, value, footnotes, spans_rows}`, and footnotes.
Citation: `ECSS-E-ST-32-10C Rev.2 Corr.1, Table 4-3`.

Citation format: `ECSS-Q-ST-80C Rev.1, 5.2.1a` / `NPR 7150.2D, SWE-033`.

## Parsing rules (v0)

- Numbered heading `5.2.1 Title` → current clause.
- ECSS requirement items `a.`, `b.` … under a clause → `req_id = clause + letter`.
- `NOTE` / `NOTE 1` paragraphs attach to the last requirement.
- NASA `[SWE-nnn]` tags anywhere in a paragraph → `req_id = SWE-nnn`.
- Cross-references detected by regex: `ECSS-X-XX-nn[-nn][A-Z]`, `NPR nnnn.n[X]`, `NASA-STD-nnnn`, `NASA-HDBK-nnnn`, plus "clause n.n.n".

Real documents (PDF loader, Phase 1): see [PARSING_NOTES.md](PARSING_NOTES.md) for the ECSS and
NASA rules (font-based headings, machine IDs, DRD IDs, NASA tag definitions vs references, FCR items,
italic guidance, tagless standards: `4.2a`, `4.3(1)`, `4.4 req 1`) and the table extraction rules (grid rows, stacked values, merged cells).

Real documents will need per-document adjustments (tables, annex requirements, multi-paragraph items). Each real document gets its own parsing test.

## Citation gate (agent, ADR-0005)

The agent runs the same loop as the answer eval's `api` backend, then checks each draft with
`src/spacestd/citations.py` (the answer eval's checker), grounding numbers in the records the loop retrieved:

| Finding | Gate action |
| --- | --- |
| invented ID (exists in no loaded document) | one revision with the findings; still failing → decline ("not covered") |
| ungrounded number (in no cited or retrieved record or table) | same |
| cited record never returned by a tool call | reported (`unretrieved`), not gated |

The decline names the valid records the drafts relied on, never the invented IDs or ungrounded numbers.

`ClaudeCodeAgent` (`src/spacestd_agent/claude_code.py`) keeps this gate and swaps the loop for `claude -p` with
the MCP server: the answer eval's `cli-agent` backend, measured against the plain `cli` client.

## Hybrid search (optional, Phase 3)

| Stage | What | Decides |
| --- | --- | --- |
| BM25 | requirement records + table rows, document filter from the query | ranking; **coverage** |
| embeddings | same records and rows (row hits credited to the owning requirement), top 50 | ranking |
| fusion | `60 · (1/(60 + bm25 rank) + w/(60 + dense rank))` | `score` |
| rerank | cross-encoder on the top 30 (row text added for table hits) | order of the top 30 |

`elsewhere` and `compare_topic` coverage keep comparing BM25 scores (`lexical_score`): the 0.75 threshold was
calibrated on them, and an embedding always finds a nearest neighbour, so it must not make a document look as
if it covers a topic. Enabled with `SPACESTD_EMBED` / `SPACESTD_RERANK` (server, agent, answer eval) or
`--embed` / `--rerank` (retrieval eval). Vectors are cached on disk by text hash (no text in the cache).

## Why not plain RAG chunks

Fixed-size chunks split requirements, lose their IDs and merge neighbours. Requirement records keep the unit engineers actually cite and make "exact text for ID X" a deterministic lookup that can be tested without an LLM.
