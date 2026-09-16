from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from api.schemas.applications import ApplicationEvaluationRequest, ApplicationEvaluationResponse
from api.schemas.common import ErrorResponse
from errors.exceptions import ExternalServiceError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/applications", tags=["applications"])

# @router.post(
#     "/evaluate",
#     response_model=ApplicationEvaluationResponse,
#     responses={422: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
# )
# async def evaluate_application(payload: ApplicationEvaluationRequest, 
#                                request: Request) -> ApplicationEvaluationResponse:
#     """
#     The production evaluation path: the LangChain/deepagents orchestrator,
#     built once at app startup (see main.py's lifespan) and reused here, not
#     rebuilt per request. A main agent delegates to three subagents
#     (credit_bureau, bank_statement_parser, policy_rules_engine), each scoped
#     to its own MCP server's tools, and returns a typed ApplicationDecision
#     (deepagents response_format).
#     """

#     graph = request.app.state.orchestrator
#     message= (
#         f"Evaluate applicant_id={payload.applicant_id}, "
#         f"requested_amount={payload.requested_amount}, "
#         f"using {payload.months_of_statements} months of bank statements."
#     )
#     try:
#         result= await graph.ainvoke({"messages": [HumanMessage(content=message)]})
#     except Exception as e:
#         raise ExternalServiceError(f"orchestrator run failed: {e}") from None

#     decision = result.get("structured_response")
#     if decision is None:
#         raise ExternalServiceError("orchestrator finished without a structured decision")

#     return ApplicationEvaluationResponse(
#         **decision.model_dump(),
#         evaluated_at=datetime.now(timezone.utc).isoformat(),
#     )

async def _run_evaluation(graph, payload: ApplicationEvaluationRequest) -> ApplicationEvaluationResponse:
   
    message = (
        f"Evaluate applicant_id={payload.applicant_id!r}, "
        f"requested_amount={payload.requested_amount}, "
        f"using {payload.months_of_statements} months of bank statements."
    )
    try:
        result = await graph.ainvoke({"messages": [HumanMessage(content=message)]})
    except Exception as exc:
        raise ExternalServiceError(f"orchestrator run failed: {exc}") from None

    decision = result.get("structured_response")
    if decision is None:
        logger.warning("orchestrator finished without structured_response, retrying with a nudge")
        nudge = HumanMessage(
            content=(
                "You did not call the required structured output tool. Using the "
                "figures you already gathered above, call it now with the final "
                "ApplicationDecision - do not write the answer as text."
            )
        )
        try:
            result = await graph.ainvoke({"messages": result["messages"] + [nudge]})
        except Exception as exc:
            raise ExternalServiceError(f"orchestrator retry failed: {exc}") from None
        decision = result.get("structured_response")

    if decision is None:
        raise ExternalServiceError("orchestrator finished without a structured decision after retry")

    return ApplicationEvaluationResponse(
        **decision.model_dump(),
        evaluated_at=datetime.now(timezone.utc).isoformat(),
    )

@router.post(
    "/evaluate",
    response_model=ApplicationEvaluationResponse,
    responses={422: {"model": ErrorResponse}, 502: {"model": ErrorResponse}},
)
async def evaluate_application(payload: ApplicationEvaluationRequest, request: Request) -> ApplicationEvaluationResponse:
    """
    Synchronous evaluation - blocks until the orchestrator finishes (can take
    minutes on a local model). For anything client-facing, prefer
    POST /evaluate/async below instead.
    """
    return await _run_evaluation(request.app.state.orchestrator, payload)

JobStatus = Literal["pending", "running", "completed", "failed"]

class JobSubmitResponse(BaseModel):
    job_id: str
    status: JobStatus

class JobStatusResponse(BaseModel):
    job_id: str
    status: JobStatus # type: ignore
    result: ApplicationEvaluationResponse | None = None
    error: str | None = None

_jobs: dict[str, JobStatusResponse] = {}

async def _run_job(job_id: str, graph, payload: ApplicationEvaluationRequest) -> None:
    _jobs[job_id].status = "running"
    try:
        result = await _run_evaluation(graph, payload)
        _jobs[job_id] = JobStatusResponse(job_id=job_id, status="completed", result=result)
    except Exception as exc:
        logger.exception("job %s failed", job_id)
        _jobs[job_id] = JobStatusResponse(job_id=job_id, status="failed", error=str(exc))

@router.post("/evaluate/async", response_model=JobSubmitResponse, status_code=202)
async def evaluate_application_async(
    payload: ApplicationEvaluationRequest, request: Request, background_tasks: BackgroundTasks
) -> JobSubmitResponse:
    """Submit an evaluation and return immediately with a job_id to poll."""
    job_id = str(uuid.uuid4())
    _jobs[job_id] = JobStatusResponse(job_id=job_id, status="pending")
    background_tasks.add_task(_run_job, job_id, request.app.state.orchestrator, payload)
    return JobSubmitResponse(job_id=job_id, status="pending")

@router.get("/evaluate/async/{job_id}", response_model=JobStatusResponse)
async def get_evaluation_job(job_id: str) -> JobStatusResponse:
    job = _jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"no job with id {job_id!r}")
    return job