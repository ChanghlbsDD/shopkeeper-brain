import logging
from logging.config import dictConfig


def configure_logging(level: str = "INFO") -> None:
    """配置统一控制台日志格式。"""

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                }
            },
            "root": {
                "handlers": ["console"],
                "level": level.upper(),
            },
        }
    )
    logging.getLogger(__name__).info("Logging configured at %s", level.upper())
