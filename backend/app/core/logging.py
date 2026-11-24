import logging
import sys


def setup_logging(app_env: str = "development") -> None:
    level = logging.DEBUG if app_env == "development" else logging.INFO

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Keep noisy third-party loggers at WARNING and above
    for noisy in ["httpx", "httpcore", "pymongo"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)