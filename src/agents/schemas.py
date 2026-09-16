from __future__ import annotations

from pydantic import BaseModel, Field

class ApplicationDecision(BaseModel):
    """The orchestrator's final structured output (deepagents response_format)."""

    applicant_id: str
    decision: str = Field(..., description="'approved' or 'declined'")
    reasons: list[str] = Field(default_factory=list, description="Empty if approved")
    credit_score: int
    debt_to_income: float
    requested_amount: float
    max_approved_amount: float
    policy_version: str