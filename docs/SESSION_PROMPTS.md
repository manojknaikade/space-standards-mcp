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

## Round 10 (prepared 15 Oct 2026)

The generic prompt above with round 10's work and round 9's lessons filled in. Paste it as is; afterwards use the
generic prompt again.

```text
Continue the space-standards-mcp project from the logged progress. You are the ORCHESTRATOR (Opus) on the
local machine; the real standards are in documents/ (gitignored; never commit or upload them).

1. `git checkout main && git pull --ff-only` (stop if the tree is dirty). Check `git remote -v`: `origin` is the private
   `space-standards-mcp-dev` (all development, PRs, docs/PROGRESS.md) and `public` is `space-standards-mcp`, PUBLIC
   (release commits only, rebuilt with the "Release flow" in docs/PUBLIC_RELEASE_PLAN.md; never force-push, never
   open PRs there). Read CLAUDE.md, docs/PUBLIC_RELEASE_PLAN.md (D3, "After going public": wave 2 B2 / B5),
   docs/PARSING_NOTES.md H20–H24 and the newest entry of docs/PROGRESS.md (round 9). Run
   `.venv/bin/python -m pytest -q` (428 expected with documents/). `gh pr list` (review and merge Dependabot PRs
   like worker PRs).

2. Plan round 10 as a table and wait for my "go":
   - D3 👤: PyPI (0.2.2, 0.2.3) and the MCP registry (0.2.3) are done; the post is mine. On each later release,
     after its PyPI publish, run `mcp-publisher publish` from a checkout of the public tag (login: device flow,
     tell me the code at once).
   - Wave 2 B5 👤: show me w2-001 … w2-010 for review (owner); apply my ok / fix.
   - Wave 2 B2 🧠📄 / 🤖: ask me about dropping NASA-HDBK-2203 (stub, H23) and STD-2818 / 2821 / 2822 (H24) from
     the corpus; H21 (4007A, rebuild heading numbers from the contents order) to a 🤖 worker on invented
     fixtures; then the ECSS valid-ID group (E-HB-10-02A, E-HB-40A, E-ST-50-11C) and the ragged-table group,
     diagnosed on the PDFs first. Per-document and per-table diff on the exact PR head before merging a parser
     change (scratch dump of records / IDs / table hashes on main vs the head); `test_verified_tables_unchanged`
     must hold. One 📄 parse at a time.
   - API pair (`--backend agent` vs `--backend api`) only if ANTHROPIC_API_KEY is set.

3. Worker rules: as in the generic prompt; one 📄 parse at a time. After every merge delete the branch on the
   remote and locally (`gh pr merge <n> --squash --delete-branch`, `git worktree remove <path>`,
   `git branch -D <branch>`, `git fetch --prune`); `--delete-branch` can leave the remote branch when the local
   one is checked out in a worktree: check `git branch -r` and `git push origin --delete <branch>`.
   Round 9 lessons:
   - A parser fix can move documents it was not aimed at (H20 changed 1009A's body start): always diff every
     document, not just the targets.
   - Workers' real-document pytest after a parser change re-parses all 167 documents (13–23 min); give them the
     time, and run full-corpus checks yourself once on the final head.
   - `gh release create --notes-from-tag` fails with `--repo`; use `-F` with the changelog section.
   - Device-flow logins (`mcp-publisher`) time out: start them only when I am at the keyboard.
   - Numbers in eval answers come from tables only; check worker drafts for numbers taken from record text.

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
