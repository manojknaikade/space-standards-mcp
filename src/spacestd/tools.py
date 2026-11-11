"""Tool implementations shared by the MCP server and the agent.

Plain functions over a StandardsIndex that return JSON-ready dicts. The MCP server (server.py) and the
agent (spacestd_agent) both call these, so a client and the agent see exactly the same results.
No MCP or agent-framework imports here (ADR-0003).
"""

from __future__ import annotations

from .index import StandardsIndex, check_flag


def annotate(index: StandardsIndex, obj, doc_id: str = "", issue: str = ""):
    """Add `tier` to every requirement and table record in a tool result, and to table rows; tables and rows
    of documents below `verified` also get `check` ("check against the source, page N"). Rows carry the
    table's `page` when known. Works in place, nested hits (neighbours, matched_table_row, elsewhere) included."""
    if isinstance(obj, list):
        for v in obj:
            annotate(index, v, doc_id, issue)
    elif isinstance(obj, dict):
        doc_id, issue = obj.get("doc_id", doc_id), obj.get("issue", issue)
        is_table = "table_id" in obj
        if doc_id and ("req_id" in obj or is_table):
            tier = index.tier_of(doc_id, issue)
            obj["tier"] = tier
            if date := index.issue_date_of(doc_id, issue):
                obj["issue_date"] = date
            if is_table and ("rows" in obj or "cells" in obj):
                if tier != "verified":
                    obj["check"] = check_flag(obj.get("page"))
                for row in obj.get("rows", []):
                    row["tier"] = tier
                    if "check" in obj:
                        row["check"] = obj["check"]
                    if obj.get("page"):
                        row["page"] = obj["page"]
        for v in obj.values():
            annotate(index, v, doc_id, issue)
    return obj


def list_documents(index: StandardsIndex, family: str = "", doc_type: str = "", discipline: str = "", query: str = "",
                   include_not_loaded: bool = False, limit: int = 50) -> dict:
    docs = index.list_documents(family, doc_type, discipline, query, include_not_loaded)
    limit = max(1, min(limit, 200))
    out = {"count": len(docs), "documents": docs[:limit]}
    if len(docs) > limit:
        out["truncated"] = f"showing {limit} of {len(docs)}; narrow with family, doc_type, discipline or query"
    return out


def _other_issue(index: StandardsIndex, doc_id: str) -> dict | None:
    """A 'not found' answer for a document named with an issue or revision letter that is not the loaded one."""
    loaded = index.loaded_issues(doc_id)
    if not loaded:
        return None
    names = "; ".join(f"{x['doc_id']} {x['issue'] or 'first issue'}" + (f" ({x['issue_date']})" if x.get("issue_date") else "")
                      for x in loaded)
    return {"found": False, "loaded_issues": loaded,
            "message": f"{doc_id} is not loaded. Loaded: {names}. Clause numbers and text can differ between "
                       "issues: ask again with the loaded issue, and tell the user which issue the answer comes from."}


def get_requirement(index: StandardsIndex, doc_id: str, req_id: str) -> dict:
    req = index.get(doc_id, req_id)
    if req is not None:
        return annotate(index, {"found": True, **req.to_dict()})
    other = _other_issue(index, doc_id)
    if other:
        return other
    help_ = index.lookup_help(doc_id, req_id)
    if "parent" in help_:  # the item is inside its paragraph's record: return that record, and say so
        parent = help_["parent"]
        return annotate(index, {
            "found": True, **parent.to_dict(), "asked_for": req_id,
            "note": f"{req_id} has no record of its own: this is {parent.req_id}, the record that holds it. Cite "
                    f"it as returned ({parent.citation}) and read the item in its text."})
    out = {"found": False, "message": f"No requirement {req_id} in {doc_id} among loaded documents."}
    if "records_in_clause" in help_:
        out["records_in_clause"] = help_["records_in_clause"]
        out["message"] = (f"{req_id} is a clause of {doc_id} with {len(help_['records_in_clause'])} records: ask "
                          "for one of them by its req_id (see records_in_clause).")
    elif "nearest_ids" in help_:
        out["nearest_ids"] = help_["nearest_ids"]
        out["message"] += (" IDs near it are listed in nearest_ids; they are suggestions, not the record asked "
                           "for: do not cite one without reading it. get_section_outline lists a clause's records.")
    return out


