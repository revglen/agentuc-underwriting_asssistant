from __future__ import annotations
from langchain_core.language_models.chat_models import BaseChatModel

from config.settings import settings
from errors.exceptions import ConfigurationError

def get_chat_model() -> BaseChatModel:
    provider = settings.provider.lower()

    if provider == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(model=settings.model_name, base_url=settings.ollama_base_url)
    elif provider=="groq":
        if not settings.groq_api_key:
            raise ConfigurationError("PROVIDER=groq but GROQ_API_KEY is not set")
    
        from langchain_groq import ChatGroq
        return ChatGroq(model=settings.model_name, api_key=settings.groq_api_key)
    elif provider=="google":
        if not settings.google_api_key:
            raise ConfigurationError("PROVIDER=google but GOOGLE_API_KEY is not set")

        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=settings.model_name, api_key=settings.google_api_key)

    raise ConfigurationError(
        f"Unsupported PROVIDER={settings.provider!r}. "
        "Supported: ollama, groq, google (openai is configured in settings but "
        "langchain-openai isn't a project dependency yet)."
    )
