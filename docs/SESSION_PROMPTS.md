# Session prompts

All work runs locally, on the machine with `documents/`. One **orchestrator** session (Opus 5.5) plans each
round and dispatches a swarm of **workers** (`step-worker` subagent: Sonnet 5.5, medium effort, defined in
`.claude/agents/step-worker.md`) for the well-defined steps, in parallel. There are no cloud sessions. The
strategy is recorded in [ADR-0008](adr/0008-local-orchestrator-worker-swarm.md); the checklist and marks are in
[PUBLIC_RELEASE_PLAN.md](PUBLIC_RELEASE_PLAN.md).

Start the orchestrator with Opus 5.5 as the model (`claude --model opus` or the model picker) in the main
checkout, and paste the prompt below.

## Orchestrator session

```text
Continue the space-standards-mcp project from the logged progress. You are the ORCHESTRATOR (Opus) on the
local machine; the real standards are in documents/ (gitignored; never commit or upload them).

1. `git checkout main && git pull --ff-only` (stop if the tree is dirty). Read CLAUDE.md,
   docs/PUBLIC_RELEASE_PLAN.md (marks, checklist, "Order at a glance") and, if present, the newest entries of
   docs/PROGRESS.md (private repository only). Run `pytest -q`. List open PRs (`gh pr list`).
2. Plan one round: every unchecked step whose prerequisites are done and that is not in flight.
   - 🤖 steps go to `step-worker` subagents, all in parallel (one message, several Agent calls), each with
     `isolation: "worktree"`. At most one 📄 step that parses the real documents runs at a time (they share
     the parse cache in documents/.spacestd-cache and the CPU); fixture-only steps have no limit.
   - 🧠 steps (judgement, debugging on the real PDFs, reviews) you do yourself while the workers run.
   - 👤 steps: prepare what I need to check, ask me, and wait.
   Show the round as a short table (step, who, why now, what it unblocks) and wait for my "go".
3. Each worker prompt: step ID and title, a precise spec (files, expected behaviour, tests, the commands to
   run, the acceptance check), MAIN=<absolute path of this checkout>, and whether it is 📄. Never put standards
   text in a prompt; point to files instead.
4. When workers report: review each PR diff (correctness, hard rules, no standards text), ask the worker to
   fix (SendMessage) or fix it yourself, wait for CI, merge. After every merge delete the branch on the remote
   and locally: `gh pr merge <n> --squash --delete-branch`, then `git worktree remove <path>` for its worktree,
   `git branch -D <branch>` and `git fetch --prune`. Then run pytest on main.
5. Close the round in one tracking PR: tick the boxes in docs/PUBLIC_RELEASE_PLAN.md (and docs/ROADMAP.md),
   record eval runs in eval/RESULTS.md, and, if docs/PROGRESS.md is present, add one newest-first entry for the round in its
   format, ending with "Next:" naming the next round's steps and their marks. Merge it and delete its branch
   (remote and local) the same way; `git branch -a` and `git worktree list` should show only main.
6. Plan the next round, or finish with a short summary: what merged (PR links), what is waiting for me.
```

## Round 9 (prepared 15 Oct 2026)

The generic prompt above with round 9's work and round 8's lessons filled in. Paste it as is; afterwards use the
generic prompt again.

