# documents/ (local only, gitignored)

Put the standards you downloaded here. Nothing in this folder except this README is committed.

## v1 core (launcher and fairing structures)

| Standard | Where to get it |
| --- | --- |
| ECSS-E-ST-32 — Structural general requirements | https://ecss.nl (free registration), .docx where available |
| ECSS-E-ST-32-10 — Structural factors of safety for spaceflight hardware | https://ecss.nl |
| ECSS-E-ST-32-01 — Fracture control | https://ecss.nl |
| NASA-STD-5001 — Structural design and test factors of safety for spaceflight hardware | NASA Technical Standards System (standards.nasa.gov) |
| NASA-STD-5019 — Fracture control requirements for spaceflight hardware | NASA Technical Standards System |

Take the latest issue/revision unless your programme is contracted to an older one, Only use NASA documents marked for public release.

## File names and document identity

Keep the files as downloaded; no renaming is needed. The standard number and issue are read from the Word page
header or the cover page (e.g. `ECSS-E-ST-32-10C Rev.2`, `NASA-STD-5019A w/Change 4`), else from the file name
(`ECSS-E-ST-32C_Rev.115November2008.pdf` -> `ECSS-E-ST-32C`, `Rev.1`). A corrigendum is part of the issue
(`ECSS-E-ST-32-10C Rev.2 Corrigendum 1` -> `Rev.2 Corr.1`). Check what was detected with the
`list_documents` tool. If neither works, the server logs a warning and you can add a sidecar.

## Sidecar metadata (optional)

`<file name without extension>.meta.yaml` next to a document overrides any detected field:

```yaml
doc_id: ECSS-E-ST-32-10C
issue: Rev.1
title: Structural factors of safety for spaceflight hardware
```

## Folders, bundles and what gets loaded

Sub-folders are fine: drop the ECSS bundles and the NASA download in as they come. `python -m spacestd.catalogue
documents` lists every standard found (one entry per document; PDF and Word copies, duplicates and parts are
sorted out) and which ones are loaded. A file directly in `documents/` wins over a copy in a sub-folder; files
under a folder named `superseded…` are never loaded. A NASA download manifest (`*.json` with a `standards` list,
as written by `scripts/download_nasa_standards.py`) supplies titles and IDs the file names lack.

`python scripts/download_nasa_standards.py documents/nasa` fetches the public NASA standards politely (project
User-Agent, robots.txt, one request every 2 s) and skips PDFs already in the folder; `--only NASA-STD-5001`
limits it, `--dry-run` only lists, `--force` re-downloads. Its docstring documents the manifest format.

Without `corpus.yaml`, only files directly in `documents/` are loaded. To load from the bundles, list doc-ID
patterns (case-insensitive, `*` wildcards; `"*"` loads everything) in `documents/corpus.yaml`:

```yaml
load:
  - ECSS-E-ST-32*
  - ECSS-E-ST-10-03C
  - NASA-STD-5*
exclude:            # optional: drop documents the load patterns would pick up
  - NASA-STD-2818*
```

Supported formats: `.pdf` (preferred; ECSS and NASA), `.docx` / `.doc` (ECSS Word files are read through
LibreOffice, which must be installed: `soffice` on the PATH), `.txt`, `.md`. When the same `doc_id` exists as
PDF and Word, the PDF is used. Parsed documents are cached in `documents/.spacestd-cache/` (also local only);
the cache is rebuilt automatically when a file or the parser changes.
