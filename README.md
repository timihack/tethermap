# Tethermap

An MCP platform that predicts what a software change will break and reconstructs why a failure happened, with every finding tied to evidence.

Tethermap builds a graph of how services, contracts, endpoints, tests and deployments depend on each other. AI assistants query that graph through MCP tools, so they reason from recorded relationships instead of guessing.

## Status

Phase 1 (shared core) is complete: the graph library, a PostgreSQL schema with versioned history, and an MCP server with two tools.

| Phase | Focus | Status |
| --- | --- | --- |
| 1 | Shared core | Done |
| 2 | Contracts | Planned |
| 3 | Impact | Planned |
| 4 | Trace | Planned |

## Requirements

- Python 3.12
- [uv](https://docs.astral.sh/uv/)
- Docker (for PostgreSQL)

## Setup

```bash
uv sync --python 3.12
docker compose up -d
```

The database listens on host port `5433`. To use a different database, set `DATABASE_URL`:

```bash
export DATABASE_URL="postgresql://user:password@host:port/dbname"
```

## Run

```bash
uv run tethermap
```

The server speaks MCP over stdio and prints nothing while it waits. Press Ctrl+C to stop it.

Tools are read-only by default. To enable `register_service`, set `TETHERMAP_ALLOW_WRITES=true`.

## Tools

| Tool | Access | Description |
| --- | --- | --- |
| `get_service_relationships` | Read | Lists what a service provides and consumes, and what points at it |
| `register_service` | Write | Registers a service and the contracts it provides or consumes |

Links registered through `register_service` are marked `confirmed`. Links Tethermap guesses later will be marked `inferred`.

## Use with Claude Desktop

Add this to `claude_desktop_config.json` (Settings → Developer → Edit Config), using your own absolute path:

```json
{
  "mcpServers": {
    "tethermap": {
      "command": "/absolute/path/to/tethermap/.venv/bin/tethermap",
      "args": [],
      "env": { "TETHERMAP_ALLOW_WRITES": "true" }
    }
  }
}
```

`mcpServers` must be a top-level key in the file. Fully quit and reopen Claude Desktop, then try in a new chat:

> Register a service named orders that provides orders-api and consumes billing-api.

> Show the relationships of orders.

To test without Claude Desktop, use the MCP Inspector:

```bash
npx @modelcontextprotocol/inspector /absolute/path/to/tethermap/.venv/bin/tethermap
```

## Test

```bash
uv run pytest
```

Tests need the database running.

## Project layout

```
src/tethermap/
├── core/          Graph engine, no MCP code
│   ├── models.py  Node and edge kinds
│   ├── schema.sql PostgreSQL schema
│   ├── db.py      Connection and schema setup
│   └── graph.py   Graph store
└── mcp_server/    MCP interface
    ├── tools.py   Tool definitions
    └── server.py  Server and tool registry
tests/
```

## Design principles

- The core engine works without an LLM. MCP is only the interface.
- Every claim links to evidence.
- Dependencies are labelled `confirmed` or `inferred`.
- Risk is an estimate, not a guarantee.
- Tools are read-only unless writes are explicitly enabled.