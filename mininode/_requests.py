"""module HttpRequest """
import logging
import os
from typing import Dict, Optional

import requests

from mininode import utils

logger = logging.getLogger(__name__)


class HttpRequest:
    """http requests"""

    def __init__(
        self,
        api_base: str = None,
        jwt_token: str = None,
        is_session: bool = True,
        is_connection: bool = False,
    ):

        requests.adapters.DEFAULT_RETRIES = 5
        self.api_base = api_base or "http://127.0.0.1"
        if is_session:
            self._session = requests.Session()
        else:
            self._session = requests

        self._session.keep_alive = self.is_connection = is_connection

        self.headers = {
            "USER-AGENT": "quorum.mininode.python",
            "Content-Type": "application/json",
        }
        if jwt_token:
            self.headers.update({"Authorization": f"Bearer {jwt_token}"})
        if not is_connection:
            self.headers.update({"Connection": "close"})

        _no_proxy = os.getenv("NO_PROXY", "")
        if "127.0.0.1" in self.api_base and self.api_base not in _no_proxy:
            os.environ["NO_PROXY"] = ",".join([_no_proxy, self.api_base])

    def _request(
        self,
        method: str,
        endpoint: str,
        payload: Optional[Dict] = None,
        api_base=None,
        url=None,
    ):
        payload = payload or {}
        if not url:
            api_base = api_base or self.api_base
            if not api_base:
                raise ValueError(f"api_base is null, {api_base}")
            url = utils.get_url(api_base, endpoint)

        try:
            resp = self._session.request(method=method, url=url, json=payload, headers=self.headers)
        except Exception as err:  # SSLCertVerificationError
            logger.warning(f"Exception {err}")
            _params = dict(method=method, url=url, json=payload, verify=False, headers=self.headers)
            resp = self._session.request(**_params)

        try:
            resp_json = resp.json()
        except Exception as err:
            logger.warning(f"Exception {err}")
            resp_json = {}

        logger.debug(f"payload:{payload}")
        logger.debug(f"url:{url}")
        logger.debug(f"resp_json:{resp_json}")
        logger.debug(f"resp.status_code:{resp.status_code}")

        return resp_json

    def get(self, endpoint: str, payload: Optional[Dict] = None):
        return self._request("get", endpoint, payload)

    def post(self, endpoint: str, payload: Optional[Dict] = None):
        return self._request("post", endpoint, payload)
