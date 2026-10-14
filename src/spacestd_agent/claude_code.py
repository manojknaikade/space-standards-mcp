"""Claude Code (`claude -p`) as the tool loop, with the space-standards MCP server as its only tools.

Used by the answer eval's `cli` backend (an off-the-shelf client) and by `ClaudeCodeAgent`: the citation gate
of ADR-0005 around the same client. It runs on a logged-in `claude` (subscription or API key), so the gate can be
measured without `ANTHROPIC_API_KEY`. The gate's revision resumes the same Claude Code session.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from spacestd.index import StandardsIndex
from spacestd.tools import record_keys

from .agent import ANSWER_SYSTEM, StandardsAgent

# search settings passed to the MCP server
SEARCH_ENV = ("SPACESTD_EMBED", "SPACESTD_RERANK", "SPACESTD_DENSE_WEIGHT")


def _json_keys(text: str) -> list[str]:
    try:
        return record_keys(json.loads(text))
    except (json.JSONDecodeError, TypeError):
        return []


class ClaudeCode:
    """Runs `claude -p` in an empty working folder (no project CLAUDE.md) with only the MCP tools allowed."""

    def __init__(self, model: str, docs: Path):
        if not shutil.which("claude"):
            sys.exit("claude CLI not found")
        self.model = model
        self.workdir = Path(tempfile.mkdtemp(prefix="spacestd-eval-"))
        self.mcp_config = self.workdir / "mcp.json"
        self.mcp_config.write_text(json.dumps({"mcpServers": {"space-standards": {
            "command": sys.executable, "args": ["-m", "spacestd.server"],
            "env": {"SPACESTD_DOCS": str(Path(docs).resolve()),
                    **{k: os.environ[k] for k in SEARCH_ENV if os.environ.get(k)}}}}}))

    def run(self, args: list[str], prompt: str) -> str:
        proc = subprocess.run(["claude", "-p", "--model", self.model, *args], input=prompt, text=True,
                              capture_output=True, cwd=self.workdir, timeout=900)
        if proc.returncode != 0 and not proc.stdout:
            raise RuntimeError(proc.stderr.strip() or f"claude exited {proc.returncode}")
        return proc.stdout

    def complete(self, system: str, prompt: str) -> str:
        """One reply, no tools (the judge)."""
        out = json.loads(self.run(["--output-format", "json", "--tools", "", "--system-prompt", system], prompt))
        if out.get("is_error"):
            raise RuntimeError(out.get("result") or out.get("terminal_reason"))
        return out.get("result", "")

    def answer(self, prompt: str, resume: str | None = None) -> dict:
        """{answer, tool_calls, retrieved, session_id[, error]}; `resume` continues an earlier session."""
        stdout = self.run(["--output-format", "stream-json", "--verbose", "--tools", "",
                           "--mcp-config", str(self.mcp_config), "--strict-mcp-config",
                           "--allowedTools", "mcp__space-standards__*",
                           "--append-system-prompt", ANSWER_SYSTEM, *(["--resume", resume] if resume else [])],
                          prompt)
        calls, retrieved, answer, error, session = [], [], "", None, None
        for line in stdout.splitlines():
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            session = ev.get("session_id") or session
            for block in (ev.get("message") or {}).get("content") or []:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "tool_use":
                    calls.append({"name": block["name"].split("__")[-1], "input": block.get("input")})
                elif block.get("type") == "tool_result":
                    content = block.get("content")
                    texts = [c.get("text", "") for c in content] if isinstance(content, list) else [content or ""]
                    for t in texts:
                        retrieved += _json_keys(t)
            if ev.get("type") == "result":
                answer = ev.get("result") or ""
                if ev.get("is_error"):
                    error, answer = answer or ev.get("terminal_reason"), ""
        out = {"answer": answer, "tool_calls": calls, "retrieved": list(dict.fromkeys(retrieved)),
               "session_id": session}
        if error:
            out["error"] = error
        return out


class ClaudeCodeAgent(StandardsAgent):
    """The agent's gate (StandardsAgent.ask) with Claude Code as the loop instead of the Messages API."""

    def __init__(self, index: StandardsIndex, client: ClaudeCode, gate: bool = True):
        super().__init__(index, client=client, model=client.model, gate=gate)

    def _loop(self, messages: list, calls: list, retrieved: list) -> tuple[str, str]:
        session = next((m["session_id"] for m in reversed(messages) if m.get("session_id")), None)
        try:
            out = self.client.answer(messages[-1]["content"], resume=session)
        except Exception as e:  # timeouts, CLI failures: reported like a loop error
            return "", f"{type(e).__name__}: {e}"
        calls += out["tool_calls"]
        retrieved += out["retrieved"]
        messages.append({"role": "assistant", "content": out["answer"], "session_id": out["session_id"]})
        return out["answer"], out.get("error") or ""
