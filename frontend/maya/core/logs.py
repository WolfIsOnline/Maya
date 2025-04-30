import logging
from colorlog import ColoredFormatter

LOG_LEVEL = logging.DEBUG


def setup_logging():
    """Setups custom logging formatting

    Returns:
        logger: logger object
    """
    logger = logging.getLogger("maya.discord")
    logger.setLevel(LOG_LEVEL)

    handler = logging.StreamHandler()
    formatter = ColoredFormatter(
        "%(log_color)s%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold_red",
        },
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    for name in ["maya.discord"]:  #
        discord_logger = logging.getLogger(name)
        discord_logger.setLevel(LOG_LEVEL)
        discord_logger.handlers = [handler]

    return logger


log = setup_logging()
