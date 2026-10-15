"""server.json (MCP registry) stays in step with pyproject.toml and the README ownership marker."""

import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load():
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    server = json.loads((ROOT / "server.json").read_text(encoding="utf-8"))
    return project, server


def test_versions_match_pyproject():
    project, server = _load()
    assert server["version"] == project["version"]
    assert [p["version"] for p in server["packages"]] == [project["version"]]


def test_package_is_the_pypi_distribution():
    project, server = _load()
    (package,) = server["packages"]
    assert package["registryType"] == "pypi"
    assert package["identifier"] == project["name"]
    assert package["transport"] == {"type": "stdio"}


def test_registry_limits_and_ownership_marker():
    _, server = _load()
    assert len(server["description"]) <= 100
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert f"mcp-name: {server['name']} -->" in readme


def test_package_version_matches_pyproject():
    import spacestd

    project, _ = _load()
    assert spacestd.__version__ == project["version"]
