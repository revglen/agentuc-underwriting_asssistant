from __future__ import annotations
from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health")
async def health() -> dict:
  """Basic liveness check. Does not verify the MCP servers are reachable."""
  return {"statis": "ok"}