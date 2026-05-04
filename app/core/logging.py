import logging
import sys


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("audit.log", mode="a", encoding="utf-8")
        ]
    )


def get_logger(name: str):
    return logging.getLogger(name)