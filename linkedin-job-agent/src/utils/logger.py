"""Logging configuration for LinkedIn Job Agent."""

import logging
from pathlib import Path

import structlog
from rich.logging import RichHandler


def setup_logging(debug: bool = False) -> None:
    """Set up structured logging."""
    # Create logs directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Set log level
    log_level = logging.DEBUG if debug else logging.INFO

    # Configure standard logging for libraries
    logging.basicConfig(
        level=log_level,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(rich_tracebacks=True, tracebacks_show_locals=debug),
            logging.FileHandler(log_dir / "app.log"),
        ],
    )

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.dict_tracebacks,
            structlog.dev.ConsoleRenderer() if debug else structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


class RequestLogger:
    """Log HTTP requests and responses."""

    def __init__(self, logger: structlog.BoundLogger):
        """Initialize request logger."""
        self.logger = logger

    def log_request(self, method: str, url: str, **kwargs) -> None:
        """Log an outgoing request."""
        self.logger.info(
            "request_sent",
            method=method,
            url=url,
            **kwargs
        )

    def log_response(self, status: int, url: str, duration: float, **kwargs) -> None:
        """Log a response."""
        log_method = self.logger.info if status < 400 else self.logger.warning
        log_method(
            "response_received",
            status=status,
            url=url,
            duration_ms=duration * 1000,
            **kwargs
        )

    def log_error(self, url: str, error: Exception, **kwargs) -> None:
        """Log a request error."""
        self.logger.error(
            "request_failed",
            url=url,
            error=str(error),
            error_type=type(error).__name__,
            **kwargs
        )
