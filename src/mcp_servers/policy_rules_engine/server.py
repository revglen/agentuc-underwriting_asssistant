from __future__ import annotations

import logging
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from config.settings import settings
from errors.exceptions import ValidationError
from guardrails.checks import check_policy_decision
from mcp_servers.common import build_server, run_server
from mcp_servers.llm_tools import generate_structured
from observability.metrics import metrics

logger = logging.getLogger(__name__)

SERVER_NAME="policy_rules_engine"
app=build_server(SERVER_NAME, settings.policy_rules_engine_mcp_port)

POLICY_VERSION="2026.1"
MIN_CREDIT_SCORE=620
MAX_DEBT_TO_INCOME=0.45
MIN_MONTHLY_INCOME=1500

class _DecisionResult(BaseModel):
    decision: str = Field(..., description="Either 'approved' or 'declined'")
    reasons: list[str] = Field(default_factory=list, description="Empty if approved")
    max_approved_amount: float = Field(..., ge=0)

@app.tool()
@metrics.track(server=SERVER_NAME, tool="evaluate_policy")
async def evaluate_policy(
    applicant_id: str,
    credit_score: int,
    monthly_income: float,
    monthly_expenses: float,
    requested_amount: float,
    ) -> dict:
    """Evaluate an applicant against the current policy guidance and return a decision."""
    if not applicant_id or not applicant_id.strip():
        raise ValidationError("applicant_id is required")

    if monthly_income <= 0:
        raise ValidationError("monthly_income must be positive")

    debt_to_income = round(monthly_expenses / monthly_income, 3)
    result: _DecisionResult = await generate_structured(
        system_prompt=(
            "You are an underwriting policy engine. Weigh the applicant's "
            "figures against this guidance and decide 'approved' or 'declined':\n"
            f"- minimum credit score: {MIN_CREDIT_SCORE}\n"
            f"- maximium debt_to_income ratio: {MAX_DEBT_TO_INCOME}\n"
            f"- minimum monthly income: {MIN_MONTHLY_INCOME}\n"
            "If declines, give specific reasons naming which guidance was "
            "violated and by how much. If approved, reasons should be empty "
            "and max_approved amount should be the requested amount capped "
            "at what the applicant's disposable income can reasonably "
            "support over 24 months; if decline, max_approved_amount is 0"

        ),
        user_prompt= (
            f"applicant_id: {applicant_id}, credit_score: {credit_score}, "
            f"monthly_inclome: {monthly_income}, monthly_expenses: {monthly_expenses}, "
            f"debt_to_income: {debt_to_income}. requested_amount: {requested_amount}"
        ),
        response_model=_DecisionResult
    )

    check_policy_decision(result.decision, result.reasons, result.max_approved_amount, requested_amount)

    return {
        "applicant_id": applicant_id,
        "decision": result.decision,
        "reasons": result.reasons,
        "debt_to_income": debt_to_income,
        "requested_amount": requested_amount,
        "max_approved_amount": result.max_approved_amount,
        "policy_version": POLICY_VERSION,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }

@app.tool()
@metrics.track(server=SERVER_NAME, tool="get_policy_rules")
def policy_rules():
    """Return the current policy thresholds used as guidance by evaluate_policy."""

    return {
        "poilicy_version": POLICY_VERSION,
        "rules": [
            {"rule": "mon_credit_score", "threshold": MIN_CREDIT_SCORE},
            {"rule": "max_debt_to_income", "threshold": MAX_DEBT_TO_INCOME},
            {"rule": "min_monthly_income", "threshold": MIN_MONTHLY_INCOME},
        ]
    }

def main() -> None:
    run_server(app, SERVER_NAME, settings.policy_rules_engine_metrics_port)

if __name__ == "__main__":
    main()