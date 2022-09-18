"""mininode"""
import datetime
import logging

from mininode.client import MiniNode
from mininode.crypto.account import create_private_key
from mininode.utils import decode_seed_url, timestamp_to_datetime

__all__ = ["MiniNode", "create_private_key", "decode_seed_url", "timestamp_to_datetime"]
__version__ = "0.2.4"
__author__ = "liujuanjuan1984"

# Set default logging handler to avoid "No handler found" warnings.
logging.getLogger(__name__).addHandler(logging.NullHandler())
logging.basicConfig(
    format="%(name)s %(asctime)s %(levelname)s %(message)s",
    filename=f"mininode_python_{datetime.date.today()}.log",
    level=logging.INFO,
)
