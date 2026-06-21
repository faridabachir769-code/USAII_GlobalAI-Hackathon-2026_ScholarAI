"""
LOGGER MODULE
=============

Provides centralized logging for the application.

WHY LOGGING?
- Print statements disappear in production
- Logging provides levels (DEBUG, INFO, WARNING, ERROR)
- Can write to files, databases, or monitoring services
- Essential for debugging production issues
"""

import logging
from typing import Optional

# Create a logger for the app
logger = logging.getLogger("scholarai")

# Configure logging format
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance

    Usage:
        log = get_logger(__name__)
        log.info("Something happened")
        log.error("An error occurred")
    """
    return logging.getLogger(name or "scholarai")
