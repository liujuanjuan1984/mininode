import base64
import logging
import uuid
from typing import Dict
from urllib import parse

logger = logging.getLogger(__name__)


def _decode_b64_urlsafe(b64str: str) -> bytes:
    # 对 base64 字符串检查长度，并补位，转换为字节
    l = len(b64str)
    m = (4 - l % 4) % 4
    b64byte = b64str.encode() + b"=" * m
    b64byte = base64.urlsafe_b64decode(b64byte)
    return b64byte


def _decode_uuid(b64str: str) -> str:
    b64byte = _decode_b64_urlsafe(b64str)
    b64uuid = uuid.UUID(bytes=b64byte)
    return str(b64uuid)


def _decode_timestamp(b64str: str) -> int:
    b64byte = _decode_b64_urlsafe(b64str)
    bigint = int.from_bytes(b64byte, "big")
    return bigint


def _decode_cipher_key(b64str: str):
    b64byte = _decode_b64_urlsafe(b64str)
    return b64byte.hex()


def _decode_pubkey(b64str: str) -> str:
    b64byte = _decode_b64_urlsafe(b64str)
    pubkey = base64.standard_b64encode(b64byte).decode()
    return pubkey


def decode_seed_url(seed_url: str) -> Dict:

    if not seed_url.startswith("rum://seed?"):
        raise ValueError("invalid Seed URL")

    # 由于 Python 的实现中，每个 key 的 value 都是 列表，所以做了下述处理
    # TODO: 如果 u 参数的值有多个，该方法需升级
    query_dict = {}
    _q = parse.urlparse(seed_url).query
    for k, v in parse.parse_qs(_q).items():
        if len(v) == 1:
            query_dict[k] = v[0]
        else:
            raise ValueError(f"key:{k},value:{v},is not 1:1,update the code")

    info = {
        "group_id": _decode_uuid(query_dict.get("g")),
        "group_name": query_dict.get("a"),
        "app_key": query_dict.get("y"),
        "owner": _decode_pubkey(query_dict.get("k")),
        "chiperkey": _decode_cipher_key(query_dict.get("c")),
        "url": query_dict.get("u"),
        "timestamp": _decode_timestamp(query_dict.get("t")),
        "genesis_block_id": _decode_uuid(query_dict.get("b")),
    }
    return info
