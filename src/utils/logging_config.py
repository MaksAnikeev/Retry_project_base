import json
import logging
import sys
from datetime import datetime


class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"

    DEBUG = "\033[36m"  # Cyan
    INFO = "\033[32m"  # Green
    WARNING = "\033[33m"  # Yellow
    ERROR = "\033[31m"  # Red
    CRITICAL = "\033[1;31m"  # Bold Red
    TIMESTAMP = "\033[90m"  # Dark Gray
    LOGGER = "\033[35m"  # Magenta
    EXTRA_KEY = "\033[34m"  # Blue
    EXTRA_VALUE = "\033[0m"  # Reset


class PrettyFormatter(logging.Formatter):
    LEVEL_COLORS = {
        logging.DEBUG: Colors.DEBUG,
        logging.INFO: Colors.INFO,
        logging.WARNING: Colors.WARNING,
        logging.ERROR: Colors.ERROR,
        logging.CRITICAL: Colors.CRITICAL,
    }

    def __init__(self, use_colors: bool = True):
        super().__init__()
        self.use_colors = use_colors

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        level = f"{record.levelname}:"
        level_color = self.LEVEL_COLORS.get(record.levelno, "")

        logger_name = record.name

        message = record.getMessage()

        extras = self._format_extras(record)

        if self.use_colors:
            parts = [
                f"{level_color}{level:<8}{Colors.RESET}",
                f"{Colors.LOGGER}{logger_name}{Colors.RESET}",
                "|",
                message,
                "|",
                f"{Colors.TIMESTAMP}{timestamp}{Colors.RESET}"
            ]
            if extras:
                parts.append(f"| {extras}")
        else:
            parts = [
                timestamp,
                "|",
                f"{level:<8}",
                "|",
                logger_name,
                "|",
                message,
            ]
            if extras:
                parts.append(f"| {extras}")

        result = " ".join(parts)

        if record.exc_info:
            result += "\n" + self.formatException(record.exc_info)

        return result

    def _format_extras(self, record: logging.LogRecord) -> str:
        """Форматирует extra-поля"""
        standard_fields = {
            'name', 'msg', 'args', 'created', 'filename', 'funcName',
            'levelname', 'levelno', 'lineno', 'module', 'msecs',
            'message', 'pathname', 'process', 'processName', 'relativeCreated',
            'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info', 'taskName'
        }

        extras = []
        for key, value in record.__dict__.items():
            if key not in standard_fields and value is not None:
                value_str = str(value)
                if len(value_str) > 100:
                    value_str = value_str[:97] + "..."

                if self.use_colors:
                    extras.append(f"{Colors.EXTRA_KEY}{key}{Colors.RESET}={Colors.EXTRA_VALUE}{value_str}")
                else:
                    extras.append(f"{key}={value_str}")

        return " | ".join(extras)


class JsonFormatter(logging.Formatter):
   def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "timestamp": datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S"),
        }

        standard_fields = {
            'name', 'msg', 'args', 'created', 'filename', 'funcName',
            'levelname', 'levelno', 'lineno', 'module', 'msecs',
            'message', 'pathname', 'process', 'processName', 'relativeCreated',
            'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info', 'taskName'
        }

        for key, value in record.__dict__.items():
            if key not in standard_fields and value is not None:
                log_data[key] = value

        if record.exc_info:
            log_data['exc_info'] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False, default=str)


def setup_logging(level: str = "INFO") -> None:
    formatter = PrettyFormatter()

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
