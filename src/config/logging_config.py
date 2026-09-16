import logging
import logging.handlers
import sys

from config.settings import settings

class LoggingConfigurator:

    def __init__(self):
        self._configured = False

    def configure(self):
        if self._configured:
            return

        formatter = logging.Formatter(
            "%(asctime)s %(levelname)-8s %(name)s - %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )

        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setFormatter(formatter)

        settings.log_file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler=logging.handlers.RotatingFileHandler(
            settings.log_file_path, maxBytes=5 * 1024 * 1024, backupCount=3
        )

        file_handler.setFormatter(formatter)
        root=logging.getLogger()
        root.setLevel(settings.log_level)
        root.handlers.clear()
        root.addHandler(stderr_handler)
        root.addHandler(file_handler)
        self._configured=True

logging_configurator = LoggingConfigurator()
logging_configurator.configure()

if __name__ == "__main__":
    logger = logging.getLogger(__name__)
    logger.info("app started")