from __future__ import annotations

import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from errors.exceptions import AppError, McpToolError

logger=logging.getLogger(__name__)

class RequestIDMidleware(BaseHTTPMiddleware):
    """Attaches a request id to every request/response for correlation in logs and error bodies."""
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.reqiest_id = request_id
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

def _error_response(request: Request, 
                    status_code: int, 
                    error: str, 
                    message: str, 
                    details: dict
                ) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=status_code,
        content={
                    "error": error,
                    "message": message,
                    "details": details,
                    "request_id": request_id
                },
    )

def register_exception_handlers(app: FastAPI)-> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, ex: AppError) -> JSONResponse:
        logger.warning("%s: %s", type(ex).__name__, ex.message, extra={"details": ex.details})
        return _error_response(request, ex.status_code, type(ex).__name__, ex.message, ex.details)

    @app.exception_handler(McpToolError)
    async def handle_mcp_tool_error(request: Request, ex: McpToolError) -> JSONResponse:
        logger.error("MCP tool call failed: %s", ex)
        return _error_response(request, 502, "ExternalServiceError", str(ex), {})

    @app.exception_handler(Exception)
    async def handle_unexpected(request: Request, ex: Exception) -> JSONResponse:
       logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
       return _error_response(request, 500, "InternalServerError", "An unexpected error occurred.", {})