from __future__ import annotations

from fastapi import APIRouter

from api.schemas.common import ErrorResponse
from api.schemas.policy_rules_engine import (
    PolicyEvaluationRequest,
    PolicyEvaluationResponse,
    PolicyRulesResponse,
)
from config.settings import settings
from mcp_servers.client import call_tool, server_url

router = APIRouter(prefix="/policy", tags=["policy_rules_engine"])
_URL = server_url(settings.policy_rules_engine_mcp_host, 
                  settings.policy_rules_engine_mcp_port
                )

@router.post(
    "/evaluate",
    response_model=PolicyEvaluationResponse,
    responses={422: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
)
async def evaluate_policy(payload: PolicyEvaluationRequest) -> PolicyEvaluationResponse:
    """Evaluate an applicant's figures against the current policy rules."""
    result = await call_tool(_URL, 
                             "evaluate_policy", 
                             payload.model_dump())
    return PolicyEvaluationResponse(**result)

@router.get(
    "/rules",
    response_model=PolicyRulesResponse,
    responses={502: {"model": ErrorResponse}},
)
async def get_policy_rules() -> PolicyRulesResponse:
    """Fetch the current policy thresholds."""
    result = await call_tool(_URL, 
                             "get_policy_rules", 
                             {}
                            )
    return PolicyRulesResponse(**result)