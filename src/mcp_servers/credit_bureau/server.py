from __future__ import annotations

import logging
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from config.settings import settings
from errors.exceptions import ValidationError
from guardrails.checks import check_credit_score
from mcp_servers.bank_statement_parser.server import _require_applicant_id
from mcp_servers.common import build_server, run_server
from mcp_servers.llm_tools import generate_structured
from observability import metrics
from observability.metrics import metrics

logger=logging.getLogger(__name__)

SERVER_NAME="credit_bureau"
app=build_server(SERVER_NAME, settings.credit_bureau_mcp_port)

def _require_applicant_Id(applicant_id: str) -> None:
    if not applicant_id or not applicant_id.strip():
        raise ValidationError("applicant_id is required")

class _ScoreResult(BaseModel):
    score: int = Field(..., ge=300, le=850)
    rating: str= Field(..., description="One of: poor, fair, good, excellent")

class _ReportResult(BaseModel):
    score: int = Field(..., ge=300, le=850)
    rating: str
    open_accounts: int = Field(..., ge=0)
    delinquencies_last_24_months: int = Field(..., ge=0)
    credit_utilisation_pct: float = Field(..., ge=0, le=100)
    inquires_last_6_months: int = Field(..., ge=0)

@app.tool()
@metrics.track(server=SERVER_NAME,tool="get_credit_score")
async def get_credit_score(applicant_id: str) -> dict:
    """Return the applicant's current credit score and rating band."""

    _require_applicant_id(applicant_id)
    result: _ScoreResult = await generate_structured(
        system_prompt = (
            "You simulate a credit bureau for a synthetic underwriting test "
            "environment. Given an applicant ID, generate a plausible credit "
            "score (300-850) and rating band (poor/fail/good/excellent). Be "
            "internally consistent: the rating must match the score band "
            "(poor <580, fair 580-669, good 670-749, excellent 750+)."
        ),
        user_prompt=f"applicant_id: {applicant_id}",
        response_model=_ScoreResult,
    )

    check_credit_score(result.score, result.rating)

    return {
        "applicanr_id": applicant_id,
        "score": result.score,
        "rating": result.rating,
        "bureau": "mock-bureau",
        "pulled_at": datetime.now(timezone.utc).isoformat(),
    }

@app.tool()
@metrics.track(server=SERVER_NAME, tool="get_credit_report")
async def get_credit_report(applicant_id: str) -> dict:
    """Return a fuller mock credit report: accounts, delinquencies, utilization."""

    _require_applicant_id(applicant_id)
    result: _ReportResult = await generate_structured(
        system_prompt=(
            "You simulate a credit bureau for a synthetic underwriting test "
            "environment. Given an applicant ID, generate a plausible "
            "internally consistent full credit report: score (300-850), "
            "rating matching the score band (poor/fair/good/excellent), "
            "number of open accounts, delinquencies in the last 24 months, "
            "credit utilisation percentage, and inquiries in the last 6 "
            "months. A higher score should generally mean fewer "
            "delinquencies and lower utilisation."
        ),
        user_prompt=f"applicant_id: {applicant_id}",
        response_model=_ReportResult,
    )

    check_credit_score(result.score, result.rating)

    return {
        "applicant_id": applicant_id,
        "score": result.score,
        "rating": result.rating,
        "open_accounts": result.open_accounts,
        "delinquencies_last_24_months": result.delinquencies_last_24_months,
        "credit_utilisation_pct": result.credit_utilisation_pct,
        "inquires_last_6_months": result.inquires_last_6_months,
        "report_date": datetime.now(timezone.utc).isoformat(),
    }

def main() -> None:
   run_server(app, SERVER_NAME, settings.credit_bureau_metrics_port)

if __name__ == "__main__":
    main()