import logging


def get_logger(name: str) -> logging.Logger:
    """Return a logger with the given name, configuring the root logger once."""
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger(name)
