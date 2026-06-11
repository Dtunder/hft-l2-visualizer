import logging
import json
import sys
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """
    Formatter that outputs JSON strings after parsing the LogRecord.

    This formatter is used to emit structured JSON logs, which include the timestamp,
    logging level, logger name, message, and optional exception information.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Formats a logging record as a JSON-encoded string.

        Args:
            record (logging.LogRecord): The log record containing all relevant logging information.

        Returns:
            str: A JSON-formatted string representing the log record.
        """
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_data["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logging(level: int = logging.INFO) -> None:
    """
    Sets up structured JSON logging to stderr for the root logger.

    This function configures the root logger to output JSON-formatted log
    messages to standard error stream (`sys.stderr`). This prevents the logs
    from interfering with any standard output (`sys.stdout`) data streams.

    Args:
        level (int): The logging level to set for the root logger. Defaults to `logging.INFO`.
                     Accepts integer constants defined in the `logging` module.

    Returns:
        None
    """
    logger = logging.getLogger()
    logger.setLevel(level)

    # Avoid adding duplicate handlers
    for handler in logger.handlers:
        if isinstance(handler, logging.StreamHandler) and isinstance(
            handler.formatter, JSONFormatter
        ):
            return

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
