import logging
import sys

from app.core.config import settings

LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def setup_logging() -> None:
    logging.basicConfig(
        level=settings.log_level,
        format=LOG_FORMAT,
        stream=sys.stdout,
        force=True,
    )

    logger = logging.getLogger(__name__)
    logger.info("Logging initialized at %s level.", settings.log_level)
