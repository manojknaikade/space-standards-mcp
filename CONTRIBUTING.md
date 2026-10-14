# Contributing

Thanks for helping. This project answers questions about ECSS and NASA standards with exact citations, and it
can only be public because **it contains no standards text**. Most of the rules below protect that.

## The one rule: no standards text

Never commit, paste or attach text from a standard: not in code, tests, eval files, docs, issues, PR
descriptions or commit messages ([ADR-0002](docs/adr/0002-bring-your-own-documents.md)).

- `documents/` is gitignored; only its README is tracked. Do not force-add anything under it, and do not
  commit `.pdf`, `.doc` or `.docx` files or parse caches (`.pkl`).
- Tests use **invented** text in `tests/fixtures/` (the `demo_*` standards). When you need a new layout or ID
  convention, write a short invented example that has the same *shape* (headings, numbering, tags, table
  layout) with made-up words and numbers.
- Never invent requirement IDs and present them as real ones. Fixtures are invented documents with `DEMO`
  document IDs (`DEMO-E-ST-98C`, `DEMO NPR 9999.1`); eval files that refer to real documents use IDs checked
  against the source.
- Eval `answer_points` are paraphrases, not quotations. Numbers (factors, test levels) come from the source
  tables with their units and conditions, never from memory.
- Committed reports about real documents (`eval/CORPUS_HEALTH.md`, `eval/RESULTS.md`,
  `tests/test_real_documents.py`) hold counts, IDs, scores and page numbers only.

**Reporting a parsing problem** without quoting: give the document ID and issue, the page, the requirement or
table ID as printed, and describe the layout in your own words ("level-4 heading without a number in the text
layer", "tag after a dotted paragraph number"). An invented reproduction is the most useful thing you can add.

If you find standards text that was committed by mistake, do not open a public issue that repeats it; report
it privately as described in [SECURITY.md](SECURITY.md).

## Development setup

Python 3.11 or newer.

```bash
pip install -e ".[dev]"
python -m pytest -q          # tests that need real documents or LibreOffice skip themselves
```

Fixture evals (the same as CI):

```bash
python eval/run_retrieval_eval.py --docs tests/fixtures --questions eval/demo_questions.yaml
python eval/run_answer_eval.py score --run /tmp/demo-run --docs tests/fixtures \
  --questions eval/demo_questions.yaml --answers eval/demo_answers.jsonl --judge none
```

With your own standards in `documents/`, the real-document tests and evals run too; see the README and
[CLAUDE.md](CLAUDE.md) for the commands. Their outputs (`eval/runs/`) are gitignored because answers quote the
standards.

## Code conventions

- Keep the knowledge layer (`src/spacestd/`) free of agent-framework dependencies
  ([ADR-0003](docs/adr/0003-python-mcp-sdk.md)); the agent lives in `src/spacestd_agent/`.
- Every tool result that contains requirement text carries its `citation` (document ID, issue, requirement ID).
- Add or update tests with each change; fixtures stay invented.
- Larger design changes get a short decision record in `docs/adr/`.

## Pull requests

- Keep each PR focused and describe what changed and how you tested it.
- Tick the template's checklist, including **"contains no standards text"**.
- CI must pass.

## Licence

The code is licensed under the [Apache License 2.0](LICENSE). By submitting a contribution you agree that it
is licensed under the same terms (section 5 of the licence). The standards themselves are not part of this
project and are not covered by its licence.
