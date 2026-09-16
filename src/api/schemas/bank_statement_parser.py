from __future__ import annotations

from pydantic import BaseModel, Field

class ParseStatementRequest(BaseModel):
    applicant_id: str = Field(..., min_length=1)
    months: int = Field(default=3, ge=1, le=24)

class ParseStatementResponse(BaseModel):
    applicant_id: str
    months_covered: int
    statement_count: int
    avg_monthly_income: float
    avg_monthly_expenses: float
    avg_closing_balances: float
    overdraft_count: int
    parsed_at: str

class TransactionSummaryRequest(BaseModel):
    applicant_id : str = Field(..., min_length=1)

class TransactionSummaryResponse(BaseModel):
    applicant_id: str
    category_breakdown: dict[str, float]
    total_inflow: float
    total_outflow: float
    summarised_at: str