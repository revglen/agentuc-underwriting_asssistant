from __future__ import annotations

import os
from dotenv import load_dotenv
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    log_level: str = "INFO"
    log_file_path: Path = Path("logs/app.log")
    tracing_enabled: bool = True

    langchain_project: str = os.getenv("LANGCHAIN_PROJECT", "")
    langchain_endpoint: str = os.getenv("LANGCHAIN_ENDPOINT", "")

    google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    langchain_api_key: str = os.getenv("LANGCHAIN_API_KEY", "")

    tavily_api_key: str = os.getenv("TAVILY_API_KEY", "")
    hf_token: str = os.getenv("HF_TOKEN", "")

    provider: str = os.getenv("PROVIDER", "ollama")
    model_name: str = os.getenv("MODEL_NAME", "qwen2.5:7b")
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    credit_bureau_metrics_port: int = int(os.getenv("CREDIT_BUREAU_METRICS_PORT", "8001"))
    bank_statement_parser_metrics_port: int = int(os.getenv("BANK_STATEMENT_PARSER_METRICS_PORT", "8002"))
    policy_rules_engine_metrics_port: int = int(os.getenv("POLICY_RULES_ENGINE_METRICS_PORT", "8003"))

    # mcp_scheme: str = os.getenv("MCP_SCHEME", "http")  # servers are reached over the compose network, plain http
    # credit_bureau_mcp_host: str = os.getenv("CREDIT_BUREAU_MCP_HOST", "127.0.0.1")
    # bank_statement_parser_mcp_host: str = os.getenv("BANK_STATEMENT_PARSER_MCP_HOST", "127.0.0.1")
    # policy_rules_engine_mcp_host: str = os.getenv("POLICY_RULES_ENGINE_MCP_HOST", "127.0.0.1")

    mcp_host: str = os.getenv("MCP_HOST", "0.0.0.0")
    credit_bureau_mcp_port: int = int(os.getenv("CREDIT_BUREAU_MCP_PORT", "9001"))
    bank_statement_parser_mcp_port: int = int(os.getenv("BANK_STATEMENT_PARSER_MCP_PORT", "9002"))
    policy_rules_engine_mcp_port: int = int(os.getenv("POLICY_RULES_ENGINE_MCP_PORT", "9003"))

    mcp_scheme: str = os.getenv("MCP_SCHEME", "http")  # servers are reached over the compose network, plain http
    credit_bureau_mcp_host: str = os.getenv("CREDIT_BUREAU_MCP_HOST", "127.0.0.1")
    bank_statement_parser_mcp_host: str = os.getenv("BANK_STATEMENT_PARSER_MCP_HOST", "127.0.0.1")
    policy_rules_engine_mcp_host: str = os.getenv("POLICY_RULES_ENGINE_MCP_HOST", "127.0.0.1")

    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8443"))
    api_title: str = "Underwriting Assistant API"
    api_version: str = "0.1.0"

    tls_enabled: bool = os.getenv("TLS_ENABLED", "true").lower() == "true"
    tls_cert_path: Path = Path(os.getenv("TLS_CERT_PATH", "certs/dev-cert.pem"))
    tls_key_path: Path = Path(os.getenv("TLS_KEY_PATH", "certs/dev-key.pem"))

settings = Settings()

if __name__ == "__main__":
    print(settings.provider)