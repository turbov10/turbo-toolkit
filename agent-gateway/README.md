# agent-gateway

Single MCP (Model Context Protocol) server that aggregates every tool in the
[turbo-toolkit](../) monorepo. Each tool directory that ships a `mcp_tools.py`
file is auto-discovered and exposed as MCP tools under a `<namespace>__<tool>`
naming convention.

See [the design spec](../superpowers/specs/2026-07-03-agent-gateway-mcp-integration-design.md)
for the full architecture.

## Install

```bash
cd agent-gateway
python -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## CLI

```bash
.venv/bin/python -m agent_gateway serve         # start stdio MCP server
.venv/bin/python -m agent_gateway list          # list all discovered tools
.venv/bin/python -m agent_gateway call <full_name> --args '<json>'
.venv/bin/python -m agent_gateway info <full_name>
.venv/bin/python -m agent_gateway version
```

## Configure your Agent

In Claude Desktop / Cursor / Cline, add this entry to your MCP config:

```json
{
  "mcpServers": {
    "agent-gateway": {
      "command": "/absolute/path/to/agent-gateway/.venv/bin/python",
      "args": ["-m", "agent_gateway", "serve"]
    }
  }
}
```
