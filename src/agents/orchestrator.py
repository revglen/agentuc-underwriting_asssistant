from __future__ import annotations

from deepagents import SubAgent, create_deep_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.graph.state import CompiledStateGraph

from agents.llm import get_chat_model
from agents.mcp_tools import get_domain_tools
from agents.schemas import ApplicationDecision

MAIN_SYSTEM_PROMPT = """
You are an underwriting assistant orchestrator.
Given an applicant_id and a requested_amount, evaluate the loan application:
1. Delegate to the credit_bureau subagent to get the applicant's credit score.
2. Delegate to the bank_statement_parser subagent to get their average monthly income and expenses.
3. Only after steps 1 and 2 have both returned real results, delegate to the
   policy_rules_engine subagent, passing it the actual credit score, monthly
   income, monthly expenses and requested_amount to get a decision. Never
   delegate this step with placeholder or missing values.
4. You must finish by calling the required structured output tool with the
   ApplicationDecision fields (applicant_id, decision, reasons, credit_score,
   debt_to_income, requested_amount, max_approved_amount, policy_version) -
   all taken from the subagents' actual results, never invented. Do not write
   the decision as text, markdown, or JSON in your response content - the
   structured output tool call is the only valid way to finish.

When delegating to a subagent, scope its task description to that subagent's own job only - never bundle instructions meant for a different subagent into another one's task description.

Do not skip a step and do not invent figures - every number must come from one of the three subagents.
"""

# MAIN_SYSTEM_PROMPT = """
# You are an underwriting assistant orchestrator.
# Given an applicant_id and a requested_amount, evaluate the loan application:
# 1. Delegate to the credit_bureau subagent to get the applicant's credit score.
# 2. Delegate to the bank_statement_parser subagent to get their average monthly income and expenses.
# 3. Delegate to the policy_rules_engine subagent, passing it the credit score, monthly income, monthly expenses and requested_amount to get a decision
# 4. Return your final answer as an ApplicationDecision: applicant_id, decision
#    ('approved' or 'declined'), reasons (empty if approved), credit_score,
#    debt_to_income, requested_amount, max_approved_amount, and policy_version -
#    all taken from the subagents' actual results, never invented.

# When delegating to a subagent, scope its task description to that subagent's own job only - never bundle instructions meant for a different subagent into another one's task description.

# Do not skip a step and do not invent figures - every number must come from one of the three sugagents. You must follow instruction. Do not hallucinate.
# """
CREDIT_BUREAU_PROMPT = (
    "You retrieve an applicant's credit data. Given an applicant_id, call "
    "get_credit_score (and get_credit_report if more detail is asked for ) "
    "report the score and rating back plainly."
)

BANK_STATEMENT_PROMPT = (
    "You parse an applicant's bank statement. Given an applicant_id, call "
    "parse_bank_statement and report avg_monthly_income and "
    "avg_monthly_expenses back plainly."
)

POLICY_PROMPT = (
    "You evaluate an applicant against underwriting policy. Given an "
    "applicant_id, credit_score, monthly_income, monthly_expenses, and requested_amount, call   evaluate_policy and report the decision, "
    "reasons, and max_approved_amount back plainly."
)

async def build_orchestrator(model: BaseChatModel | None = None) -> CompiledStateGraph:
    """Connects to all three MCP servers and compiles the deep agent graph."""

    tools_by_domain = await get_domain_tools()

    subagents: list[SubAgent] = [
        {
            "name": "credit_bureau",
            "description": "Pulls an applicant's credit score and credit report.",
            "tools": tools_by_domain["credit_bureau"],
            "system_prompt": CREDIT_BUREAU_PROMPT,
        },
        {
            "name": "bank_statement_parser",
            "description": "Parses an applicant's bank statements into income/expense figures.",
            "tools": tools_by_domain["bank_statement_parser"],
            "system_prompt": BANK_STATEMENT_PROMPT,
        },
        {
            "name": "policy_rules_engine",
            "description": "Evaluates an applicant's figures against underwriting policy.",
            "tools": tools_by_domain["policy_rules_engine"],
            "system_prompt": POLICY_PROMPT,
        },
    ]

    return create_deep_agent(
        model = model or get_chat_model(),
        subagents=subagents,
        system_prompt = MAIN_SYSTEM_PROMPT,
        response_format=ApplicationDecision,
        name="underwriting_orchestrator",
        debug=True,
    )