import datetime
import logging

from mininode.client import MiniNode

__version__ = "0.1.5"
__author__ = "liujuanjuan1984"

# Set default logging handler to avoid "No handler found" warnings.
logging.getLogger(__name__).addHandler(logging.NullHandler())
logging.basicConfig(
    format="%(name)s %(asctime)s %(levelname)s %(message)s",
    filename=f"mininode_python_{datetime.date.today()}.log",
    level=logging.INFO,
)
