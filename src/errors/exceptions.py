class AppError(Exception):
    status_code: int = 500
    
    def __init__(self, message: str, details: dict | None= None):
        super().__init__(message)
        self.message=message
        self.details = details or {}

    def to_dict(self) -> dict:
        return {
                "error": type(self).__name__, 
                "message": self.message, 
                "details": self.details
            }

class NotFoundError(AppError):
    """A requested resource doesn't exist (e.g. unknown applicant_id)."""
    status_code = 404

class ValidationError(AppError):
    """Input failed validation."""
    status_code = 422

class DataSourceError(AppError):
    """A data file/source is unreadable or malformed."""
    status_code = 502

class ConfigurationError(AppError):
    """Required config is missing or invalid."""
    status_code = 500

class ExternalServiceError(AppError):
    """A call to an external service failed."""
    status_code = 502

class McpToolError(Exception):
    """Raised when a tool call returns an MCP-level error (isError=True)."""

class _TransientLLMError(Exception):
    """A failure worth retrying: connection refused, timeout, rate limit, etc."""