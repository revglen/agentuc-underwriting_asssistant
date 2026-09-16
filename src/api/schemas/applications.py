from __future__ import annotations

from pydantic import BaseModel, Field

class ApplicationEvaluationRequest(BaseModel):
    applicant_id: str = Field(..., min_length=1)
    requested_amount: float = Field(..., gt=0)
    months_of_statements: int = Field(default=3, ge=1, le=24)

class ApplicationEvaluationResponse(BaseModel):
    applicant_id: str
    decision: str
    reasons: list[str]
    credit_score: int
    debt_to_income: float
    requested_amount: float
    max_approved_amount: float
    policy_version: str
    evaluated_at: str