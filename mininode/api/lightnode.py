"""lightnode.py"""
import base64
import json
import logging
import time
from typing import Dict, List, Optional, Tuple, Union

from mininode import utils
from mininode.api.base import BaseAPI
from mininode.crypto.account import check_private_key, private_key_to_pubkey
from mininode.crypto.sign_trx import aes_encrypt, trx_decrypt, trx_encrypt

logger = logging.getLogger(__name__)


class QuorumLightNodeAPI(BaseAPI):
    """the light node api for quorum"""

    def send_content(
        self,
        private_key,
        content: Optional[str] = None,
        name: Optional[str] = None,
        images: Optional[List] = None,
        timestamp: Union[str, int, float, None] = None,
    ):
        """send content"""
        if not (content or images):
            raise ValueError("param content or images is required")
        obj = {"type": "Note"}
        if content:
            obj["content"] = content
        if name:
            obj["name"] = name
        if images:
            obj["image"] = utils.pack_images(images)

        return self.send_trx(private_key, obj=obj, timestamp=timestamp)

    def edit_trx(
        self,
        private_key: Union[str, int, bytes],
        trx_id: str,
        check_sender: bool = False,
        content: Optional[str] = None,
        images: Optional[List] = None,
        timestamp: Union[str, int, float, None] = None,
    ):
        """edit trx content, which is to send a new trx but connected to the old trx."""
        if check_sender:
            sender = self.get_trx(trx_id).get("SenderPubkey")
            user = private_key_to_pubkey(private_key)
            if user != sender:
                raise ValueError("You are not the sender of the trx, you can't edit it.")

        if not (content or images):
            raise ValueError("param content or images is required")
        obj = {
            "type": "Note",
            "id": trx_id,
        }
        if content:
            obj["content"] = content
        if images:
            obj["image"] = utils.pack_images(images)
        return self.send_trx(private_key, obj=obj, timestamp=timestamp)

    def del_trx(
        self,
        private_key: Union[str, int, bytes],
        trx_id: str,
        timestamp: Union[str, int, float, None] = None,
    ):
        """mark trx as delete, which is to send a new trx but connected to the old trx."""
        obj = {"type": "Note", "id": trx_id, "content": "OBJECT_STATUS_DELETED"}
        return self.send_trx(private_key, obj=obj, timestamp=timestamp)

    def reply_trx(
        self,
        private_key: Union[str, int, bytes],
        trx_id: str,
        content: Optional[str] = None,
        images: Optional[List] = None,
        timestamp: Union[str, int, float, None] = None,
    ):
        """reply trx"""
        if not (content or images):
            raise ValueError("param content or images is required")
        obj = {
            "type": "Note",
            "inreplyto": {"trxid": trx_id},
        }
        if content:
            obj["content"] = content
        if images:
            obj["image"] = utils.pack_images(images)
        return self.send_trx(private_key, obj=obj, timestamp=timestamp)

    def like(
        self,
        private_key: Union[str, int, bytes],
        trx_id: str,
        like_type: str = "Like",
        timestamp: Union[str, int, float, None] = None,
    ):
        """like trx"""
        if like_type.lower() not in ("like", "dislike"):
            raise ValueError("param like_type should be Like or Dislike")
        obj = {"id": trx_id, "type": like_type.title()}
        return self.send_trx(private_key, obj=obj, timestamp=timestamp)

    def update_profile(
        self,
        private_key: Union[str, int, bytes],
        name: Optional[str] = None,
        image: Optional[str] = None,
        timestamp: Union[str, int, float, None] = None,
    ):
        """update profile"""
        if name is None and image is None:
            raise ValueError("param name or image is required.")
        person = {}
        if name:
            person["name"] = name
        if image:
            person["image"] = utils.pack_profile_image(image)
        return self.send_trx(private_key, person=person, timestamp=timestamp)

    def send_trx(
        self,
        private_key: Union[str, int, bytes],
        obj: Optional[Dict] = None,
        person: Optional[Dict] = None,
        timestamp: Union[str, int, float, None] = None,
    ):
        """
        obj/person: dict
        timestamp:2022-10-05 12:34
        """

        private_key = check_private_key(private_key)
        # 此处开放了时间戳的自定义
        if timestamp and isinstance(timestamp, str):
            timestamp = timestamp.replace("/", "-")[:16]
            timestamp = time.mktime(time.strptime(timestamp, "%Y-%m-%d %H:%M"))
        trx = trx_encrypt(
            self.group_id,
            self.aes_key,
            private_key,
            obj=obj,
            person=person,
            timestamp=timestamp,
            version=self.version,
        )
        return self._post(endpoint=f"/node/trx/{self.group_id}", payload=trx)

    def get_trx(self, trx_id: str):
        """get encrpyted trx"""
        return self._get(endpoint=f"/trx/{self.group_id}/{trx_id}")

    def trx(self, trx_id: str):
        """get decrypted trx"""
        encrypted_trx = self.get_trx(trx_id)
        trx = trx_decrypt(self.aes_key, encrypted_trx)
        return trx

    def get_content(
        self,
        start_trx: Optional[str] = None,
        num: int = 20,
        reverse: bool = False,
        include_start_trx: bool = False,
        senders: Optional[List] = None,
        trx_types: Optional[Tuple] = None,
    ):
        """get content"""
        # TODO:如果把 senders 传入 quorum，会导致拿不到数据，或数据容易中断，所以实现时拿了全部数据，再筛选senders

        params = {
            "group_id": self.group_id,
            "reverse": "true" if reverse is True else "false",
            "num": num,
            "include_start_trx": "true" if include_start_trx is True else "false",
            "senders": [],
        }
        if start_trx:
            params["start_trx"] = start_trx

        payload = {
            "Req": self._pack_obj({"Req": params}),
        }
        encypted_trxs = self._post(f"/node/groupctn/{self.group_id}", payload=payload)

        # check trx_types:
        if trx_types:
            for i in trx_types:
                if i not in utils.CLIENT_TRX_TYPES:
                    raise ValueError(
                        "Invalid trx_type. param trx_type is one of %s", str(utils.CLIENT_TRX_TYPES)
                    )
        # chooce trxs:
        try:
            trxs = [trx_decrypt(self.aes_key, i) for i in encypted_trxs]
            if senders:
                trxs = [i for i in trxs if i["Publisher"] in senders]
            if trx_types:
                trxs = [trx for trx in trxs if utils.get_trx_type(trx) in trx_types]
        except Exception as err:
            logger.warning("get_content error: %s", err)
            trxs = encypted_trxs
        return trxs

    def __get_all_contents(
        self,
        start_trx: Optional[str] = None,
    ):
        """get all contents as a generator"""
        hightest_trxid = None
        _hightest_trxs = self.get_content(reverse=True, include_start_trx=True, num=1)
        if _hightest_trxs:
            hightest_trxid = _hightest_trxs[0].get("TrxId")
        trxs = self.get_content(start_trx=start_trx, num=20)
        checked_trxids = []
        num = 20
        max_try = 30
        while start_trx != hightest_trxid and max_try > 0:  # 应该用区块高度来判断，而不是是否取得数据。
            if start_trx in checked_trxids:
                num += 20
                max_try -= 1
            else:
                checked_trxids.append(start_trx)
                max_try = 30
            for trx in trxs:
                start_trx = trx["TrxId"]
                yield trx
            trxs = self.get_content(start_trx=start_trx, num=num)

    def get_all_contents(
        self,
        start_trx: Optional[str] = None,
        senders: Optional[List] = None,
        trx_types: Optional[Tuple] = None,
    ):
        """get all contents as a generator"""
        # 如果把 senders 传入 quorum，会导致拿不到数据，或数据容易中断，所以实现时拿了全部数据，再筛选senders
        trx_types = trx_types or []
        senders = senders or []
        for trx in self.__get_all_contents(start_trx):
            flag1 = (utils.get_trx_type(trx) in trx_types) or (not trx_types)
            flag2 = (trx.get("Publisher", "") in senders) or (not senders)
            if flag1 and flag2:
                yield trx

    def get_profiles(
        self,
        types=("name", "image"),
        senders: Optional[List] = None,
        users: Optional[Dict] = None,  # 已有的data，传入可用来更新数据
    ):
        """get profiles of users"""
        users = users or {}
        progress_tid = users.get("progress_tid", None)
        trxs = self.get_all_contents(
            start_trx=progress_tid,
            trx_types=("person",),
            senders=senders,
        )

        for trx in trxs:
            progress_tid = trx["TrxId"]
            trx_content = trx.get("Content", {})
            pubkey = trx["Publisher"]

            if pubkey not in users:
                users[pubkey] = {}
            for key in types:
                if key in trx_content:
                    users[pubkey][key] = trx_content[key]

        users["progress_tid"] = progress_tid
        return users

    def trx_retweet_params(self, trx: Dict, nicknames: Optional[Dict] = None, **kwargs) -> Dict:
        """trans from trx to an object of new trx to send to chain.
        Returns:
            obj: object of new trx,can be used as: self.send_note(obj=obj).
        """
        # 从trx中筛选出引用的 trx_id
        refer_tid = None

        trxtype = utils.get_trx_type(trx)
        if trxtype == "reply":
            refer_tid = trx["Content"]["inreplyto"]["trxid"]
        elif trxtype in ("like", "dislike"):
            refer_tid = trx["Content"]["id"]
        refer_trx = None
        if refer_tid:
            refer_trx = self.trx(trx_id=refer_tid)
        params = utils.init_trx_retweet_params(
            trx=trx, refer_trx=refer_trx, nicknames=nicknames, **kwargs
        )
        return params

    def _pack_obj(self, obj: Dict[str, str]) -> str:
        """pack obj with group chiperkey and return a string"""
        obj_bytes = json.dumps(obj).encode()
        obj_encrypted = aes_encrypt(self.aes_key, obj_bytes)
        req = base64.b64encode(obj_encrypted).decode()
        return req

    def _get_chaindata(self, obj: Dict, req_type: str):
        """base api of get chaindata"""
        payload = {
            "Req": self._pack_obj(obj),
            "ReqType": req_type,
        }
        return self._post(endpoint=f"/node/getchaindata/{self.group_id}", payload=payload)

    def get_group_info(self):
        """get group info"""
        obj = {"GroupId": self.group_id}
        return self._get_chaindata(obj, "group_info")

    def get_auth_type(self, trx_type: str):
        """get auth type of trx_type"""
        obj = {"GroupId": self.group_id, "TrxType": trx_type}
        return self._get_chaindata(obj, "auth_type")

    def get_auth_allowlist(self):
        """get allowlist"""
        obj = {"GroupId": self.group_id}
        return self._get_chaindata(obj, "auth_allowlist")

    def get_auth_denylist(self):
        """get denylist"""
        obj = {"GroupId": self.group_id}
        return self._get_chaindata(obj, "auth_denylist")

    def get_appconfig_keylist(self):
        """get appconfig keylist"""
        obj = {"GroupId": self.group_id}
        return self._get_chaindata(obj, "appconfig_listlist")

    def get_appconfig_key(self, key: str):
        """get appconfig key value by keyname"""
        obj = {"GroupId": self.group_id, "Key": key}
        return self._get_chaindata(obj, "appconfig_item_bykey")

    def get_group_producer(self):
        """get group producers"""
        obj = {"GroupId": self.group_id}
        return self._get_chaindata(obj, "group_producer")

    def get_announced_producer(self):
        """get announced producer"""
        obj = {"GroupId": self.group_id}
        return self._get_chaindata(obj, "announced_producer")

    def get_announced_user(self, pubkey: str):
        """get announced user info by pubkey"""
        obj = {"GroupId": self.group_id, "SignPubkey": pubkey}
        return self._get_chaindata(obj, "announced_user")
