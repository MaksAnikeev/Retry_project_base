import json
import logging
import sys
from datetime import datetime

from src.database.db import settings


class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DEBUG = "\033[36m"       # Cyan
    INFO = "\033[32m"        # Green
    WARNING = "\033[33m"     # Yellow
    ERROR = "\033[31m"       # Red
    CRITICAL = "\033[1;31m"  # Bold Red
    TIMESTAMP = "\033[90m"   # Dark Gray
    LOGGER = "\033[35m"      # Magenta
    EXTRA_KEY = "\033[34m"   # Blue
    EXTRA_VALUE = "\033[0m"  # Reset

    LEVEL_COLORS = {
        logging.DEBUG: DEBUG,
        logging.INFO: INFO,
        logging.WARNING: WARNING,
        logging.ERROR: ERROR,
        logging.CRITICAL: CRITICAL,
    }


class BaseLogFormatter(logging.Formatter):

    STANDARD_FIELDS = {
        'name', 'msg', 'args', 'created', 'filename', 'funcName',
        'levelname', 'levelno', 'lineno', 'module', 'msecs',
        'message', 'pathname', 'process', 'processName', 'relativeCreated',
        'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info', 'taskName',
        'asctime',
    }

    def get_extras_dict(self, record: logging.LogRecord) -> dict:
        return {
            key: value
            for key, value in record.__dict__.items()
            if key not in self.STANDARD_FIELDS and not key.startswith("_") and value is not None
        }

    def _format_value_for_text(self, value: object, max_len: int = 200) -> str:
        val_str = (
            json.dumps(value, ensure_ascii=False, default=str)
            if isinstance(value, (dict, list))
            else str(value)
        )
        return val_str if len(val_str) <= max_len else val_str[:max_len - 3] + "..."


class PrettyFormatter(BaseLogFormatter):

    def __init__(self):
        super().__init__()

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        level = f"{record.levelname}:"
        level_color = Colors.LEVEL_COLORS.get(record.levelno, "")

        parts = [
            f"{level_color}{level:<8}{Colors.RESET}",
            f"{Colors.LOGGER}{record.name}{Colors.RESET}",
            "|",
            record.getMessage(),
            "|",
            f"{Colors.TIMESTAMP}{timestamp}{Colors.RESET}"
        ]

        extras = self.get_extras_dict(record)
        if extras:
            extras_str = " | ".join(
                f"{Colors.EXTRA_KEY}{key}{Colors.RESET}={Colors.EXTRA_VALUE}{self._format_value_for_text(value, max_len=100)}"
                for key, value in extras.items()
            )
            parts.append(f"| {extras_str}")

        result = " ".join(parts)
        if record.exc_info:
            result += "\n" + self.formatException(record.exc_info)
        return result


class JsonFormatter(BaseLogFormatter):
   def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "timestamp": datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S"),
        }
        log_data.update(self.get_extras_dict(record))

        if record.exc_info:
            log_data['exc_info'] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False, default=str)


def setup_logging(level: str = "INFO") -> None:
    if settings.LOG_FORMAT_TYPE == "pretty":
        formatter = PrettyFormatter()
    elif settings.LOG_FORMAT_TYPE ==  "json":
        formatter = JsonFormatter()
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.setLevel(level)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.INFO)



