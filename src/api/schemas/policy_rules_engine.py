from __future__ import annotations

from pydantic import BaseModel, Field

class PolicyEvaluationRequest(BaseModel):
    applicant_id: str = Field(..., min_length=1)
    credit_score: int = Field(..., ge=300, le=850)
    monthly_income: float = Field(..., gt=0)
    monthly_expenses: float = Field(..., ge=0)
    requested_amount: float = Field(..., gt=0)

class PolicyEvaluationResponse(BaseModel):
    applicant_id: str
    decision: str
    reasons: list[str]
    debt_to_income: float
    requested_amount: float
    max_approved_amount: float
    polict_version: str
    evalauated_at: str

class PolicyRule(BaseModel):
    rule: str
    threshold: float

class PolicyRulesResponse(BaseModel):
    policy_version: str
    rules: list[PolicyRule]