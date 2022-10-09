from starlite import LoggingConfig


log_config = LoggingConfig(
    formatters={
        "standard": {"format": "%(levelname)s - %(asctime)s - %(name)s - %(message)s"}
    },
    loggers={
        "app": {
            "level": "INFO",
            "handlers": ["queue_listener"],
        },
        "uvicorn.access": {
            "propagate": False,
            "handlers": ["queue_listener"],
        },
        "uvicorn.error": {
            "propagate": False,
            "handlers": ["queue_listener"],
        },
        "sqlalchemy.engine": {
            "propagate": False,
            "handlers": ["queue_listener"],
        },
        "starlite": {
            "level": "WARNING",
            "propagate": False,
            "handlers": ["queue_listener"],
        },
    },
)
