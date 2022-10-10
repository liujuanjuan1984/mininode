"""sign_trx.py"""
import base64
import hashlib
import json
import logging
import os
import time
import uuid
from typing import Any, Dict, Union

import eth_keys
from Crypto.Cipher import AES
from google.protobuf import any_pb2, json_format

from mininode.crypto.account import private_key_to_pubkey
from mininode.proto import pbQuorum

logger = logging.getLogger(__name__)
nonce = 1


def aes_encrypt(key: bytes, data: bytes) -> bytes:
    """aes encrypt"""
    cipher = AES.new(key, AES.MODE_GCM, nonce=os.urandom(12))
    ciphertext, tag = cipher.encrypt_and_digest(data)
    return b"".join([cipher.nonce, ciphertext, tag])


def aes_decrypt(key: bytes, data: bytes) -> bytes:
    """aes decrypt"""
    nonce, tag = data[:12], data[-16:]
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(data[12:-16], tag)


def check_timestamp(timestamp: Union[str, int, float, None] = None):
    """check timestamp"""
    if timestamp is None:
        return int(time.time() * 1e9)
    try:
        timestamp = str(timestamp).replace(".", "")
        if len(timestamp) > 19:
            timestamp = timestamp[:19]
        elif len(timestamp) < 19:
            timestamp += "0" * (19 - len(timestamp))
        timestamp = int(timestamp)
        return timestamp
    except Exception as err:
        logger.info("timestamp error: %s", err)
        return int(time.time() * 1e9)


def trx_encrypt(
    group_id: str,
    aes_key: bytes,
    private_key: bytes,
    obj: Dict[str, Any] = None,
    person: Dict[str, Any] = None,
    timestamp=None,
) -> Dict[str, str]:
    """trx encrypt"""
    # pylint: disable=W,E,R
    if obj is None and person is None:
        raise ValueError("obj and person is None")
    if obj is not None and person is not None:
        raise ValueError("obj and person is not None")
    if obj is not None:
        obj_pb = pbQuorum.Object(**obj)
    elif person is not None:
        obj_pb = pbQuorum.Person(**person)
    any_obj_pb = any_pb2.Any()
    any_obj_pb.Pack(obj_pb, type_url_prefix="type.googleapis.com/")
    data = any_obj_pb.SerializeToString()
    encrypted = aes_encrypt(aes_key, data)

    priv = eth_keys.keys.PrivateKey(private_key)
    sender_pub_key = private_key_to_pubkey(private_key)

    timestamp = check_timestamp(timestamp)
    global nonce
    trx = {
        "TrxId": str(uuid.uuid4()),
        "GroupId": group_id,
        "Data": encrypted,
        "TimeStamp": timestamp,
        "Version": "1.0.0",
        "Expired": timestamp + int(30 * 1e9),
        "Nonce": nonce + 1,
        "SenderPubkey": sender_pub_key,
    }

    trx_without_sign_pb = pbQuorum.Trx(**trx)
    trx_without_sign_pb_bytes = trx_without_sign_pb.SerializeToString()
    trx_hash = hashlib.sha256(trx_without_sign_pb_bytes).digest()
    signature = priv.sign_msg_hash(trx_hash).to_bytes()
    trx["SenderSign"] = signature

    trx_pb = pbQuorum.Trx(**trx)
    trx_json_str = json.dumps(
        {
            "TrxBytes": base64.b64encode(trx_pb.SerializeToString()).decode(),
        }
    )

    enc_trx_json = aes_encrypt(aes_key, trx_json_str.encode())

    send_trx_obj = {
        "GroupId": group_id,
        "TrxItem": base64.b64encode(enc_trx_json).decode(),
    }
    return send_trx_obj


def trx_decrypt(aes_key: bytes, encrypted_trx: Dict):
    """trx decrypt"""
    # pylint: disable=W,E,R
    data = encrypted_trx.get("Data")
    if data is None:
        raise ValueError("Data is None")
    data = base64.b64decode(data)
    data = aes_decrypt(aes_key, data)
    any_obj = any_pb2.Any().FromString(data)
    if any_obj.type_url.find("quorum.pb.Person") >= 0:
        typeurl = "quorum.pb.Person"
        obj = pbQuorum.Person()
    elif any_obj.type_url.find("quorum.pb.Object") >= 0:
        typeurl = "quorum.pb.Object"
        obj = pbQuorum.Object()
    else:
        raise ValueError("type_url is not quorum.pb.Person or quorum.pb.Object")
    any_obj.Unpack(obj)
    dict_obj = json_format.MessageToDict(obj)
    decrpyted_trx = {
        "TrxId": encrypted_trx.get("TrxId"),
        "Publisher": encrypted_trx.get("SenderPubkey"),
        "Content": dict_obj,
        "TypeUrl": typeurl,
        "TimeStamp": encrypted_trx.get("TimeStamp"),
    }
    return decrpyted_trx


def pack_content_param(
    aes_key: bytes,
    group_id: str,
    start_trx: str = None,
    num: int = 20,
    reverse: bool = False,
    include_start_trx: bool = False,
    senders=None,
) -> Dict[str, str]:
    """pack content param"""
    params = {
        "group_id": group_id,
        "reverse": "true" if reverse is True else "false",
        "num": num,
        "include_start_trx": "true" if include_start_trx is True else "false",
        "senders": senders or [],
    }
    if start_trx:
        params["start_trx"] = start_trx

    get_group_ctn_item = {
        "Req": params,
    }

    get_group_ctn_item_str = json.dumps(get_group_ctn_item)
    encrypted = aes_encrypt(aes_key, get_group_ctn_item_str.encode())
    send_param = {
        "Req": base64.b64encode(encrypted).decode(),
    }

    return send_param
