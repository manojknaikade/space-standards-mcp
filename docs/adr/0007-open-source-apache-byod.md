# ADR-0007: Open-source the code under Apache-2.0, bring your own documents, publish from a fresh repository

Status: accepted · 2026-10-09 · owner decisions C1 and C5 of the [release plan](../PUBLIC_RELEASE_PLAN.md);
builds on [ADR-0002](0002-bring-your-own-documents.md)

## Context

The roadmap left one open decision before a release: keep the project private, open-source it, or turn it into
a product. What the project is now:

- The reusable part is code: parsers, catalogue, index, tools, citation gate, MCP server, thin agent, evals.
  None of it is worth anything without the standards, and the standards cannot be shipped with it: ECSS
  documents are licensed to the registered user, and NASA documents carry their own distribution statements
  (ADR-0002).
- Bring-your-own-documents already works: `documents/` is gitignored, tests use an invented `DEMO` standard,
  eval files hold IDs and paraphrases, eval answers (`eval/runs/`) are gitignored, and a text audit of the
  release tree (C3, run in C4) found and removed the three standards sentences that had slipped in.
- The history of this repository is not clean in the same way. Those three sentences were committed before C4
  paraphrased them, and older commits carry dated working notes. GitHub keeps every merged PR's commits
  reachable under `refs/pull/*`, so squashing or force-pushing `main` here would still publish the old history
  once the repository is made public.

## Options considered

1. **Stay private.** No licence work, but no users or contributors beyond the owner, and the work cannot be
   shown or reused.
2. **Product (hosted service).** Answering for third parties from a hosted corpus means redistributing
   standards text the operator is only licensed to use themselves. Not viable without agreements with the
   publishers.
3. **Open-source the code, documents stay with each user.** Each user downloads the standards under their own
   registration or from the public NASA site, and the software parses them locally.

Licence for option 3: a permissive licence fits a tool meant to be embedded in other MCP clients and
engineering workflows. **Apache-2.0** rather than MIT for its explicit patent grant and its `NOTICE` file, which
carries the independence and no-standards-text statements with every redistribution.

## Decision

1. **Open-source the code under Apache-2.0** (option 3). `LICENSE` and `NOTICE` cover everything in the
   repository: code, tests and their invented fixtures, eval questions and scripts, docs. Contributions come in
   under the same licence (inbound = outbound, `CONTRIBUTING.md`).
2. **Bring your own documents stays the rule** (ADR-0002, unchanged). The licence covers no standards text,
   because the repository holds none. Users get ECSS documents from ecss.nl after registration and NASA
   documents from standards.nasa.gov (`scripts/download_nasa_standards.py`, which never fetches ECSS documents).
   Guards: the text audit (`scripts/audit_standards_text.py`) on the release tree at D1, and a CI check that
   fails on committed document files or anything under `documents/` but its README (C6).
3. **Publish from a fresh repository holding one squashed commit** (D1a). This repository is renamed
   `space-standards-mcp-dev` and stays private with its full history and PRs. A new `space-standards-mcp`
   receives one commit with the audited release tree, authored by the owner and tagged `v0.2.0`, and all
   later work happens there. It starts private and is made public at D2, after the release gate (stage A, wave 1
   loaded and evaluated, licence and text audit clean).
4. **A product is not pursued.** A hosted or commercial offer would need its own ADR and the publishers'
   agreement first.

## Consequences

- C2 is done under this decision: `LICENSE`, `NOTICE`, the README disclaimer, `CONTRIBUTING.md`, `SECURITY.md`
  and PR / issue templates with a "contains no standards text" box. C9 adds the licence to the package metadata.
- ADR-0002's checks before any public release become preconditions of D2 (👤): read the current ECSS terms of
  use on ecss.nl, and re-check the distribution statement of every NASA document the docs or evals name.
- The text audit and the CI guard protect the public tree from the first commit on; a slip after going public
  would be in public history, so `SECURITY.md` asks for committed standards text to be reported privately.
- Links into this repository's PRs and dated private notes do not resolve or do not fit in
  the public repository. C10 tidies the internal docs before D1a; the full record stays in the private `-dev`
  repository. The round log `docs/PROGRESS.md` is excluded from the public tree via `scripts/release_exclude.txt`,
  which D1a applies and `scripts/check_release_tree.py --release` verifies.
- Work after D1a uses the new repository as `origin` (all local since ADR-0008); its GitHub settings (labels used by the issue forms,
  branch protection, secret scanning, private vulnerability reporting) are set up at D2.
- Contributors cannot add standards text even as test data: fixtures stay invented (`CONTRIBUTING.md`), and
  parsing problems are reported by document ID, page and pattern, without quoting.
