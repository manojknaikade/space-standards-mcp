"""eval/run_answer_eval.py scoring on the invented fixtures, with a fake judge (no LLM, no network)."""

import importlib.util
import json
from pathlib import Path

import pytest

from spacestd.citations import CitationChecker
from spacestd.index import StandardsIndex
from spacestd.loaders import load_folder
from spacestd.tools import record_keys
from spacestd_agent.claude_code import _json_keys

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("run_answer_eval", ROOT / "eval" / "run_answer_eval.py")
rae = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rae)


@pytest.fixture(scope="module")
def checker():
    return CitationChecker(StandardsIndex(load_folder(ROOT / "tests" / "fixtures")))


class FakeJudge:
    def __init__(self, reply: str):
        self.reply, self.prompts = reply, []

    def complete(self, system, prompt, max_tokens=2000):
        self.prompts.append(prompt)
        return self.reply


def test_judge_parses_reply_and_scores_coverage():
    q = {"type": "numeric", "question": "Q?", "answer_points": ["a", "b"], "reference_answer": "ref"}
    fake = FakeJudge('Here: {"points": [{"point": "a", "grade": "yes"}, {"point": "b", "grade": "partial"}], '
                     '"errors": [], "verdict": "partial"}')
    res = rae.judge(fake, q, "answer text")
    assert res["verdict"] == "partial" and res["coverage"] == 0.75
    assert "answer text" in fake.prompts[0] and "- a\n- b" in fake.prompts[0]


def test_check_one_recall_and_not_covered(checker):
    q = {"id": "x", "type": "compare", "question": "Unit testing?",
         "expected_ids": ["DEMO-E-ST-99C|5.2.1a", "DEMO NPR 9999.1|SWE-950"]}
    res = rae.check_one(checker, q, {"answer": "DEMO-E-ST-99C 5.2.1a requires it."})
    assert res["citation_recall"] == 0.5 and res["table_recall"] is None
    nc = {"id": "y", "type": "not_covered", "question": "Radiation?", "expected_ids": []}
    assert rae.check_one(checker, nc, {"answer": "The loaded standards do not cover this."})["not_covered_ok"]
    assert not rae.check_one(checker, nc, {"answer": "Not covered, but use 50 krad."})["not_covered_ok"]


def test_score_demo_answers(tmp_path, capsys):
    args = rae.argparse.Namespace(
        run=str(tmp_path), docs=str(ROOT / "tests" / "fixtures"), questions=str(ROOT / "eval" / "demo_questions.yaml"),
        ids=None, workers=1, answers=str(ROOT / "eval" / "demo_answers.jsonl"), judge="none",
        judge_model="", rejudge=False, markdown=False)
    rae.score(args)
    scores = json.loads((tmp_path / "scores.json").read_text())
    assert scores["demo-004"]["ungrounded"] == ["9.7"]
    assert scores["demo-005"]["invented"] == ["4.2.9a"]
    assert scores["demo-003"]["not_covered_ok"] is True
    assert "answers with an invented ID" in capsys.readouterr().out


def test_tool_keys_from_results():
    res = {"results": [{"doc_id": "D", "req_id": "1.1a", "matched_table_row": {"citation": "D, Table 1"}}],
           "elsewhere": [{"doc_id": "E", "req_id": "X 2"}]}
    assert record_keys(res) == ["D|1.1a", "E|X 2"]
    assert _json_keys('{"found": true, "doc_id": "D", "table_id": "Table 1"}') == ["D|Table 1"]