```text
Continue the space-standards-mcp project from the logged progress. You are the ORCHESTRATOR (Opus) on the
local machine; the real standards are in documents/ (gitignored; never commit or upload them).

1. `git checkout main && git pull --ff-only` (stop if the tree is dirty). Check `git remote -v`: `origin` is the private
   `space-standards-mcp-dev` (all development, PRs, docs/PROGRESS.md) and `public` is `space-standards-mcp`, PUBLIC
   (release commits only, rebuilt with the "Release flow" in docs/PUBLIC_RELEASE_PLAN.md; never force-push, never
   open PRs there). Read CLAUDE.md, docs/PUBLIC_RELEASE_PLAN.md (D3, "After going public": wave 2 B2 / B5) and the
   newest entry of docs/PROGRESS.md (round 8). Run `.venv/bin/python -m pytest -q` (426 expected with documents/;
   the local corpus.yaml now loads wave 2, 167 documents). `gh pr list` (review and merge Dependabot PRs like
   worker PRs).

2. Plan round 9 as a table and wait for my "go":
   - D3 👤: ask whether I have set up PyPI (pending trusted publisher for `publish.yml`, environment `pypi`) and
     the `pypi` environment on the public repository; if yes, and on my "go", create the GitHub Release v0.2.2 on
     the public repository (that starts the publish), check PyPI, then the registry (`mcp-publisher`, I log in),
     then the README install section in a v0.2.3. The announcement is mine to post (docs/ANNOUNCEMENT_DRAFT.md).
   - Wave 2 B2 🧠📄: NASA documents that parse to almost nothing (HDBK-2203, 4007A, 6024, 1005, 4002B, 1004;
     STD-2818, 2821, 2822, 6033) and NASA-STD-3001 Vol 1 (valid IDs 9 %): look at the PDFs, write each pattern up
     in docs/PARSING_NOTES.md and hand fixture-reproducible fixes to 🤖 workers. Then the ECSS valid-ID and
     ragged-table groups (list in round 8's PROGRESS entry). Per-table diff on the exact head before merging a
     parser change; `test_verified_tables_unchanged` must hold.
   - Wave 2 B5 🤖: draft ~10 wave-2 eval questions (`review: pending`, paraphrased answer points, IDs checked with
     the tools), for my review.
   - API pair (`--backend agent` vs `--backend api`) only if ANTHROPIC_API_KEY is set.

3. Worker rules: as in the generic prompt; one 📄 parse at a time. After every merge delete the branch on the
   remote and locally (`gh pr merge <n> --squash --delete-branch`, `git worktree remove <path>`,
   `git branch -D <branch>`, `git fetch --prune`); `--delete-branch` can leave the remote branch when the local
   one is checked out in a worktree: check `git branch -r` and `git push origin --delete <branch>`.
   Round 8 lessons:
   - Check what a CI workflow triggers on before a release push: #88 published on every `v*` tag, which the
     release flow pushes (changed to a published GitHub Release, #90).
   - A 📄 worker's text audit only covers the corpus it loaded; re-run the audit on main (full catalogue) before
     a release. Health-report count rows hit E-HB-31-01 Part 14A Table 8-8 by coincidence (allowlisted per file).
   - The version lives in three places: pyproject.toml, src/spacestd/__init__.py, server.json (tested).
   - fs-021's empty call is gone; its remaining partial is a scope hedge in the answer, not a tool fault.

4. Close the round with one tracking PR (plan and ROADMAP boxes, eval/RESULTS.md if runs were made, one
   newest-first PROGRESS entry ending with "Next:"). Merge it and delete its branch, remote and local;
   `git branch -a` and `git worktree list` should show only main and release. When preparing the next round's
   prompt, keep this branch-deletion rule in it.
```

## Notes

- The round log `docs/PROGRESS.md` lives only in the private development repository (it is on
  `scripts/release_exclude.txt`). Workers do not touch it, `docs/PUBLIC_RELEASE_PLAN.md` or `docs/ROADMAP.md`; the
  orchestrator updates them once per round, so parallel PRs never conflict on them.
- Worktrees have only `documents/README.md`; a 📄 worker copies the folder's contents from the main checkout
  (`cp -Rc "$MAIN/documents/." documents/`, an APFS clone; never a symlink: the catalogue does not follow it) and
  runs Python as `PYTHONPATH=src $MAIN/.venv/bin/python`.
- A step can be worked by hand without the orchestrator: give the orchestrator prompt and say "do only <ID>".
- Since D1a (14 Oct) development stays on the private `space-standards-mcp-dev` (`origin`); the public
  `space-standards-mcp` (`public`) only receives release commits rebuilt from -dev's `main` (release plan, "Release
  flow"). Workers branch from `origin/main` and open PRs on -dev. Check `git remote -v` at the start of each round.
