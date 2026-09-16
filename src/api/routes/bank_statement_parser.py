from __future__ import annotations

from fastapi import APIRouter, Query
from api.schemas.bank_statement_parser import (
        ParseStatementResponse, 
        TransactionSummaryResponse
    )
from api.schemas.common import ErrorResponse
from config.settings import settings
from mcp_servers.client import call_tool, server_url

router = APIRouter(prefix="/bank-statements", tags=["bank_statement_parser"])
_URL = server_url(settings.bank_statement_parser_mcp_host, 
                  settings.bank_statement_parser_mcp_port
                )

@router.get(
    "/{applicant_id}/parse",
    response_model=ParseStatementResponse,
    responses={422: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
)
async def parse_bank_statement(
    applicant_id: str, months: int = Query(default=3, ge=1, le=24)
) -> ParseStatementResponse:
    """Parse the applicant's last N months of bank statements into a summary."""
    result = await call_tool(
                            _URL, 
                            "parse_bank_statement", 
                            {
                                "applicant_id": applicant_id, 
                                "months": months
                            }
                        )
    
    return ParseStatementResponse(**result)

@router.get(
    "/{applicant_id}/transactions",
    response_model=TransactionSummaryResponse,
    responses={422: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
)
async def get_transaction_summary(applicant_id: str) -> TransactionSummaryResponse:
    """Fetch a category-level breakdown of the applicant's recent transactions."""
    result = await call_tool(
                            _URL, 
                            "get_transaction_summary", 
                            {
                                "applicant_id": applicant_id
                            }
                        )
    
    return TransactionSummaryResponse(**result)