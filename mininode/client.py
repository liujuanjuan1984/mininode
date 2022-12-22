""" MiniNode module"""

import logging
from urllib import parse

from mininode import utils
from mininode._requests import HttpRequest
from mininode.api import QuorumLightNodeAPI

logger = logging.getLogger(__name__)


class MiniNode:
    """python for quorum lightnode, without datastore, one MiniNode client for one group"""

    def __init__(
        self,
        seedurl: str,
        is_session: bool = True,
        keep_alive: bool = True,
        version: int = 1,
    ):
        """init mininode client

        Args:
            seedurl (str): the seed url of rum group which shared by rum fullnode, with host:post?jwt=xxx to connect
            is_session (bool, optional): http request use session or not. Defaults to True.
            keep_alive (bool, optional): http request keep alive or not. Defaults to True.

        Raises:
            ValueError: invalid seedurl, must start with rum://seed?, shared by rum fullnode.
        """
        info = utils.decode_seed_url(seedurl)
        url = parse.urlparse(info["url"])
        if not info["url"]:
            raise ValueError("Invalid seedurl.")
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
            keep_alive=keep_alive,
            is_session=is_session,
        )
        self.http = HttpRequest(**_params)
        self.api = QuorumLightNodeAPI(self.http, group_id, aes_key, version=version)
