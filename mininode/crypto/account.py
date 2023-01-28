"""account.py"""
import base64
import logging
from typing import Dict, Union

import eth_keys
from eth_account import Account
from eth_utils.hexadecimal import encode_hex

logger = logging.getLogger(__name__)


def create_private_key() -> str:
    """create private key"""
    acc = Account().create()
    private_key = encode_hex(acc.privateKey)
    return private_key


def check_private_key(private_key: Union[str, int, bytes]) -> bytes:
    """check private key"""
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


def private_key_to_address(private_key: Union[str, int, bytes]) -> str:
    """private key to address"""
    private_key = check_private_key(private_key)
    address = Account().from_key(private_key).address
    return address


def public_key_to_address(public_key: str) -> str:
    """public key to address"""
    public_key = base64.urlsafe_b64decode(public_key)
    pubkey = eth_keys.keys.PublicKey.from_compressed_bytes(public_key)
    address = pubkey.to_checksum_address()
    return address


def private_key_to_pubkey(private_key: Union[str, int, bytes]) -> str:
    """private key to public key"""
    private_key = check_private_key(private_key)
    account = eth_keys.keys.PrivateKey(private_key)
    public_key = base64.urlsafe_b64encode(account.public_key.to_compressed_bytes()).decode()
    return public_key


def private_key_to_keystore(private_key: Union[str, int, bytes], password: str):
    """private key to keystore with password"""
    private_key = check_private_key(private_key)
    keystore = Account().from_key(private_key).encrypt(password=password)
    return keystore


def keystore_to_private_key(keystore: Dict, password: str) -> str:
    """keystore with password to private key"""
    pvtkey = Account().decrypt(keystore, password)
    private_key = encode_hex(pvtkey)
    return private_key
