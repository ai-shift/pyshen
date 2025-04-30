import atexit
import json
import logging
import logging.config
import logging.handlers
from datetime import UTC, datetime
from typing import Any, override

_LOG_RECORD_BUILTIN_ATTRS = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
    "taskName",
}


class LogsJSONFormatter(logging.Formatter):
    def __init__(
        self,
        *,
        fmt_keys: dict[str, str] | None = None,
    ):
        super().__init__()
        self.fmt_keys = fmt_keys if fmt_keys is not None else {}

    @override
    def format(self, record: logging.LogRecord) -> str:
        message = self._prepare_log_dict(record)
        return json.dumps(message, default=str)

    def _prepare_log_dict(self, record: logging.LogRecord) -> dict[str, Any]:
        always_fields = {
            "message": record.getMessage(),
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
        }
        if record.exc_info is not None:
            always_fields["exc_info"] = self.formatException(record.exc_info)

        if record.stack_info is not None:
            always_fields["stack_info"] = self.formatStack(record.stack_info)

        message = {
            key: msg_val
            if (msg_val := always_fields.pop(val, None)) is not None
            else getattr(record, val)
            for key, val in self.fmt_keys.items()
        }
        message.update(always_fields)

        for key, val in record.__dict__.items():
            if key not in _LOG_RECORD_BUILTIN_ATTRS:
                message[key] = val  # noqa: PERF403

        return message


_LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": LogsJSONFormatter,
            "fmt_keys": {
                "level": "levelname",
                "message": "message",
                "timestamp": "timestamp",
                "logger": "name",
                "module": "module",
                "function": "funcName",
                "line": "lineno",
                "thread_name": "threadName",
            },
        }
    },
    "handlers": {
        "stderr": {
            "class": logging.StreamHandler,
            "level": logging.INFO,
            "formatter": "json",
            "stream": "ext://sys.stderr",
        },
        "queue_handler": {
            "class": logging.handlers.QueueHandler,
            "handlers": ["stderr"],
            "respect_handler_level": True,
        },
    },
    "loggers": {"root": {"level": logging.DEBUG, "handlers": ["queue_handler"]}},
}


class NonErrorFilter(logging.Filter):
    @override
    def filter(self, record: logging.LogRecord) -> bool | logging.LogRecord:
        return record.levelno <= logging.INFO


def setup() -> None:
    logging.config.dictConfig(_LOG_CONFIG)
    queue_handler = logging.getHandlerByName("queue_handler")
    if queue_handler is None:
        return
    assert isinstance(queue_handler, logging.handlers.QueueHandler)
    assert queue_handler.listener is not None
    queue_handler.listener.start()
    atexit.register(queue_handler.listener.stop)
