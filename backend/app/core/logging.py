"""Structured JSON logging to stdout, with request_id bound onto every log
line for the lifetime of a request. docs/architecture/backend.md §6.
"""

import logging
import sys
from contextvars import ContextVar

import structlog

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


def _add_request_id(
    logger: structlog.typing.WrappedLogger, method_name: str, event_dict: structlog.typing.EventDict
) -> structlog.typing.EventDict:
    event_dict["request_id"] = request_id_var.get()
    return event_dict


def configure_logging(log_level: str = "INFO") -> None:
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            _add_request_id,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.typing.FilteringBoundLogger:
    return structlog.get_logger(name)
