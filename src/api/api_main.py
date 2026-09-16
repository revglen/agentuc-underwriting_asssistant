from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from agents.orchestrator import build_orchestrator
from api.routes import  (
     bank_statement_parser, 
     credit_bureau, 
     health, 
     policy_rules_engine,
     applications
)
from config.settings import settings
from errors.error_handlers import RequestIDMidleware, register_exception_handlers

logger=logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Building Orchestrator at startup")
    app.state.orchestrator=await build_orchestrator()
    yield

app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=(
        "Underwriting assistant API. /applications/evaluate is the real "
        "business flow, backed by the LangChain/deepagents orchestrator. "
        "/internal/applications, /credit-bureau, /bank-statements and "
        "/policy are direct per-system debug routes over the underlying "
        "MCP servers, not the production path."
    ),
    lifespan=lifespan,
)

app.add_middleware(RequestIDMidleware)
register_exception_handlers(app)

app.include_router(health.router)
app.include_router(applications.router)
#app.include_router(internal_applications.router)
app.include_router(credit_bureau.router)
app.include_router(bank_statement_parser.router)
app.include_router(policy_rules_engine.router)