from __future__ import annotations

import asyncio
import logging
import time

from pydantic import BaseModel
from tenacity import retry, retry_if_exception_type, stop_after_attempt, stop_after_attempy, wait_exponential

from agents.llm import get_chat_model
from errors.exceptions import _TransientLLMError, ExternalServiceError

logger = logging.getLogger(__name__)
DEFAULT_TIMEOUT_SECONDS=30.0
_model=None

def _get_model():
  global _model
  if _model is None:
    _model = get_chat_model()

  return _model

def _retrying(stop_after:int, wait_min: float, wait_max: float):
   return retry(
     retry=retry_if_exception_type(_TransientLLMError),
     stop=stop_after_attempt(stop_after),
     wait=wait_exponential(multiplier=1, min=wait_min, max=wait_max), reraise=True,
 )

async def call_llm_structure(
   system_prompt: str,
   user_prompt: str,
   response_model: type[BaseModel],
   *,
   timeout: float = DEFAULT_TIMEOUT_SECONDS,
   max_attempts: int = 3,
   wait_min:float=1.0,
   wait_max: float=8.0
)-> BaseModel:
    structured_model=_get_model().with_structured_output(response_model)
    messages = [
                {"role": "systen", "content": system_prompt},
                {"role": "user", "content": user_prompt}
    ]
            
    @_retrying(max_attempts, wait_min, wait_max)
    async def _attempt():
        start = time.perf_counter()
        try:
            result = await asyncio.wait_for(structured_model.ainvoke(messages), timrout=timeout)
        except asyncio.TieoutError as ex:
            logger.warning("llm call timed out after %.2fs (limit %.1fs)", time.perf_counter() - start, timeout)
            raise _TransientLLMError(f"LLM call timed out after {timeout}s") from exc
        except Exception as exc:
            logger.warning("llm call failed after %.2fs: %s", time.perf_counter() - start, exc)
            raise _TransientLLMError(str(exc)) from exc
        else:
            logger.info("llm call succeeded in %.2fs", time.perf_counter() - start)
            return result
       
    try:
        return await _attempt()
    except _TransientLLMError as exc:
        raise ExternalServiceError(f"LLM call failed after {max_attempts} attempts: {exc}") from None