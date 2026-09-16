from __future__ import annotations
import logging

from mcp.server.fastmcp import FastMCP
from config.settings import settings
from observability import metrics

logger=logging.getLogger(__name__)

def build_server(name: str, mcp_port: int) -> FastMCP:
    return FastMCP(name=name, host=settings.mcp_host, port=mcp_port)

def run_server(app: FastMCP, server_name: str, metrics_port: int) -> None:
    metrics.start_http_server(metrics_port)
    logger.info(
        "%s: /metrics on :%s, MCP endpoint on :%s%s",
        server_name, metrics_port, app.settings.port, app.settings.streamable_http_path,
    )
  
    app.run(transport="streamable-http")