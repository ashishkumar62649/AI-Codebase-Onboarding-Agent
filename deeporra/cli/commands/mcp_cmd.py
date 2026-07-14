"""DeepOrra mcp — start the MCP stdio server."""

from deeporra.mcp_server.__main__ import main as run_mcp_server


def mcp_cmd() -> None:
    """Start MCP stdio server for coding agents."""
    run_mcp_server()
