import os

from mcp.server.mcpserver import MCPServer

from tethermap.core.db import connect, init_schema
from tethermap.mcp_server.tools import READ_TOOLS, WRITE_TOOLS


def build_server(allow_writes: bool) -> MCPServer:
    server = MCPServer("tethermap")
    tools = READ_TOOLS + (WRITE_TOOLS if allow_writes else [])
    for tool in tools:
        server.tool()(tool)
    return server

def main() -> None:
    with connect() as conn:
        init_schema(conn)
    allow_writes = os.getenv("TETHERMAP_ALLOW_WRITES", "false").lower() == "true"
    build_server(allow_writes).run()


if __name__ == "__main__":
    main()


