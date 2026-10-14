## What and why

<!-- What does this change, and why? Link the issue or release-plan step if there is one. -->

## How it was tested

<!-- Commands you ran, e.g. `python -m pytest -q` and the fixture evals from CONTRIBUTING.md. -->

## Checklist

- [ ] **Contains no standards text**: no sentences, table rows or figures copied from an ECSS or NASA document
      in code, tests, eval files, docs, this description or the commit messages (ADR-0002)
- [ ] New or changed tests use invented text in `tests/fixtures/` only
- [ ] No invented requirement IDs presented as real; numbers about real documents come from the source tables
- [ ] Nothing added under `documents/` and no `.pdf` / `.doc` / `.docx` / `.pkl` files
- [ ] `python -m pytest -q` passes
