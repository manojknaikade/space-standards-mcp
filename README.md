# space-standards-mcp

<!-- mcp-name: io.github.manojknaikade/space-standards-mcp -->

An MCP server (and a thin optional agent) that answers questions about **ECSS** and **NASA** space standards with
**exact, requirement-level citations**: every result names the document, issue and requirement ID, or the answer is
"not covered". You bring the standards; nothing from them is stored in this repository. It is aimed at launcher and
payload-fairing structures first (factors of safety, fracture control, loads, shock, vibroacoustics) and is built to
grow to the whole ECSS and NASA set.

> **Independent project.** Not affiliated with or endorsed by the European Space Agency (ESA), the ECSS Secretariat
> or NASA. The ECSS, ESA and NASA names and the names of their standards belong to their owners and are used here
> only to identify the documents the software works with.

## 60-second demo (invented fixtures)

The repository ships three invented demo standards and a demo handbook in `tests/fixtures/` (made-up text and numbers, so you can try
everything without any real document).

```bash
git clone https://github.com/manojknaikade/space-standards-mcp.git && cd space-standards-mcp
python -m venv .venv && source .venv/bin/activate      # Python 3.11+
pip install -e ".[dev]"
pytest -q                                              # fixture tests; real-document tests skip without documents/

# retrieval eval on the demo standards: expected recall@5 1.00 over 4 questions
python eval/run_retrieval_eval.py --docs tests/fixtures --questions eval/demo_questions.yaml

# the MCP server over the demo standards (stdio; an MCP client talks to it)
SPACESTD_DOCS=tests/fixtures python -m spacestd.server
```

Connect a client (below) to that server and ask, for example, "which factor of safety applies to a metallic
fairing in DEMO-E-ST-98C?". The answer comes back with a citation such as `DEMO-E-ST-98C Rev.2, 4.1.2a`.

## Use your own documents

No standards text is distributed here. Download the documents yourself and put them in `documents/` (gitignored)
or any folder you point `SPACESTD_DOCS` at:

- **ECSS:** <https://ecss.nl> (free registration); Word or PDF.
- **NASA:** the NASA Technical Standards System, <https://standards.nasa.gov>. `python scripts/download_nasa_standards.py documents/nasa`
  fetches the public ones politely (robots.txt, one request every 2 s); `--dry-run` only lists them.

Then:

```bash
python -m spacestd.catalogue documents      # what was found, and what is loaded
python -m spacestd.health documents         # parse every document, set its tier, write eval/CORPUS_HEALTH.md
```

