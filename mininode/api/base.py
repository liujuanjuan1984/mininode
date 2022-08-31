from typing import Dict

from mininode._requests import HttpRequest


class BaseAPI:
    def __init__(self, http: HttpRequest, group_id, aes_key):
        self._http = http
        self.group_id = group_id
        self.aes_key = aes_key

    def _get(self, endpoint: str, payload: Dict = {}):
        return self._http.get(endpoint, payload)

    def _post(self, endpoint: str, payload: Dict = {}):
        return self._http.post(endpoint, payload)
