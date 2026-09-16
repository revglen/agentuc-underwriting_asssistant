"""
Bank statement parser MCP server.

Tools call the LLM (structured output) to produce the parsed figures, in
place of the earlier hash-based mock generator. No real statement files are
read; the LLM stands in for that parsing step in this synthetic environment.
"""

from __future__ import annotations
import logging
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from config.settings import settings
from errors.exceptions import ValidationError
from guardrails.checks import check_bank_statement, check_transaction_summary
from mcp_servers.common import build_server, metrics, run_server
from mcp_servers.llm_tools import generate_structured
from observability.metrics import metrics

logger = logging.getLogger(__name__)
SERVER_NAME = "bank_statement_parser"
app = build_server(SERVER_NAME, settings.bank_statement_parser_mcp_port)

def _require_applicant_id(applicant_id: str) -> None:
    if not applicant_id or not applicant_id.strip():
        raise ValidationError("Applicant_id is required")

class _StatementResult(BaseModel):
    avg_monthly_income: float = Field(..., gt=0)
    avg_monthly_expenses: float = Field(..., ge=0)
    avg_closing_balance: float
    overdraft_count: int = Field(..., ge=0)

class _TransactionSummaryResult(BaseModel):
    category_breakdown: dict[str, float]
    total_inflow: float = Field(..., ge=0)
    total_outflow: float = Field(..., ge=0)

@app.tool()
@metrics.track(server=SERVER_NAME, tool="parse_bank_statement")
async def parse_bank_statement(applicant_id: str, months: int = 3) -> dict:
    """Parse the applicant's last N months of bank statements into a summary."""
    _require_applicant_id(applicant_id)
    if months < 1 or months > 24:
        raise ValidationError("months must be between 1 and 24")

    result: _StatementResult = await generate_structured(
        system_prompt=(
            "You simulate parsing an applicant's bank statements for a "
            "synthetic underwriting test environment. Given an applicant id  "
            "and a number of months, generate plausible, internally "
            "consistent figures: average monthly income, average monthly "
            "expenses (should generally be less than income for a "
            "financially stable applicant, but not always), average closing " 
            "balance, and count of overdrafts."
        ),
        user_prompt=f"applicant_id: {applicant_id}, months: {months}",
        response_model=_StatementResult,
    )

    check_bank_statement(result.avg_monthly_income, result.avg_monthly_expenses)

    return {
        "applicant_id": applicant_id,
        "months_covered": months,
        "statement_count": months,
        "avg_monthly_income": result.avg_monthly_income,
        "avg_monthly_expenses": result.avg_monthly_expenses,
        "avg_clsoing_balance": result.overdraft_count,
        "parsed_at": datetime.now(timezone.utc).isoformat(),
    }

@app.tool()
@metrics.track(server=SERVER_NAME, tool="get_transaction_summary")
async def get_transaction_summary(applicant_id: str) -> dict:
    """Return a category-level breakdown of the applicant's recent transactions."""

    _require_applicant_id(applicant_id)
    result: _TransactionSummaryResult = await generate_structured(
        system_prompt=(
            "You simulate a transaction-category breakdown for an "
            "applicant's recent bank activity in a synthetic underwriting "
            "test environment. Generate a category_breakdown dict covering  "
            "categories like rent_or_mortgage, utilities, groceries, "
            "transport, discreptionary, and existing_debt, each mapped to a "
            "plausible monthly amount. total_outflow should equal the sum "
            "of the breakdown, and total_inflow should be somewhat higher "
            "than total_outflow"
        ),
        user_prompt=f"applicant_id: {applicant_id}",
        response_model=_TransactionSummaryResult,
    )

    check_transaction_summary(result.category_breakdown, result.total_outflow)

    return {
        "applicant_id": applicant_id,
        "category_breakdown": result.category_breakdown,
        "total_inflow": result.total_inflow,
        "total_outflow": result.total_outflow,
        "summarszed_at": datetime.now(timezone.utc).isoformat(),
    }

def mcp_main() -> None:
    run_server(app, SERVER_NAME, settings.bank_statement_parser_metrics_port)


if __name__ == "__main__":
    mcp_main()
