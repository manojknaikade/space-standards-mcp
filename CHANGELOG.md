# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

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
