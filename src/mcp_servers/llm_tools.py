from __future__ import annotations
from pydantic import BaseModel
from agents.llm import get_chat_model

_model=None

def _get_model():
    global _model
    if _model is None:
        _model = get_chat_model()

    return _model

async def generate_structured(
        system_prompt: str, 
        user_prompt: str, 
        response_model: type[BaseModel
    ]) -> BaseModel:

    structured_model = _get_model().with_structured_output(response_model)
    return await structured_model.ainvoke([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ])