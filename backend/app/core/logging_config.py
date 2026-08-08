"""
إعداد الـ logging المركزي: JSON + Text + Console مع RotatingFileHandler.
"""
import logging
import logging.handlers
import json
from datetime import datetime
import os

LOGS_DIR = "logs"

class JSONFormatter(logging.Formatter):
    """Formatter يخرج JSON."""

    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)

def setup_logging(level: int = logging.INFO):
    """إعداد الـ logging. آمنة للاستدعاء أكثر من مرة."""

    os.makedirs(LOGS_DIR, exist_ok=True)

    root_logger = logging.getLogger()
    if root_logger.handlers:
        return root_logger

    root_logger.setLevel(level)

    # File handler - JSON
    file_handler = logging.handlers.RotatingFileHandler(
        os.path.join(LOGS_DIR, "app.json.log"),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(file_handler)

    # File handler - Text
    text_handler = logging.handlers.RotatingFileHandler(
        os.path.join(LOGS_DIR, "app.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    text_handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ))
    root_logger.addHandler(text_handler)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    ))
    root_logger.addHandler(console_handler)

    return root_logger
