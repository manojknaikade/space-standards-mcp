"""MCP server exposing ECSS/NASA standards as requirement-level tools.

Run:  SPACESTD_DOCS=/path/to/documents python -m spacestd.server
Hybrid search (optional, pip install -e ".[embed]"): SPACESTD_EMBED=default (or a fastembed model name),
SPACESTD_RERANK=default to add a cross-encoder reranker, SPACESTD_DENSE_WEIGHT to tune the fusion.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from mcp.server.mcpserver import MCPServer
from mcp.types import ToolAnnotations

from . import tools
from .catalogue import build_catalogue
from .embeddings import index_options_from_env
from .index import StandardsIndex

mcp = MCPServer(
    "space-standards",
    instructions=(
        "Tools for ECSS and NASA standards. Always cite requirements and tables as returned in the "
        "'citation' field. Only cite requirements returned by these tools. Take numbers (factors, "
        "test levels) only from get_table rows, with their conditions and footnotes. Every record and table "
        "carries its parse `tier`; values from tables below `verified` carry a `check` flag and a `page`: give "
        "such numbers with the flag, as \"check against the source, page N\". State the "
        "record kind (requirement, recommendation, permission, guidance, deleted, table (a table with no owning record: cite the table)). If no tool "
        "result supports an answer, say the loaded standards do not cover it."
    ),
)


READ_ONLY = ToolAnnotations(readOnlyHint=True, openWorldHint=False)


@lru_cache(maxsize=1)
def get_index() -> StandardsIndex:
    folder = Path(os.environ.get("SPACESTD_DOCS", "documents")).expanduser()
    if not folder.is_dir():
        return StandardsIndex([], **index_options_from_env())
    catalogue = build_catalogue(folder)
    return StandardsIndex(catalogue.load_documents(), catalogue=catalogue, **index_options_from_env())


@mcp.tool(annotations=READ_ONLY)
def list_documents(family: str = "", doc_type: str = "", discipline: str = "", query: str = "",
                   include_not_loaded: bool = False, limit: int = 50) -> dict:
    """List the standards currently loaded: issue, title, family (ECSS / NASA), doc_type (standard, handbook, ...),
    discipline, record counts and parse `tier` ("verified": hand-checked against the source; "checked": passes the
    automatic parse health checks; "unchecked": parsed automatically — for both, check numbers against the source
    page before relying on them).

    Filters (optional, case-insensitive): family "ECSS" or "NASA"; doc_type e.g. "handbook"; discipline as a
    code ("E-32", "Q-70", "NASA-5000") or a name ("structures"); query: words in the doc ID or title.
    include_not_loaded: also list standards in the user's documents folder that are not loaded (`loaded: false`).
    Their text is not available: never answer from them, but you may name one as the standard that would cover
    a question. Returns {"count", "documents"} (at most `limit`, plus "truncated" when more match).
    """
    return tools.list_documents(get_index(), family, doc_type, discipline, query, include_not_loaded, limit)


@mcp.tool(annotations=READ_ONLY)
def get_requirement(doc_id: str, req_id: str) -> dict:
    """Get the exact text of one requirement.

    doc_id: e.g. "ECSS-Q-ST-80C" or "ECSS-Q-ST-80" or "NPR 7150.2".
    req_id: ECSS clause + letter, e.g. "5.2.1a" (DRD content: "A.2.1<5.2>a"); NASA tag, e.g. "FSR 24",
    or an FCR item, e.g. "FCR 11 / 7.2.1.c"; untagged NASA standards: section + item, e.g. "4.2a", "4.3(1)",
    or the n-th "shall" paragraph of a section, e.g. "4.4 req 1". Records carry a `kind`: requirement, recommendation,
    permission, guidance or deleted — say which when answering.
    """
    return tools.get_requirement(get_index(), doc_id, req_id)


@mcp.tool(annotations=READ_ONLY)
def search_requirements(query: str, doc_id: str | None = None, limit: int = 5) -> dict:
    """Search across loaded requirements (BM25; hybrid with embeddings when the server enables it).
    Optionally restrict to one document.

    query: REQUIRED search words, never empty, e.g. "ultimate factor of safety metallic structure" or
    "fracture control NASA-STD-5019". A call without search words returns no results.

    Returns {"results": [...]} plus, when relevant, "not_loaded", "elsewhere" and "notes".
    Without doc_id, standards named in the query (e.g. "NASA-STD-5001B", "ECSS-E-ST-32-01") restrict
    the search to them. `not_loaded` lists named standards that are not loaded: never answer from
    them. It is split into `in_documents_folder` (present in the user's documents folder but not loaded,
    with issue and status: say so, and that they can be loaded through corpus.yaml) and
    `not_in_documents_folder` (the user does not have them). `elsewhere` holds stronger hits from other loaded documents when the named document
    matches weakly — it may not cover the topic. Table rows are searched too: a hit found through a
    table carries `matched_table_row` (table citation, row labels, cells) — take the numbers from
    there or from get_table, and cite both the requirement and the table. Records and rows carry `tier`
    (verified, checked, unchecked) and `page`; rows from tables below `verified` carry `check`: repeat it
    ("check against the source, page N") next to any number taken from them. Each hit may carry
    `neighbours`: the records next to it in the same clause (a requirement is often split over sibling
    letters). They are full records with citations; read them before concluding a clause is not covered.
    """
    return tools.search_requirements(get_index(), query, doc_id, limit)


@mcp.tool(annotations=READ_ONLY)
def get_table(doc_id: str, table_id: str = "") -> dict:
    """Get a table (e.g. factors of safety) as structured rows, verbatim from the source.

    doc_id: e.g. "ECSS-E-ST-32-10C" or "NASA-STD-5001B". table_id: e.g. "Table 4-3" or "4-3".
    Each row has row labels and value cells (text as printed, parsed value, footnote markers).
    Quote the cell text and its footnotes; 'spans_rows' marks a value printed once in a merged
    cell that covers several rows. The table and each row carry `tier` and `page`; below `verified` they also
    carry `check` ("check against the source, page N"): give every number from such a table with that flag
    (an answer that does not repeat it fails the citation check). Omit table_id (empty string) to list the tables of a document.
    """
    return tools.get_table(get_index(), doc_id, table_id)


@mcp.tool(annotations=READ_ONLY)
def get_references(doc_id: str, req_id: str) -> dict:
    """List the standards and clauses that a requirement (or its notes) refers to."""
    return tools.get_references(get_index(), doc_id, req_id)


@mcp.tool(annotations=READ_ONLY)
def compare_topic(topic: str, doc_ids: list[str] | None = None, limit: int = 5) -> dict:
    """Side-by-side search of one topic in several standards, e.g. ECSS vs NASA on factors of safety.

    topic: the subject only, e.g. "ultimate design factor metallic structure" (no standard names).
    doc_ids: the standards to compare, e.g. ["ECSS-E-ST-32-10", "NASA-STD-5001"]; omit for all loaded.
    Returns one section per document, grouped by family (ECSS, NASA), with its top hits and the
    table rows they matched. Requested or named standards that are not loaded are listed as in
    search_requirements (`not_loaded`, `in_documents_folder`, `not_in_documents_folder`). `coverage: "weak"` marks a document whose best hit is far below the
    best hit elsewhere: it may not treat the topic — say so rather than force an equivalence.
    Coverage is judged on keyword matches: read the hits, and use get_requirement / get_table before comparing.
    """
    return tools.compare_topic(get_index(), topic, doc_ids, limit)


@mcp.tool(annotations=READ_ONLY)
def get_section_outline(doc_id: str, clause: str = "", depth: int = 2) -> dict:
    """Table of contents of one standard: clause numbers, titles and how many records (by kind) each holds.

    doc_id: e.g. "ECSS-E-ST-32-01C" or "NASA-STD-5019A". clause: e.g. "7.2" to list that section and its
    subsections, plus the record IDs placed directly in it and the tables in it; omit for the whole document.
    depth: how many heading levels to list below the starting point (default 2).
    The outline has no requirement text: use get_requirement / get_table for anything you quote or cite.
    """
    return tools.get_section_outline(get_index(), doc_id, clause, depth)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
