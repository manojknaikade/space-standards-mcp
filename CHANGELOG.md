# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [0.3.0]

### Added

- Revision guard. A document named with an issue or revision letter that is not the loaded one is reported and
  never answered silently: `search_requirements` returns `issue_mismatch`; `get_requirement`, `get_table` (with or
  without a table ID) and `get_references` return `found: false` with `loaded_issues`. Document names accept issue words
  (`ECSS-Q-ST-80C Rev.2`).
- `issue_date` on every record, table and listed document: the edition's date from the file name or the first
  page (an NPR's effective date; never an expiration date).
- `find_standards` tool: loaded standards ranked on a topic, with their best-matching sections.
- `search_requirements` signals for declining: `external_standards` (another body's standard named in the
  query), `coverage: none` (no keyword match) and `coverage: weak` with `unmatched_terms` (an acronym or
  designation of the query is in no hit).
- Lookup help in `get_requirement`: identifiers printed in a record's text resolve to it (`M&S 26`,
  `Requirement 4.4-1`); an item kept inside its paragraph returns that paragraph's record (`asked_for`); a
  clause number returns `records_in_clause`; a miss lists `nearest_ids`.
- NASA Procedural Requirements: `scripts/download_nasa_nprs.py` (NODIS, current revisions, manifest), document
  IDs `NPR 7150.2D`, a parser for the NODIS layout (`src/spacestd/npr_parser.py`), doc type
  `procedural requirements`.
- ECSS parser: terms and definitions as records of kind `definition` (clause 3 of a standard, the glossary
  ECSS-S-ST-00-01); requirements printed without letters under their machine IDs as `<clause> req N`
  (ECSS-Q-ST-60C, ECSS-Q-ST-70-61C).
- Coverage evaluation: `eval/coverage_questions.yaml` (all ECSS branches and NASA families, expected standard,
  clause and issue read from the sources) and `eval/run_coverage_eval.py` (deterministic score);
  `eval/run_answer_eval.py` reads the same file and checks the cited standard, clause and issue by string match.
- `docs/TOOLS.md`: the full tool interface.

### Changed

- `compare_topic` without `doc_ids` on a corpus above 8 documents compares the three best-matching standards per
  family (`documents_chosen`) instead of returning one section per loaded document.
- ECSS parser: a table-of-contents line is never a heading; a heading's parents in `heading_path` follow its
  clause number; a chapter title printed without its number joins the path of its first clause.
- Server instructions, tool descriptions and the agent prompt cover every discipline, not only structures.
- The `anthropic` dependency accepts versions below 3 (was below 2).

## [0.2.4]

### Added

- `documents/corpus.yaml` takes an optional `exclude:` list of doc-ID patterns, dropped from what `load:` selects.

### Changed

- The ten wave-2 evaluation questions (`w2-001` to `w2-010`) are reviewed by the owner: all ok.

## [0.2.3]

### Changed

- README: install from PyPI (`uvx space-standards-mcp`, `pipx install space-standards-mcp`); the package is
  published since 0.2.2.
- NASA parser: table-of-contents pages are never the start or end of the body (a bold section-4 or `APPENDIX`
  entry in the contents had cut several handbooks down to a few contents lines; PARSING_NOTES H20).

### Added

- Ten wave-2 evaluation questions (`w2-001` to `w2-010`, pending owner review).

## [0.2.2]

### Added

- `server.json` for the official MCP registry (`io.github.manojknaikade/space-standards-mcp`, PyPI package, stdio)
  and the registry's ownership marker in the README.
- PyPI publishing workflow with Trusted Publishing, run in the public repository when a GitHub Release is
  published (a tag push alone publishes nothing); `docs/PUBLISHING.md` lists the one-time setup and the steps.
- The sdist holds the source, README, licence files, changelog and `pyproject.toml` only.

### Changed

- Tool schemas mark mandatory arguments as required (`search_requirements` `query`); `get_table`'s `table_id` is
  optional (empty lists the document's tables). An empty query's message asks for a new call with search words.
- Agent prompt: every search call carries search words; after an empty or unhelpful result, search again instead
  of declining.
- README links are absolute, so they work on PyPI.
- CI uses `actions/checkout` and `actions/setup-python` v7.

## [0.2.1]

### Fixed

- Citation gate: numbers inside launcher names ("Ariane 5", "Atlas V", "Long March 3B") are no longer read as
  answer values.
- Citation checker: a paragraph number right after a document name ("NASA-STD-7003A, 4.3.1.1") counts as a
  citation when that document has the record (NASA documents without requirement tags, handbooks).
- `search_requirements` with an empty query returns a message instead of an error.
- Parser: a group label printed in a table's header band (NASA-STD-7002B Table 1), a numbered group row with mixed
  bold and roman text (ECSS-E-ST-10-03C Table 4-1), and a tagless NASA lead-in paragraph that points to a table
  (NASA-STD-7003A 4.3) are read correctly.
- Release-tree guard: a tree with none of the release-excluded files is checked as the release tree.

## [0.2.0]

### Added

- Full-corpus catalogue of ECSS and NASA standards and handbooks, with `documents/corpus.yaml` selecting what loads,
  parse tiers (verified / checked / unchecked) and a parse-health report (`python -m spacestd.health`).
- MCP tools `compare_topic` (one topic per standard, grouped ECSS / NASA, with coverage rating) and
  `get_section_outline` (a standard's heading tree, or the record IDs of one clause).
- `list_documents` filters (family, type, discipline, title) and `include_not_loaded`.
- Neighbouring records shown with each search hit.
- Optional hybrid search (BM25 + embeddings) and cross-encoder reranking, via the `embed` extra.
- Thin agent (`space-standards-agent`, `agent` extra) with a citation gate: invented requirement IDs and ungrounded
  numbers trigger one revision, then a decline.
- Retrieval and answer evaluations (`eval/`), including deterministic citation and number checks.
- Text-audit script that checks the release tree for copied standards text.
- Apache-2.0 licence, packaging metadata, ruff lint and a CI matrix on Python 3.11 to 3.13.

### Changed

- Parser coverage extended to more ECSS and NASA document layouts; requirement kinds (requirement, recommendation,
  permission, guidance, deleted) recorded on every record.

## [0.1.0]

### Added

- MCP server with `list_documents`, `get_requirement`, `search_requirements`, `get_table` and `get_references`.
- Requirement-level parsing of ECSS and NASA standards from PDF (and Word for one ECSS document), with tables as
  structured rows, and a citation (document, issue, requirement ID) on every result.
- In-memory index with lookup by ID and BM25 keyword search.
- Synthetic demo standards and unit tests.
