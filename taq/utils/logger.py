import json, logging, sys
from datetime import datetime, timezone
from taq.core.config import config


class StructFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {"timestamp": datetime.now(timezone.utc).isoformat(), "level": record.levelname, "logger": record.name, "message": record.getMessage()}
        if hasattr(record, "extra"): entry.update(record.extra)
        if record.exc_info and record.exc_info[0]: entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry)


class PlainFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        return f"{datetime.now(timezone.utc).isoformat()} [{record.levelname}] {record.name}: {record.getMessage()}"


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructFormatter() if config.logging.format == "json" else PlainFormatter())
    logger.setLevel(getattr(logging, config.logging.level.upper(), logging.INFO))
    logger.addHandler(handler)
    return logger
