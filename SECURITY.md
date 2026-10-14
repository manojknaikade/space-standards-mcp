# Security policy

## Supported versions

Only the latest release (and `main`) receives fixes.

## Reporting a vulnerability

Please report security problems privately through GitHub's
[private vulnerability reporting](https://github.com/manojknaikade/space-standards-mcp/security/advisories/new)
(the repository's **Security** tab, then **Report a vulnerability**). Do not open a public issue.

Include what is affected (MCP server, agent, eval scripts, download script), how to reproduce it, and the
impact you expect. You should get a first answer within 7 days.

Examples of what counts:

- a way for a crafted document or MCP request to read or write files outside the configured documents folder,
  or to run code;
- leaking an API key or other secret through logs, tool results or eval outputs;
- a dependency with a known vulnerability that this project actually reaches.

## Standards text committed by mistake

The repository must not contain text from ECSS or NASA standards ([ADR-0002](docs/adr/0002-bring-your-own-documents.md)).
If you find some, report it through the same private channel and give only the file and line. Do not quote it in
a public issue or PR. It will be removed promptly.

## Out of scope

- Wrong or incomplete answers about a standard: open a normal issue (without quoting the standard). Answers are
  aids for locating requirements; always verify against the applicable standard.
- Problems in the standards themselves, or in ecss.nl or standards.nasa.gov: contact their owners.
