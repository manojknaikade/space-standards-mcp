# MCP tool interface

The server (`python -m spacestd.server`, stdio) exposes eight read-only tools over the standards in
`SPACESTD_DOCS`. The same functions back the agent (`src/spacestd/tools.py`). Every tool returns one JSON object.

Three rules hold for every tool:

1. **Only loaded text is returned.** Nothing is answered from a standard that is not loaded; a named standard
   that is missing, of another issue, or from another body is reported as such.
2. **Every record names its edition.** `citation` (document, issue, record ID), `issue`, `issue_date`, `page`
   and the parse `tier` come with each record and table.
3. **No result means no answer.** `found: false` and `coverage: "none"` mean nothing supports an answer: say
   "the loaded standards do not cover this". `not_loaded` and `external_standards` name sources this server does
   not hold: state nothing from them. `issue_mismatch` comes with results from the loaded issue: they may be
   used when the user accepts that issue, named as such. None of these is a reason to fall back on memory.

## Records

A record is one requirement, recommendation, permission, guidance paragraph, definition or deleted placeholder.

| Field | Meaning |
| --- | --- |
| `citation` | How to cite it: `ECSS-Q-ST-80C Rev.2, 6.2.2.1a`, `NASA-STD-5001B w/Change 3, FSR 24`, `NPR 7150.2D, SWE-144` |
| `doc_id`, `issue` | Document and issue as loaded. `issue` is empty for the first issue of a revision letter |
| `issue_date` | ISO date of the loaded edition (file name, else the first page; an NPR's effective date) |
| `req_id` | ECSS: clause + letter (`5.2.1a`), DRD item (`A.2.1<5.2>a`), unlettered paragraph (`4.2.3 req 2`), definition (`3.2.1`). NASA: tag (`FSR 24`, `SWE-144`, `FCR 11 / 7.2.1.c`), or section + item (`4.2a`, `4.3(1)`, `4.4 req 1`), guidance (`4.1 guidance 2`). Handbooks: the section number |
| `kind` | `requirement` (shall), `recommendation` (should), `permission` (may), `guidance` (informative text, handbook sections, notes on intent), `definition`, `deleted`, `table` (a table no record owns) |
| `clause`, `heading_path` | Clause number and the headings above it |
| `text`, `notes` | Verbatim text and the NOTEs attached to it |
| `references` | Standards and clauses the text refers to |
| `tables` | Tables the text points to (`Table 4-3`): fetch them with `get_table` |
| `page` | 1-based page of the source PDF |
| `tier` | `verified` (hand-checked against the source), `checked` (passes the automatic parse checks), `unchecked` |
| `machine_id`, `parent`, `flags` | ECSS machine ID; the tag an item belongs to; parser warnings (e.g. `inferred clause number`) |

Table rows carry `labels`, `cells` (`text` as printed, parsed `value`, `footnotes`, `spans_rows`, `shaded`),
`tier`, `page`, and below the `verified` tier a `check` flag (`check against the source, page N`) that must be
repeated next to any number taken from the row.

## Tools

### `list_documents(family="", doc_type="", discipline="", query="", include_not_loaded=false, limit=50)`

The loaded standards. Filters are case-insensitive: `family` `ECSS` or `NASA`; `doc_type` (`standard`,
`handbook`, `adoption notice`, `specification`, `procedural requirements`); `discipline` as a code (`E-32`,
`Q-80`, `NASA-5000`, `NPR-7000`) or a name (`structures`); `query` words in the ID or title.
Returns `count`, `documents` (ID, issue, title, family, type, discipline, tier, record counts by kind, table IDs)
and `truncated` when more match. With `include_not_loaded`, documents present in the folder but not selected by
`corpus.yaml` are listed with `loaded: false`: name them, never answer from them.

### `find_standards(topic, family="", doc_type="", limit=8)`

"Which standards cover X?" Ranks loaded documents by keyword matches on the topic and by title.
Returns `documents`: ID, issue, `issue_date`, title, type, discipline, tier, `score`, `matching_records` and
`top_sections` (clause, heading, citation of the best record there; no text). A listed standard writes about
the topic; that does not make it applicable to a given project. `coverage: "none"` when nothing matches.

### `search_requirements(query, doc_id=null, limit=5)`

Keyword search (BM25; plus embeddings when `SPACESTD_EMBED` is set) over records and table rows.
`query` is required. Standards named in the query, or `doc_id`, restrict the search to them.

| Result field | Meaning |
| --- | --- |
| `results` | Records, best first, each with `score`; `neighbours` (records next to it in the same clause); `matched_table_row` when the match was a table row |
| `not_loaded`, `in_documents_folder`, `not_in_documents_folder` | Standards named in the query that are not loaded, split by whether the folder holds them |
| `issue_mismatch` | The query names an issue or revision letter that is not the loaded one: `asked`, the loaded `doc_id` / `issue` / `issue_date`, `reason`. Results come from the loaded issue: say so |
| `external_standards` | Standards of other bodies named in the query (`MIL-STD-1540`, `ISO 24113`, `SMC-S-016`): never held here |
| `coverage` | Present only as a warning. `none`: no keyword match at all. `weak`: an acronym or designation of the query (`unmatched_terms`) is in no hit, so the hits may not treat it |
| `elsewhere` | Stronger hits in other documents when the named document matches weakly |
| `notes` | The above in words |

The absence of `coverage` does not prove the topic is covered: read the hits.

### `get_requirement(doc_id, req_id)`

One record by ID. `doc_id` accepts the ID with or without its issue letter and with issue words
(`ECSS-Q-ST-80`, `ECSS-Q-ST-80C Rev.2`, `NPR 7150.2`). Returns the record with `found: true`, or `found: false` with:

| Field | When |
| --- | --- |
| `loaded_issues` | The named issue or revision letter is not loaded; lists what is |
| `records_in_clause` | `req_id` is a clause holding several records: ask for one of them |
| `nearest_ids` | IDs of the same document close to the one asked: suggestions to read, not to cite unread |

A record that holds the item asked for (`5.2.2` for `5.2.2a`) is returned with `asked_for` and a `note`.
Identifiers printed in the text (`M&S 26`, `Requirement 4.4-1`) resolve to their record.

### `get_table(doc_id, table_id="")`

A table as structured rows: `label_columns`, `value_columns`, `rows`, `footnotes`, `units`, `caption`, `clause`.
Without `table_id`, the list of the document's tables. Numbers are quoted from `cells[].text` with their
footnotes and, below the `verified` tier, with the `check` flag.

### `get_references(doc_id, req_id)`

The standards and clauses a record (or its notes) refers to: `citation`, `references`.

### `compare_topic(topic, doc_ids=null, limit=5)`

One topic searched separately per standard, grouped ECSS then NASA. `doc_ids` picks the standards; without it,
two or more standards named in the topic, else the three best matches per family (`documents_chosen`); a
single standard named in the topic is always among them. Pass `doc_ids` to fix the set.
Each section: `doc_id`, `issue`, `title`, `results`, and `coverage` (`ok`, `weak`: far below the best section,
`none`). A weak or empty section means that standard may not treat the topic: do not force an equivalence.

### `get_section_outline(doc_id, clause="", depth=2)`

A document's heading tree with record counts by kind. With `clause`, that section's subsections, the IDs and
kinds of the records placed in it, and its tables. No requirement text: fetch records before quoting.

## Typical sequences

| Question | Calls |
| --- | --- |
| "What does ECSS-Q-ST-80 require for software criticality?" | `search_requirements` (the named standard restricts it) → `get_requirement` for the records cited |
| "Which standards apply to thermal vacuum testing?" | `find_standards` → `get_section_outline` on the top documents → `get_requirement` |
| "Compare ECSS and NASA fracture control" | `compare_topic` (or with `doc_ids`) → `get_requirement` / `get_table` per side |
| "What factor of safety applies to …?" | `search_requirements` → `get_table` for the table the record points to |
| "What does ECSS mean by residual risk?" | `search_requirements` (definitions are records of kind `definition`) |
| A question naming `Rev.1` when `Rev.2` is loaded | `issue_mismatch` / `loaded_issues`: answer from the loaded issue only if the user accepts it, and say which issue it is |

## Configuration

| Setting | Effect |
| --- | --- |
| `SPACESTD_DOCS` | Documents folder (default `documents`) |
| `documents/corpus.yaml` | `load:` / `exclude:` patterns over document IDs select what is loaded |
| `SPACESTD_EMBED`, `SPACESTD_RERANK`, `SPACESTD_DENSE_WEIGHT` | Optional hybrid search (`pip install -e ".[embed]"`) |

Scores for this interface, deterministic:

```bash
python eval/run_coverage_eval.py --docs documents
```

Answers with an LLM judge (two steps, same run folder):

```bash
python eval/run_answer_eval.py generate --run eval/runs/<name> --questions eval/coverage_questions.yaml
```

```bash
python eval/run_answer_eval.py score --run eval/runs/<name> --questions eval/coverage_questions.yaml
```
