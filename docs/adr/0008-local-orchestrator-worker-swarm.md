# ADR-0008: All work runs locally: an Opus orchestrator and a swarm of Sonnet workers

Status: accepted · 2026-10-10 · owner decision; replaces the cloud / local split of the
[release plan](../PUBLIC_RELEASE_PLAN.md) and the `orchestrator` subagent

## Context

Until now each release-plan step was marked ☁️ (cloud session: fresh clone, no `documents/`) or 💻 (local
session with the standards). The split followed ADR-0002 but cost time: findings had to be written up as
invented reproductions before a cloud session could fix them (`docs/PARSING_NOTES.md`), parser fixes were not
checked on the real PDFs until a later local re-run, and parallel cloud PRs conflicted on the round log `docs/PROGRESS.md` (a file that now exists only in the private development repository).
An `orchestrator` subagent dispatched the sessions but could not do any of the work itself.

## Decision

- **Everything runs on one local machine.** No cloud sessions. The standards stay local (ADR-0002 unchanged).
- **One orchestrator session on Opus 5.5** plans each round, does the judgement-heavy steps itself (🧠), reviews
  and merges the workers' PRs, and owns the tracking files.
- **Workers are `step-worker` subagents on Sonnet 5.5, medium effort** (`.claude/agents/step-worker.md`), for
  well-defined steps (🤖): a spec, files, tests and an acceptance check. They run in parallel, each in its own
  git worktree, open a PR and report back; they never merge or edit the tracking files.
- **📄 marks a step that reads the real standards.** At most one such run parses at a time (shared parse cache
  and CPU); fixture-only workers run without limit.
- **Tracking is centralised:** one round-log entry (`docs/PROGRESS.md`, private repository only) and one round of checkbox updates per round, in a
  tracking PR by the orchestrator.
- The `orchestrator` subagent is deleted; the orchestrator is the main session, started with the prompt in
  `docs/SESSION_PROMPTS.md`.

## Consequences

- Parser fixes can be developed against the real PDFs and checked in the same round; `PARSING_NOTES.md`
  reproductions with invented text are still needed for the fixtures (ADR-0002), not for a hand-off.
- Faster rounds: the independent 🤖 steps of a stage run at the same time; Opus time goes to planning, review and
  the 🧠 steps.
- Workers have access to `documents/`, so the hard rules (text-free commits, invented fixtures) are enforced
  by the worker definition and by the orchestrator's review of every diff, and by the text audit (C3/C4) before
  release.
- Old ☁️ / 💻 marks and "cloud" / "local" labels in the round log (`docs/PROGRESS.md`, private repository only) and dated notes are history and stay as
  written.
