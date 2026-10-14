# Notes for AI coding sessions

Project: MCP server (then a thin agent) for cited, requirement-level Q&A over ECSS and NASA standards. Initial scope: launcher and payload-fairing structures (factors of safety, fracture control, loads, shock, vibroacoustics) — see docs/adr/0004. Read docs/PROJECT_BRIEF.md, docs/ROADMAP.md, docs/PUBLIC_RELEASE_PLAN.md and the newest entries of the round log docs/PROGRESS.md (if present) first. That log lives only in the private development repository (it is on `scripts/release_exclude.txt`).
If docs/PROGRESS.md is present, end every orchestrator round with one entry in it (format in that file; workers do not edit it); start prompts are in docs/SESSION_PROMPTS.md.
All work runs locally (ADR-0008): an Opus orchestrator session plans rounds and dispatches parallel `step-worker` subagents (Sonnet, medium effort; `.claude/agents/step-worker.md`) for 🤖 steps, each in its own worktree; it does 🧠 steps itself and owns the tracking files. Never upload standards anywhere.

Hard rules:
- Never commit standards text. `documents/` is gitignored; tests use invented text in `tests/fixtures/` only (ADR-0002).
- Every tool result that contains requirement text must include its `citation` (doc ID, issue, requirement ID).
- Never fabricate requirement IDs in tests, eval files or prompts; eval `answer_points` are paraphrases.
- Numbers (factors, test levels) must come from source tables with units and conditions; never from model memory.
- Keep the knowledge layer (`src/spacestd/`) free of agent-framework dependencies (ADR-0003).

Workflow:
- `pip install -e ".[dev]" && pytest`
- `python eval/run_retrieval_eval.py --docs tests/fixtures --questions eval/demo_questions.yaml`
- Real eval (needs local documents): `python eval/run_retrieval_eval.py --docs documents`
  (hybrid: `pip install -e ".[embed]"`, then `--embed default [--rerank default]`; server/agent: `SPACESTD_EMBED=default`)
- Answer eval: `python eval/run_answer_eval.py generate --run eval/runs/<name>` then `... score --run eval/runs/<name>`
  (needs `pip install -e ".[eval]"` + `ANTHROPIC_API_KEY`, or `--backend cli` / `--judge cli` with a logged-in `claude`).
  `--backend cli-agent` runs the same gate around `claude -p` (no API key needed).
  `--backend agent` runs the Phase 3 agent (`src/spacestd_agent`): the `api` loop plus the citation gate.
  `eval/runs/` is gitignored (answers quote standards text).
- Catalogue of the local documents: `python -m spacestd.catalogue documents`; `documents/corpus.yaml` selects what loads (ADR-0006).
- Parse health (sets the `checked` tier): `python -m spacestd.health documents [--corpus all]` writes `eval/CORPUS_HEALTH.md`.
- Text audit of the release tree (needs local documents): `python scripts/audit_standards_text.py --docs documents` (file:line, length and IDs only).
- Update the ROADMAP and PUBLIC_RELEASE_PLAN checkboxes when a milestone is done.
