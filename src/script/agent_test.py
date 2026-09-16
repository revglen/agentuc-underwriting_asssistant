"""
Standalone test for the deep agent orchestrator - bypasses FastAPI entirely,
so an agent problem isn't mixed up with an API problem.

Requires all three MCP servers already running (the orchestrator connects to
them at startup) and a reachable LLM per your PROVIDER setting.

    PYTHONPATH=src python3 src/script/agent_test.py
    PYTHONPATH=src python3 src/script/agent_test.py applicant-1 20000 6
"""
import asyncio
import sys

from langchain_core.messages import HumanMessage

from agents.orchestrator import build_orchestrator
from config.settings import settings


async def main() -> None:
    applicant_id = sys.argv[1] if len(sys.argv) > 1 else "test-applicant-1"
    requested_amount = float(sys.argv[2]) if len(sys.argv) > 2 else 20000
    months = int(sys.argv[3]) if len(sys.argv) > 3 else 6

    print(f"provider={settings.provider} model={settings.model_name}")
    print("connecting to MCP servers and building the graph...")
    graph = await build_orchestrator()
    print("graph built.\n")

    message = (
        f"Evaluate applicant_id={applicant_id!r}, requested_amount={requested_amount}, "
        f"using {months} months of bank statements."
    )
    print(f"invoking: {message}\n")

    result = await graph.ainvoke({"messages": [HumanMessage(content=message)]})

    print("--- full message trace (every LLM turn and tool call/response) ---")
    for m in result["messages"]:
        print(f"[{m.type}] {m.content!r}")
        if getattr(m, "tool_calls", None):
            print(f"    tool_calls: {m.tool_calls}")

    print("\n--- structured_response (the typed final decision) ---")
    print(result.get("structured_response"))


if __name__ == "__main__":
    asyncio.run(main())