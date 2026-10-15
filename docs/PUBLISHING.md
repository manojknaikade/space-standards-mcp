# Publishing checklist (maintainers)

Order: PyPI first, then the MCP registry (the registry checks that the PyPI package exists and carries the
ownership marker). Everything happens from the public repository `manojknaikade/space-standards-mcp`; the workflow
`.github/workflows/publish.yml` does nothing in any other repository.

## One-time setup

1. **PyPI account** with 2FA. The name `space-standards-mcp` was free on PyPI on 15 October 2026.
2. **Pending trusted publisher** (the project does not exist yet): pypi.org, Account, Publishing, "Add a new
   pending publisher":
   - PyPI project name: `space-standards-mcp`
   - Owner: `manojknaikade`, repository: `space-standards-mcp`
   - Workflow name: `publish.yml`
   - Environment name: `pypi`
3. **GitHub environment**: public repository, Settings, Environments, New environment `pypi`. Optionally add
   yourself as a required reviewer, so a publish waits for your approval.
4. Install `mcp-publisher` (`brew install mcp-publisher`, or the release binary from
   github.com/modelcontextprotocol/registry).

## Each release

1. On -dev: bump `version` in `pyproject.toml`, `src/spacestd/__init__.py` and `server.json` (two places there: `version` and
   `packages[0].version`; `tests/test_server_json.py` fails if they differ), update `CHANGELOG.md`, merge.
2. Rebuild the release commit and tag it `vX.Y.Z` as in docs/PUBLIC_RELEASE_PLAN.md ("Release flow") and push the
   commit and the tag to `public`. The tag push alone publishes nothing.
3. To publish that version, create a GitHub Release from the tag on the public repository
   (`gh release create vX.Y.Z --repo manojknaikade/space-standards-mcp --notes-from-tag`, or the web UI). Publishing
   the release starts "Publish to PyPI": it checks that the tag equals the `pyproject.toml` version, builds the
   sdist and wheel, runs `twine check`, then publishes with Trusted Publishing (approve the `pypi` environment if
   you set a reviewer). The first publish creates the project. A manual run (workflow_dispatch) uploads whatever the
   chosen ref builds; PyPI refuses a version that already exists.
4. Check `https://pypi.org/project/space-standards-mcp/`: the README renders and contains the line
   `mcp-name: io.github.manojknaikade/space-standards-mcp` (an HTML comment, invisible on the page).
5. Once the package is live, update the README "Install without a clone" section (it still says the package is
   not on PyPI) and release again, or do that in the first release if you publish later.

## MCP registry

From a checkout of the release tag, at the repository root (where `server.json` is):

```bash
mcp-publisher validate        # if your mcp-publisher version has it
mcp-publisher login github    # device flow in the browser; the name io.github.manojknaikade/* needs this GitHub account
mcp-publisher publish
```

Then check `https://registry.modelcontextprotocol.io/v0/servers?search=space-standards`. The registry stores
metadata only; a new version needs a new `server.json` version and another `mcp-publisher publish`.

## Local dry run (no upload)

```bash
python -m pip install build twine
python -m build && twine check dist/*
```

The sdist holds `src/`, the README, licence files, changelog and `pyproject.toml` only (no tests, eval data or
documents).
