"""Agent loop and citation gate with a scripted fake model client: no network, no API key, invented fixtures."""

from pathlib import Path
from types import SimpleNamespace as NS

import pytest

from spacestd.index import StandardsIndex
from spacestd.loaders import load_folder
from spacestd_agent import StandardsAgent
from spacestd_agent.agent import tool_definitions

FIXTURES = Path(__file__).parent / "fixtures"
GOOD = "DEMO-E-ST-98C Rev.2, 4.1.2b: the design ultimate factor for composite sandwich panels is 9.8."


def text(t):
    return NS(stop_reason="end_turn", content=[NS(type="text", text=t)])


def tool(name, **args):
    return NS(stop_reason="tool_use", content=[NS(type="tool_use", id=f"tu_{name}", name=name, input=args)])


class FakeClient:
    """Returns the scripted responses in order and records every request."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.requests = []
        self.beta = NS(messages=NS(create=self.create))

    def create(self, **kw):
        self.requests.append({**kw, "messages": list(kw["messages"])})
        return self.responses.pop(0)


@pytest.fixture(scope="module")
def index() -> StandardsIndex:
    return StandardsIndex(load_folder(FIXTURES))


def lookup():
    return tool("get_requirement", doc_id="DEMO-E-ST-98C", req_id="4.1.2b")


def test_tools_are_the_mcp_servers():
    assert {t["name"] for t in tool_definitions()} == {
        "list_documents", "get_requirement", "search_requirements", "get_references", "get_table", "compare_topic",
        "get_section_outline"}


def test_answer_passes_gate(index):
    client = FakeClient(lookup(), text(GOOD))
    res = StandardsAgent(index, client=client).ask("Ultimate factor for sandwich panels?")
    assert res.status == "passed" and res.answer == GOOD and res.unretrieved == []
    assert res.retrieved == ["DEMO-E-ST-98C|4.1.2b"] and res.tool_calls[0]["name"] == "get_requirement"
    tool_result = client.requests[1]["messages"][-1]["content"][0]
    assert tool_result["tool_use_id"] == "tu_get_requirement" and "9.8" in tool_result["content"]
    assert client.requests[0]["fallbacks"] == "default" and "gate" in res.to_record()


def test_invented_id_is_revised(index):
    client = FakeClient(lookup(), text("DEMO-E-ST-98C 4.1.9b sets 9.8."), text(GOOD))
    res = StandardsAgent(index, client=client).ask("Ultimate factor?")
    assert res.status == "revised" and res.answer == GOOD and res.draft.startswith("DEMO-E-ST-98C 4.1.9b")
    assert "4.1.9b" in client.requests[2]["messages"][-1]["content"]  # findings sent back for the revision


def test_failed_revision_declines_without_repeating_the_error(index):
    bad = text("DEMO-E-ST-98C 4.1.2b: the factor is 9.8, or 1.4 for secondary structure.")
    res = StandardsAgent(index, client=FakeClient(lookup(), bad, bad)).ask("Ultimate factor?")
    assert res.status == "declined" and res.answer.startswith("Not covered")
    assert "1.4" not in res.answer and "DEMO-E-ST-98C, 4.1.2b" in res.answer
    assert res.check["declines"] and res.check["ungrounded"] == [] and res.check["invented"] == []


def test_unretrieved_citation_is_reported_not_gated(index):
    ans = text("DEMO-E-ST-98C 4.1.2a sets the yield factor 9.9.")  # real ID, never retrieved
    res = StandardsAgent(index, client=FakeClient(lookup(), ans)).ask("Yield factor?")
    assert res.status == "passed" and res.unretrieved == ["DEMO-E-ST-98C|4.1.2a"]


def test_gate_off_and_tool_errors(index):
    client = FakeClient(tool("get_requirement", doc_id="DEMO-E-ST-98C"), text("Made up 1.23."))  # missing req_id
    res = StandardsAgent(index, client=client, gate=False).ask("?")
    assert res.status == "ungated" and res.answer == "Made up 1.23." and "gate" not in res.to_record()
    assert "error" in client.requests[1]["messages"][-1]["content"][0]["content"]


def test_refusal_and_turn_budget(index):
    res = StandardsAgent(index, client=FakeClient(NS(stop_reason="refusal", content=[]))).ask("?")
    assert res.status == "error" and res.to_record()["error"] == "refusal" and res.answer == ""
    res = StandardsAgent(index, client=FakeClient(lookup(), lookup()), max_turns=2).ask("?")
    assert res.to_record()["error"] == "max_turns"


class FakeClaudeCode:
    """Stands in for spacestd_agent.claude_code.ClaudeCode: scripted answers, records prompts and resumes."""

    model = "fake"

    def __init__(self, *answers):
        self.answers = list(answers)
        self.calls = []

    def answer(self, prompt, resume=None):
        self.calls.append((prompt, resume))
        return {"answer": self.answers.pop(0), "tool_calls": [{"name": "search_requirements", "input": {}}],
                "retrieved": ["DEMO-E-ST-98C|4.1.2b"], "session_id": "s1"}


def test_claude_code_agent_revises_in_the_same_session(index):
    from spacestd_agent.claude_code import ClaudeCodeAgent

    cc = FakeClaudeCode("DEMO-E-ST-98C 4.9.9z sets the factor.", GOOD)
    res = ClaudeCodeAgent(index, cc).ask("What ultimate factor applies to sandwich panels?")
    assert res.status == "revised" and res.answer == GOOD
    assert cc.calls[0][1] is None and cc.calls[1][1] == "s1"  # the revision resumes the first session
    assert "4.9.9z" in cc.calls[1][0] and len(res.tool_calls) == 2
