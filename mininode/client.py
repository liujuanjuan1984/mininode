""" MiniNode module"""

import logging
from urllib import parse

from mininode import utils
from mininode._requests import HttpRequest
from mininode.api import QuorumLightNodeAPI

logger = logging.getLogger(__name__)


class MiniNode:
    """python for quorum lightnode, without datastore, one MiniNode client for one group"""

    def __init__(self, seedurl: str, is_session: bool = True, is_connection: bool = True):
        info = utils.decode_seed_url(seedurl)
        url = parse.urlparse(info["url"])
        if not info["url"]:
            raise ValueError("Invalid seed url.")
        jwt = parse.parse_qs(url.query)
        if jwt:
            jwt = jwt["jwt"][0]
        else:
            jwt = None

        group_id = info["group_id"]
        aes_key = bytes.fromhex(info["chiperkey"])
        _params = dict(
            api_base=f"{url.scheme}://{url.netloc}/api/v1",
            jwt_token=jwt,
            is_connection=is_connection,
            is_session=is_session,
        )
        self.http = HttpRequest(**_params)
        self.api = QuorumLightNodeAPI(self.http, group_id, aes_key)
