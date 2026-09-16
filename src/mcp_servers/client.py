from __future__ import annotations
import json
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client as streamablehttp_client

from errors.exceptions import McpToolError

def server_url(host: str, port: int, path: str="/mcp") -> str:
  return f"http://{host}:{port}{path}"

@asynccontextmanager
async def mcp_session(url: str) -> AsyncIterator[ClientSession]:
    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session

async def list_tools(url: str) -> list[str]:
    async with mcp_session(url) as session:
        result = await session.list_tools()
        return [tool.name for tool in result.tools]

async def call_tool(url: str, tool_name: str, arguments: dict[str, Any]) -> Any:
    """
    Call `tool_name` on the server at `url` and return its result.

    All three mock servers return a single JSON-object text block (no
    structured_output schema is declared), so on success this parses that
    text back into a dict. Raises McpToolError on an MCP-level failure.
    """

    async with mcp_session(url) as session:
        result = await session.call_tool(tool_name, arguments)

    if result.isError:
        message = "; ".join(getattr(block, "text", str(block)) for block in result.content)
        raise McpToolError(f"{tool_name} failed: {message}")

    if result.structuredContent is not None:
        return result.structuredContent

    texts = [block.text for block in result.content if hasattr(block, "text")]
    if len(texts) == 1:
        try:
            return json.loads(texts[0])
        except json.JSONDecodeError:
            return texts[0]

    return texts