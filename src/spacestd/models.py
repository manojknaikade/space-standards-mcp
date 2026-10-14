"""Core data model: one record per requirement, one record per table."""

from __future__ import annotations

from dataclasses import dataclass, field

# requirement     "shall" (ECSS lettered item, NASA tagged requirement or an FCR item)
# recommendation  "should" without "shall"
# permission      "may" / "need not" without "shall"/"should" (ECSS nomenclature)
# guidance        NASA italic text, rationale, informative annexes, other descriptive items
# deleted         ECSS "<<deleted>>" placeholders, kept so lookups can explain the gap
KINDS = ("requirement", "recommendation", "permission", "guidance", "deleted")


@dataclass
class Requirement:
    doc_id: str
    issue: str
    req_id: str
    clause: str
    text: str
    heading_path: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    references: list[str] = field(default_factory=list)
    kind: str = "requirement"
    machine_id: str = ""  # e.g. ECSS-E-ST-32-10_0110001, where the document has one
    parent: str = ""  # e.g. "FCR 11" for an FCR item record
    page: int | None = None
    tables: list[str] = field(default_factory=list)  # tables the text points to, e.g. "Table 4-3"
    flags: list[str] = field(default_factory=list)  # parser warnings, e.g. stale cross-references

    @property
    def citation(self) -> str:
        issue = f" {self.issue}" if self.issue else ""
        return f"{self.doc_id}{issue}, {self.req_id}"

    def to_dict(self) -> dict:
        d = {
            "citation": self.citation,
            "doc_id": self.doc_id,
            "issue": self.issue,
            "req_id": self.req_id,
            "kind": self.kind,
            "clause": self.clause,
            "heading_path": self.heading_path,
            "text": self.text,
            "notes": self.notes,
            "references": self.references,
        }
        if self.machine_id:
            d["machine_id"] = self.machine_id
        if self.parent:
            d["parent"] = self.parent
        if self.tables:
            d["tables"] = self.tables
        if self.page:
            d["page"] = self.page
        if self.flags:
            d["flags"] = self.flags
        return d


@dataclass
class Cell:
    """One table cell: verbatim text, parsed number (if any) and footnote markers."""

    text: str
    value: float | None = None
    footnotes: list[str] = field(default_factory=list)
    spans_rows: bool = False  # value printed once in a merged cell covering several rows
    shaded: bool = False  # grey fill: "required" under the table's legend (footnotes["shaded"])

    def to_dict(self) -> dict:
        d: dict = {"text": self.text}
        if self.spans_rows:
            d["spans_rows"] = True
        if self.shaded:
            d["shaded"] = True
        if self.value is not None:
            d["value"] = self.value
        if self.footnotes:
            d["footnotes"] = self.footnotes
        return d


@dataclass
class TableRow:
    labels: dict[str, str]  # row-label columns, e.g. {"Structure type": "Metallic parts", "Vehicle": "Launch vehicle"}
    cells: dict[str, Cell]  # value columns
    page: int | None = None  # set only on rows from a continuation page (the table's `page` is the first)

    def to_dict(self) -> dict:
        d = {"labels": self.labels, "cells": {k: v.to_dict() for k, v in self.cells.items()}}
        if self.page is not None:
            d["page"] = self.page
        return d


@dataclass
class Table:
    doc_id: str
    issue: str
    table_id: str  # "Table 4-3" / "Table 1"
    caption: str
    label_columns: list[str]
    value_columns: list[str]
    rows: list[TableRow]
    footnotes: dict[str, str] = field(default_factory=dict)
    units: dict[str, str] = field(default_factory=dict)  # per column, only when stated in the source
    clause: str = ""
    machine_id: str = ""
    page: int | None = None

    @property
    def citation(self) -> str:
        issue = f" {self.issue}" if self.issue else ""
        return f"{self.doc_id}{issue}, {self.table_id}"

    def to_dict(self) -> dict:
        d = {
            "citation": self.citation,
            "doc_id": self.doc_id,
            "issue": self.issue,
            "table_id": self.table_id,
            "caption": self.caption,
            "clause": self.clause,
            "label_columns": self.label_columns,
            "value_columns": self.value_columns,
            "units": self.units,
            "rows": [r.to_dict() for r in self.rows],
            "footnotes": self.footnotes,
        }
        if self.machine_id:
            d["machine_id"] = self.machine_id
        if self.page:
            d["page"] = self.page
        return d


@dataclass
class Document:
    doc_id: str
    issue: str
    title: str
    source_file: str
    requirements: list[Requirement] = field(default_factory=list)
    tables: list[Table] = field(default_factory=list)
    unparsed: list[str] = field(default_factory=list)  # body fragments the parser could not place
    body_words: int = 0  # words of the body text layer (PDF parsers; 0 = not measured)
    unparsed_words: int = 0  # words of the unparsed fragments, uncut

    def summary(self) -> dict:
        kinds: dict[str, int] = {}
        for r in self.requirements:
            kinds[r.kind] = kinds.get(r.kind, 0) + 1
        return {
            "doc_id": self.doc_id,
            "issue": self.issue,
            "title": self.title,
            "source_file": self.source_file,
            "requirement_count": len(self.requirements),
            "records_by_kind": kinds,
            "tables": [t.table_id for t in self.tables],
        }
