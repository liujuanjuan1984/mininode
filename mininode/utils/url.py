import json
import logging
from typing import Optional
from urllib import parse

logger = logging.getLogger(__name__)


def get_url(base: Optional[str] = None, endpoint: Optional[str] = None, is_quote: bool = False, **query_params) -> str:
    # url = parse.urljoin(base, endpoint) if base else endpoint
    url = ""
    if base:
        url = base
    if endpoint:
        url += endpoint

    if query_params:
        for k, v in query_params.items():
            if isinstance(v, bool):
                query_params[k] = json.dumps(v)
        query_ = parse.urlencode(query_params)
        if is_quote:
            query_ = parse.quote(query_, safe="?&/")
        return "?".join([url, query_])
    return url
