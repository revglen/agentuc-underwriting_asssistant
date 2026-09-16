from __future__ import annotations

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from pydantic import BaseModel

from config.settings import settings
from mcp_servers.client import server_url

DOMAIN_SERVERS = {
    "credit_bureau": server_url(settings.credit_bureau_mcp_host, settings.credit_bureau_mcp_port),
    "bank_statement_parser": server_url(settings.bank_statement_parser_mcp_host, settings.bank_statement_parser_mcp_port) ,
    "policy_rules_engine": server_url(settings.policy_rules_engine_mcp_host, settings.policy_rules_engine_mcp_port)
}

def _client() -> MultiServerMCPClient:
    return MultiServerMCPClient({
	    domain: {"transport": "streamable_http", "url": url}
        for domain, url in DOMAIN_SERVERS.items()
	})

async def get_domain_tools() -> dict[str, list[BaseModel]]:
   """Connect to all three MCP servers and return their tools, keyed by domain."""
   client = _client()
   return {domain: await client.get_tools(server_name=domain) for domain in DOMAIN_SERVERS}