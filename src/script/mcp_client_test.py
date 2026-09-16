"""
Connects to one MCP server, discovers its tools, and calls every one of them
with a fixed set of test parameters - no manual args needed per tool.

    PYTHONPATH=src python3 src/script/mcp_client_test.py credit_bureau
    PYTHONPATH=src python3 src/script/mcp_client_test.py bank_statement_parser
    PYTHONPATH=src python3 src/script/mcp_client_test.py policy_rules_engine
"""
import asyncio
import sys

from config.settings import settings
from mcp_servers.client import McpToolError, call_tool, list_tools, server_url

SERVER_PORTS = {
    "credit_bureau": settings.credit_bureau_mcp_port,
    "bank_statement_parser": settings.bank_statement_parser_mcp_port,
    "policy_rules_engine": settings.policy_rules_engine_mcp_port,
}

# One fixed test payload per known tool name, across all three servers.
TEST_ARGS = {
    "get_credit_score": {"applicant_id": "test-applicant-1"},
    "get_credit_report": {"applicant_id": "test-applicant-1"},
    "parse_bank_statement": {"applicant_id": "test-applicant-1", "months": 3},
    "get_transaction_summary": {"applicant_id": "test-applicant-1"},
    "evaluate_policy": {
        "applicant_id": "test-applicant-1",
        "credit_score": 700,
        "monthly_income": 5000,
        "monthly_expenses": 1500,
        "requested_amount": 20000,
    },
    "get_policy_rules": {},
}


async def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in SERVER_PORTS:
        print(f"usage: mcp_client_test.py <{'|'.join(SERVER_PORTS)}>")
        return

    server_name = sys.argv[1]
    url = server_url("127.0.0.1", SERVER_PORTS[server_name])

    tools = await list_tools(url)
    print(f"{server_name}: {len(tools)} tool(s) - {tools}\n")

    for tool_name in tools:
        args = TEST_ARGS.get(tool_name)
        if args is None:
            print(f"[SKIP] {tool_name}: no test args defined for this tool")
            continue
        print(f"[CALL] {tool_name}({args})")
        try:
            result = await call_tool(url, tool_name, args)
            print(f"[OK]   {result}\n")
        except McpToolError as exc:
            print(f"[FAIL] {exc}\n")


if __name__ == "__main__":
    asyncio.run(main())