def search_requirements(index: StandardsIndex, query: str, doc_id: str | None = None, limit: int = 5) -> dict:
    if not query or not query.strip():
        return {"found": False, "message": "Empty query, nothing was searched. Do not answer yet: call "
                                           "search_requirements again with search words (a topic or a requirement ID, "
                                           "e.g. \"factor of safety metallic structure\"), optionally with doc_id; "
                                           "list_documents shows the loaded documents."}
    return annotate(index, index.search_response(query, doc_id, max(1, min(limit, 20))))


def get_table(index: StandardsIndex, doc_id: str, table_id: str = "") -> dict:
    if not table_id:
        tables = index.list_tables(doc_id)
        if not tables and (other := _other_issue(index, doc_id)):
            return other  # the named issue is not the loaded one: no silent empty list
        return annotate(index, {"found": True, "tables": tables})
    t = index.get_table(doc_id, table_id)
    if t is None:
        return _other_issue(index, doc_id) or {
            "found": False, "message": f"No {table_id} in {doc_id} among loaded documents.",
            "tables": index.list_tables(doc_id)}
    return annotate(index, {"found": True, **t.to_dict()})


def get_references(index: StandardsIndex, doc_id: str, req_id: str) -> dict:
    req = index.get(doc_id, req_id)
    if req is None:
        return _other_issue(index, doc_id) or {
            "found": False, "message": f"No requirement {req_id} in {doc_id} among loaded documents."}
    return {"found": True, "citation": req.citation, "references": req.references}


def compare_topic(index: StandardsIndex, topic: str, doc_ids: list[str] | None = None, limit: int = 5) -> dict:
    return annotate(index, index.compare_topic(topic, doc_ids, max(1, min(limit, 10))))


def find_standards(index: StandardsIndex, topic: str, family: str = "", doc_type: str = "", limit: int = 8) -> dict:
    if not topic or not topic.strip():
        return {"found": False, "message": "Empty topic. Give the subject in a few words, e.g. \"thermal vacuum test\"."}
    docs = index.rank_documents(topic, family, doc_type, max(1, min(limit, 20)))
    for d in docs:
        if date := index.issue_date_of(d["doc_id"], d["issue"]):
            d["issue_date"] = date
    out: dict = {"topic": topic, "count": len(docs), "documents": docs}
    notes = ["Ranked by keyword matches in the loaded documents: a listed standard mentions the topic, which does "
             "not prove it applies to the user's product or project. Open the sections (get_section_outline, "
             "get_requirement) before saying what a standard requires."]
    missing, more = index.not_loaded_report(index.mentioned_not_loaded(topic))
    out.update(missing)
    notes += more
    if external := index.external_standards(topic):
        out["external_standards"] = external
    if not docs:
        out["coverage"] = "none"
        notes.append("No loaded standard matches this topic.")
    out["notes"] = notes
    return out


def get_section_outline(index: StandardsIndex, doc_id: str, clause: str = "", depth: int = 2) -> dict:
    out = index.section_outline(doc_id, clause, max(1, min(depth, 6)))
    if out is None:
        return {"found": False, "message": f"{doc_id} is not among the loaded documents."}
    return out


def record_keys(result) -> list[str]:
    """'doc|id' keys of every requirement or table record in a tool result, nested hits included."""
    out = []
    if isinstance(result, dict):
        if result.get("doc_id") and (result.get("req_id") or result.get("table_id")):
            out.append(f"{result['doc_id']}|{result.get('req_id') or result['table_id']}")
        for v in result.values():
            out += record_keys(v)
    elif isinstance(result, list):
        for v in result:
            out += record_keys(v)
    return out
