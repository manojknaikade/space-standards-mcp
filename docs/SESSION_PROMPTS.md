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

## Round 8 (prepared 15 Oct 2026)

The generic prompt above with round 8's work and round 7's lessons filled in. Paste it as is; afterwards use the
generic prompt again.

```text
Continue the space-standards-mcp project from the logged progress. You are the ORCHESTRATOR (Opus) on the
local machine; the real standards are in documents/ (gitignored; never commit or upload them).

1. `git checkout main && git pull --ff-only` (stop if the tree is dirty). Check `git remote -v`: `origin` is the private
   `space-standards-mcp-dev` (all development, PRs, docs/PROGRESS.md) and `public` is `space-standards-mcp`, now
   PUBLIC (release commits only, rebuilt with the "Release flow" in docs/PUBLIC_RELEASE_PLAN.md; never force-push,
   never open PRs there). Read CLAUDE.md, docs/PUBLIC_RELEASE_PLAN.md (Stage D, "After going public") and the newest
   entry of docs/PROGRESS.md (round 7). Run `.venv/bin/python -m pytest -q` (420 expected with documents/).
   `gh pr list` (Dependabot PRs may now appear on -dev: review and merge them like worker PRs).

2. Plan round 8 as a table and wait for my "go":
   - D3 🤖 optional: ask me which of PyPI, an MCP registry listing and an announcement post I want; PyPI and the
     registry publish under my name, so the publish itself waits for my "go".
   - 🤖 fs-021: the agent sends a search call with no arguments (r12b and r13) and then hedges a decline. Stop it in
     the agent prompt or the tool schema (required `query`); fixture-only, replay r13's fs-021 through the change.
   - 🧠 release v0.2.2 to `public` with the release flow after those merge (version and CHANGELOG first); the push
     to protected `main` goes through as admin; check the public CI afterwards.
   - Wave 2 B1 🤖📄 only if I ask for it.
   - API pair (`--backend agent` vs `--backend api`) only if ANTHROPIC_API_KEY is set.

3. Worker rules: as in the generic prompt; one 📄 parse at a time. After every merge delete the branch on the
   remote and locally (`gh pr merge <n> --squash --delete-branch`, `git worktree remove <path>`,
   `git branch -D <branch>`, `git fetch --prune`); `--delete-branch` can leave the remote branch when the local
   one is checked out in a worktree: check `git branch -r` and `git push origin --delete <branch>`.
   Round 7 lessons:
   - Re-score stored answers with the current checker before reading a gain as an answer improvement: the whole
     NASA citation-recall gain (0.82 → 0.94) was the checker.
   - A grade that flips on a fresh judge pass of the same answer (fs-018) is judge variance, not a fault.
   - A `cli-agent` run takes about 15 minutes, not an hour.
   - The public repository keeps no PRs: Dependabot security updates run on -dev, and -dev-only files
     (docs/PROGRESS.md, .github/dependabot.yml) are on scripts/release_exclude.txt.

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
