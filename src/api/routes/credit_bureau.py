from __future__ import annotations

from fastapi import APIRouter, Query

from api.schemas.common import ErrorResponse
from api.schemas.credit_bureau import CreditReportResponse, CreditScoreREsponse
from config.settings import settings
from mcp_servers.client import call_tool, server_url

router = APIRouter(prefix="/credit_bureau", tags=["credit_bureau"])

_URL = server_url(settings.credit_bureau_mcp_host, settings.credit_bureau_mcp_port)

@router.get(
   "/{applicant_id}/score",
   response_model=CreditScoreREsponse,
   responses={422: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
) 
async def get_credit_score(
   applicant_id: str
) -> CreditScoreREsponse:
    """Fetch the applicant's current credit score and rating band."""

    result = await call_tool(_URL, "get_credit_score", {"applicant_id": applicant_id})
    return CreditScoreREsponse(**result)

@router.get(
    "/{applicant_id}/transactions",
    response_model=CreditReportResponse,
    responses={422: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
)
async def get_credit_report(applicant_id: str) -> CreditReportResponse:
    """Fetch the applicant's fuller mock credit report."""
    result = await call_tool(_URL, "get_credit_report", {"applicant_id": applicant_id})
    return CreditReportResponse(**result)
   