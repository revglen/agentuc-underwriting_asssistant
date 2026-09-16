from __future__ import annotations

from pydantic import BaseModel, Field

class CreditScoreRequest(BaseModel):
    applicant_id: str  = Field(..., min_length=1)

class CreditScoreREsponse(BaseModel):
    applicant_id: str
    score: int
    rating: str
    bureau: str
    pulled_at: str

class CreditReportResponse(BaseModel):
    applicant_id: str
    score: int
    rating: str
    open_accounts: int
    delinquencies_last_24_months: int
    credit_utilization_pct: float
    inquiries_last_6_months: int
    report_date: str