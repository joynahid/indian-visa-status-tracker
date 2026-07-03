"""Application logger."""

import logging

logging.basicConfig(format="%(name)s :: %(levelname)-8s :: %(message)s")
logger = logging.getLogger("indianvisastatus")
logger.setLevel(logging.INFO)
