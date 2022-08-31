import logging
from typing import Dict

from eth_account import Account
from eth_utils.hexadecimal import encode_hex

logger = logging.getLogger(__name__)


def create_private_key() -> str:
    acc = Account.create()
    private_key = encode_hex(acc.privateKey)
    return private_key


def private_key_to_address(private_key) -> str:
    return Account.from_key(private_key).address


def check_private_key(private_key: str) -> bytes:
    if isinstance(private_key, int):
        private_key = hex(private_key)
    if isinstance(private_key, str):
        if private_key.startswith("0x"):
            private_key = bytes.fromhex(private_key[2:])
        else:
            private_key = bytes.fromhex(private_key)
    elif isinstance(private_key, bytes):
        pass
    else:
        raise ValueError("Invalid private key. param private_key is required.")
    if len(private_key) != 32:
        raise ValueError("Invalid private key. param private_key is required.")
    return private_key


def private_key_to_keystore(private_key, password: str):
    return Account.from_key(private_key).encrypt(password=password)


def keystore_to_private_key(keystore: Dict, password: str) -> str:
    pvtkey = Account.decrypt(keystore, password)
    private_key = encode_hex(pvtkey)
    return private_key
