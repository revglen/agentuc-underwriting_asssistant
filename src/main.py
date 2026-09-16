import uvicorn
import logging

from config.settings import settings
from api.api_main import app

logger=logging.getLogger(__name__)

if __name__ == "__main__":
   
    ssl_kwargs = {}
    if settings.tls_enabled:
        if settings.tls_cert_path.exists() and settings.tls_key_path.exists():
            ssl_kwargs = {
                "ssl_certfile": str(settings.tls_cert_path),
                "ssl_keyfile": str(settings.tls_key_path),            
            }
        else:
            logger.warning(
                "TLS_ENABLED is true but %s / %s not found; falling back to plain HTTP. "
                "Run scripts/generate_dev_certs.sh to create a local dev cert.",
                settings.tls_cert_path, settings.tls_key_path,
            )

    uvicorn.run("api.api_main:app", 
                host=settings.api_host, 
                port=settings.api_port, 
                reload=True,
                **ssl_kwargs)