`documents/corpus.yaml` selects what is loaded (doc-ID patterns with `*`, see
[ADR-0006](https://github.com/manojknaikade/space-standards-mcp/blob/main/docs/adr/0006-full-corpus-parse-tiers.md)); without it only files directly in `documents/` load:

```yaml
load:
  - ECSS-E-ST-32*
  - NASA-STD-5*
```

File naming, sidecar metadata and formats (PDF preferred; Word files need LibreOffice) are described in
[documents/README.md](https://github.com/manojknaikade/space-standards-mcp/blob/main/documents/README.md). Parsed documents are cached in `documents/.spacestd-cache/`.
The standards remain subject to their publishers' terms of use.

## Install without a clone

The package is not on PyPI yet; install it from git:

```bash
uvx --from git+https://github.com/manojknaikade/space-standards-mcp space-standards-mcp
pipx install git+https://github.com/manojknaikade/space-standards-mcp
```

The `space-standards-mcp` command starts the server (stdio) and reads `SPACESTD_DOCS`.

## Connect an MCP client

Use an absolute path to the Python that has the package installed, and to your documents folder.

With `uvx`, a client can start the server without a local install, e.g. in Claude Desktop:
`{"command": "uvx", "args": ["--from", "git+https://github.com/manojknaikade/space-standards-mcp", "space-standards-mcp"], "env": {"SPACESTD_DOCS": "/abs/path/to/documents"}}`.

**Claude Code**

```bash
claude mcp add space-standards --env SPACESTD_DOCS=/abs/path/to/documents -- /abs/path/to/.venv/bin/python -m spacestd.server
```

**Claude Desktop** (`claude_desktop_config.json`)

```json
{
  "mcpServers": {
    "space-standards": {
      "command": "/abs/path/to/.venv/bin/python",
      "args": ["-m", "spacestd.server"],
      "env": { "SPACESTD_DOCS": "/abs/path/to/documents" }
    }
  }
}
```

**VS Code** (`.vscode/mcp.json`)

```json
{
  "servers": {
    "space-standards": {
      "type": "stdio",
      "command": "/abs/path/to/.venv/bin/python",
      "args": ["-m", "spacestd.server"],
      "env": { "SPACESTD_DOCS": "/abs/path/to/documents" }
    }
  }
}
```

## Tools

| Tool | What it does |
| --- | --- |
| `list_documents` | Loaded standards and issues with family, type, discipline, parse tier, record counts and tables; filters; can also list documents present but not loaded |
| `get_requirement` | Exact record for a document and requirement ID |
| `search_requirements` | BM25 keyword search over requirements and table rows, with neighbouring records per hit; reports named standards that are not loaded |
| `get_table` | A table (e.g. factors of safety) as structured rows with labels, cell text, parsed value and footnotes |
| `get_references` | Standards and clauses a requirement points to |
| `compare_topic` | One topic searched separately in each standard, grouped ECSS / NASA, with a coverage rating per standard |
| `get_section_outline` | A standard's table of contents; for one clause its record IDs and tables (no requirement text) |

Every record carries its `kind` (requirement, recommendation, permission, guidance, deleted) and a `citation`.

### Optional: hybrid search and the agent

`pip install -e ".[embed]"` and `SPACESTD_EMBED=default` add embedding ranking fused with BM25 (opt-in, see
[eval/RESULTS.md](https://github.com/manojknaikade/space-standards-mcp/blob/main/eval/RESULTS.md)). `pip install -e ".[agent]"` adds `python -m spacestd_agent "<question>" --docs documents`,
the same tools in a tool-calling loop with a citation gate that checks each draft for invented IDs and numbers not
found in the retrieved records ([ADR-0005](https://github.com/manojknaikade/space-standards-mcp/blob/main/docs/adr/0005-agent-loop.md)); it needs an Anthropic API key.

## Parse tiers

Documents differ in how well they parse, so each carries a tier ([ADR-0006](https://github.com/manojknaikade/space-standards-mcp/blob/main/docs/adr/0006-full-corpus-parse-tiers.md)):

- **verified**: checked by hand against the source (requirement counts, IDs, tables).
- **checked**: passes the automatic health checks (`python -m spacestd.health`), not reviewed by hand.
- **unchecked**: parsed, but no check has passed; treat results as leads.

Records, tables and rows carry their `tier` and `page`. Numbers taken from tables of documents below `verified`
come with a "check against the source, page N" flag, and the citation gate only accepts such a number when the
answer repeats it. Always confirm a number in the source.

## Evaluation and its limits

Two evals run on a 57-question set (17 numeric, 17 lookup, 7 classification, 5 compare, 11 not covered). Numbers
from [eval/RESULTS.md](https://github.com/manojknaikade/space-standards-mcp/blob/main/eval/RESULTS.md), on the 7 hand-verified standards:

| Measure | Value |
| --- | --- |
| retrieval recall@5 / @20 (46 scored questions) | 0.64 / 0.89 (0.74 at @5 counting neighbouring records) |
| table recall@5: row hit / reachable (10 questions) | 0.50 / 0.85 |
| answers, independent judge, plain client: correct / partial / wrong | 52 / 4 / 1 |
| answers, gated agent: correct / partial / wrong | 49 / 7 / 1 |
| invented requirement IDs | 0 |
| "not covered" questions declined without numbers | 11 / 11 |

Limits: the question set is small and written by one author; the first 21 questions had domain review and the
later additions did not; one model family answers and judges; retrieval is keyword-based and misses paraphrases
(hybrid search helps only partly); and the figures say nothing about the many documents at tier `checked` or
`unchecked`. Treat answers as aids for locating requirements, not as authority.

## Disclaimer

- **No standards text is included.** You download the standards yourself.
- **Answers are aids, not authority.** They are not a substitute for the applicable standard in the issue your
  project is contracted to, with its tailoring. Verify any requirement, factor or test level against the source.

## Project docs

[Roadmap](https://github.com/manojknaikade/space-standards-mcp/blob/main/docs/ROADMAP.md) · [Release plan](https://github.com/manojknaikade/space-standards-mcp/blob/main/docs/PUBLIC_RELEASE_PLAN.md) · [Project brief](https://github.com/manojknaikade/space-standards-mcp/blob/main/docs/PROJECT_BRIEF.md) ·
[Architecture](https://github.com/manojknaikade/space-standards-mcp/blob/main/docs/ARCHITECTURE.md) · [Decision records](https://github.com/manojknaikade/space-standards-mcp/tree/main/docs/adr/) · [Contributing](https://github.com/manojknaikade/space-standards-mcp/blob/main/CONTRIBUTING.md) ·
[Security](https://github.com/manojknaikade/space-standards-mcp/blob/main/SECURITY.md)

## Licence

The code is licensed under the [Apache License 2.0](https://github.com/manojknaikade/space-standards-mcp/blob/main/LICENSE); see also [NOTICE](https://github.com/manojknaikade/space-standards-mcp/blob/main/NOTICE) and
[ADR-0007](https://github.com/manojknaikade/space-standards-mcp/blob/main/docs/adr/0007-open-source-apache-byod.md).
