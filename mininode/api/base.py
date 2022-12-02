"""base.py"""
import logging
from typing import Dict, Optional

from mininode._requests import HttpRequest

logger = logging.getLogger(__name__)


class BaseAPI:
    """BaseAPI"""

    def __init__(self, http: HttpRequest, group_id, aes_key, version: int = 1):
        self._http = http
        self.group_id = group_id
        self.aes_key = aes_key
        self.version = version

    def _get(self, endpoint: str, payload: Optional[Dict] = None):
        """api _get"""
        return self._http.get(endpoint, payload)

    def _post(self, endpoint: str, payload: Optional[Dict] = None):
        """api _post"""
        return self._http.post(endpoint, payload)
