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
        api_base: Optional[str] = None,
        jwt_token: Optional[str] = None,
        is_session: bool = True,
        keep_alive: bool = False,
        no_proxy: bool = True,
        user_agent: Optional[str] = None,
    ):
        """http request"""
        requests.adapters.DEFAULT_RETRIES = 5
        self.api_base = api_base or "http://127.0.0.1"
        if is_session:
            self._session = requests.Session()
        else:
            self._session = requests

        self._session.keep_alive = self.keep_alive = keep_alive

        self.headers = {
            "USER-AGENT": user_agent or "quorum.mininode.python",
            "Content-Type": "application/json",
        }
        if jwt_token:
            self.headers.update({"Authorization": f"Bearer {jwt_token}"})
        if not keep_alive:
            self.headers.update({"Connection": "close"})

        if no_proxy:
            _no_proxy = os.getenv("NO_PROXY", "")
            if self.api_base not in _no_proxy:
                os.environ["NO_PROXY"] = ",".join([_no_proxy, self.api_base])

    def _request(
        self,
        method: str,
        endpoint: str,
        payload: Optional[Dict] = None,
    ):
        """common request"""
        payload = payload or {}
        url = utils.join_url(self.api_base, endpoint)

        try:
            resp = self._session.request(method=method, url=url, json=payload, headers=self.headers)
        except Exception as err:  # SSLCertVerificationError
            logger.warning("request error %s", err)
            _params = dict(method=method, url=url, json=payload, verify=False, headers=self.headers)
            resp = self._session.request(**_params)

        try:
            resp_json = resp.json()
        except Exception as err:
            logger.warning("response error %s", err)
            resp_json = {}

        return resp_json

    def get(self, endpoint: str, payload: Optional[Dict] = None):
        """get method request"""
        return self._request("get", endpoint, payload)

    def post(self, endpoint: str, payload: Optional[Dict] = None):
        """post method request"""
        return self._request("post", endpoint, payload)
