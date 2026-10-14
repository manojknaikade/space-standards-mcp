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

## Round 7 (prepared 14 Oct 2026)

The generic prompt above with round 7's work and round 6's lessons filled in. Paste it as is; afterwards use the
generic prompt again.

```text
Continue the space-standards-mcp project from the logged progress. You are the ORCHESTRATOR (Opus) on the
local machine; the real standards are in documents/ (gitignored; never commit or upload them).

1. `git checkout main && git pull --ff-only` (stop if the tree is dirty). Check `git remote -v`: `origin` is the private
   `space-standards-mcp-dev` (all development, PRs, docs/PROGRESS.md) and `public` is `space-standards-mcp`
   (release commits only, rebuilt with the "Release flow" in docs/PUBLIC_RELEASE_PLAN.md). Read CLAUDE.md, docs/PUBLIC_RELEASE_PLAN.md (Stage D, "Order at a glance") and the newest
   entry of docs/PROGRESS.md (round 6). Run `.venv/bin/python -m pytest -q` (419 expected
   with documents/). `gh pr list` (the default repository is -dev; the public one has no PRs).

2. Plan round 7 as a table and wait for my "go":
   - D2 👤: prepare the ADR-0002 / ADR-0007 checks (current ECSS terms of use on ecss.nl; the distribution
     statement of every NASA document the docs or evals name: list them with where they are named), then wait for
     my "go" before changing visibility, branch protection, Dependabot, secret scanning or vulnerability reporting.
   - 🤖📄 one `cli-agent` answer run on the round-6 code (`generate`, then `score`), compared per question with
     r12: citation recall for tagless NASA documents was undercounted before #76.
   - API pair (`--backend agent` vs `--backend api`) only if ANTHROPIC_API_KEY is set.
   - D3 🤖 only after D2.

3. Worker rules: as in the generic prompt; one 📄 parse at a time. After every merge delete the branch on the
   remote and locally (`gh pr merge <n> --squash --delete-branch`, `git worktree remove <path>`,
   `git branch -D <branch>`, `git fetch --prune`); `--delete-branch` can leave the remote branch when the local
   one is checked out in a worktree: check `git branch -r` and `git push origin --delete <branch>`.
   Round 6 lessons:
   - Diagnose a reported eval failure on the stored answers before writing the worker spec: two of three
     round-5 "bugs" were checker misreadings (a launcher name, an unrecognised citation form), not agent faults.
   - Replay stored answers through a checker change (main replays unchanged first, then the PR head) and review
     every question that changes.
   - Parallel PRs that append to the same test file conflict; rebase the later one before merging.
   - Health over the whole corpus (`--corpus all`) takes about 26 minutes: run it in the background.
   - A small search gain next to a recall cliff is not worth merging (#77).

4. Close the round with one tracking PR (plan and ROADMAP boxes, eval/RESULTS.md if runs were made, one
   newest-first PROGRESS entry ending with "Next:"). Merge it and delete its branch, remote and local;
   `git branch -a` and `git worktree list` should show only main. When preparing the next round's prompt,
   keep this branch-deletion rule in it.
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
