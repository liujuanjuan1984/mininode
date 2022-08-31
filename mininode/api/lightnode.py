import logging
import time
from typing import Dict, List, Optional

import filetype

from mininode import utils
from mininode.api.base import BaseAPI
from mininode.crypto.account import check_private_key
from mininode.crypto.sign_trx import get_content_param, trx_decrypt, trx_encrypt
from mininode.data import IMAGE_MAX_NUM, IMAGE_MAX_SIZE_KB, ImgContent

logger = logging.getLogger(__name__)


class QuorumLightNodeAPI(BaseAPI):
    def send_content(
        self,
        private_key,
        content: str = None,
        name: str = None,
        images: List = None,
        timestamp=None,
    ):
        if not (content or images):
            raise ValueError("param content or images is required")
        obj = {"type": "Note"}
        if content:
            obj["content"] = content
        if name:
            obj["name"] = name
        if images:
            kb = int(IMAGE_MAX_SIZE_KB // min(len(images), IMAGE_MAX_NUM))
            obj["image"] = [ImgContent(i, kb=kb).__dict__ for i in images[:IMAGE_MAX_NUM]]

        return self.send_trx(private_key, obj=obj, timestamp=timestamp)

    def edit_trx(self, private_key, trx_id, content: str = None, images: List = None, timestamp=None):
        # TODO: 检查发起 edit 的 pubkey 是否为 group owner 或 trx_id 的用户自己
        if not (content or images):
            raise ValueError("param content or images is required")
        obj = {
            "type": "Note",
            "id": trx_id,
        }
        if content:
            obj["content"] = content
        if images:
            obj["image"] = [ImgContent(img).__dict__ for img in images]
        return self.send_trx(private_key, obj=obj, timestamp=timestamp)

    def del_trx(self, private_key, trx_id, timestamp=None):
        obj = {"type": "Note", "id": trx_id, "content": "OBJECT_STATUS_DELETED"}
        return self.send_trx(private_key, obj=obj, timestamp=timestamp)

    def reply_trx(self, private_key, trx_id, content: str = None, images: List = None, timestamp=None):
        if not (content or images):
            raise ValueError("param content or images is required")
        obj = {
            "type": "Note",
            "inreplyto": {"trxid": trx_id},
        }
        if content:
            obj["content"] = content
        if images:
            obj["image"] = [ImgContent(img).__dict__ for img in images]
        return self.send_trx(private_key, obj=obj, timestamp=timestamp)

    def like(self, private_key, trx_id, like_type="Like", timestamp=None):
        if like_type.lower() not in ("like", "dislike"):
            raise ValueError(f"param like_type should be Like or Dislike")
        obj = {"id": trx_id, "type": like_type.title()}
        return self.send_trx(private_key, obj=obj, timestamp=timestamp)

    def update_profile(self, private_key, name=None, image=None, timestamp=None):
        if name is None and image is None:
            raise ValueError("param name or image is required.")
        person = {}
        if name:
            person["name"] = name
        if image:
            file_bytes = utils.zip_image(image, 200)
            person["image"] = {"content": file_bytes, "mediaType": filetype.guess(file_bytes).mime}
        return self.send_trx(private_key, person=person, timestamp=timestamp)

    def send_trx(self, private_key, obj: Dict = None, person: Dict = None, timestamp=None):
        """
        obj/person: dict
        timestamp:2022-10-05 12:34
        """

        private_key = check_private_key(private_key)
        # 此处开放了时间戳的自定义
        if timestamp and isinstance(timestamp, str):
            timestamp = timestamp.replace("/", "-")[:16]
            timestamp = time.mktime(time.strptime(timestamp, "%Y-%m-%d %H:%M"))
        trx = trx_encrypt(self.group_id, self.aes_key, private_key, obj=obj, person=person, timestamp=timestamp)
        return self._post(endpoint=f"/node/trx/{self.group_id}", payload=trx)

    def get_trx(self, trx_id):
        return self._get(endpoint=f"/trx/{self.group_id}/{trx_id}")

    def encrypt_trx(self, encrypted_trx: dict):
        return trx_decrypt(self.aes_key, encrypted_trx)

    def trx(self, trx_id):
        encrypted_trx = self.get_trx(trx_id)
        return self.encrypt_trx(encrypted_trx)

    def get_content(
        self,
        start_trx: str = None,
        num: int = 20,
        reverse: bool = False,
        include_start_trx: bool = False,
        senders=None,
        trx_types=None,
    ):
        # TODO:如果把 senders 传入 quorum，会导致拿不到数据，或数据容易中断，所以实现时拿了全部数据，再筛选senders
        payload = get_content_param(
            self.aes_key, self.group_id, start_trx, num, reverse, include_start_trx, senders=None
        )
        encypted_trxs = self._post(f"/node/groupctn/{self.group_id}", payload=payload)
        # check trx_types:
        if trx_types:
            for i in trx_types:
                if i not in utils.CLIENT_TRX_TYPES:
                    raise ValueError(f"Invalid trx_type. param trx_type is one of {utils.CLIENT_TRX_TYPES}")
        try:
            trxs = [self.encrypt_trx(i) for i in encypted_trxs]
            if senders:
                trxs = [i for i in trxs if i["Publisher"] in senders]
            if trx_types:
                trxs = [trx for trx in trxs if (utils.trx_type(trx) in trx_types)]
        except Exception as e:
            logger.warning(f"get_content error: {e}")
            trxs = encypted_trxs
        return trxs

    def get_all_contents(self, start_trx=None, senders=None, trx_types=None):
        """获取所有内容trxs的生成器，可以用 for...in...来迭代。"""
        # 如果把 senders 传入 quorum，会导致拿不到数据，或数据容易中断，所以实现时拿了全部数据，再筛选senders
        hightest_trxid = None
        _hightest_trxs = self.get_content(reverse=True, include_start_trx=True, num=1)
        if _hightest_trxs:
            hightest_trxid = _hightest_trxs[0].get("TrxId")
        trxs = self.get_content(start_trx=start_trx, num=20, senders=None, trx_types=trx_types)
        checked_trxids = []
        trx_types = trx_types or []
        senders = senders or []
        num = 20
        max_try = 20
        while start_trx != hightest_trxid and max_try > 0:  # 应该用区块高度来判断，而不是是否取得数据。
            if start_trx in checked_trxids:
                num += 20
                max_try -= 1
            else:
                checked_trxids.append(start_trx)
                max_try = 20
            for trx in trxs:
                start_trx = trx["TrxId"]
                flag1 = (utils.trx_type(trx) in trx_types) or (not trx_types)
                flag2 = (trx.get("Publisher", "") in senders) or (not senders)
                if flag1 and flag2:
                    yield trx
            trxs = self.get_content(start_trx=start_trx, num=num, senders=None, trx_types=trx_types)

    def get_profiles(
        self,
        types=("name", "image"),
        senders: Optional[List] = None,
        users: Optional[Dict] = None,  # 已有的data，传入可用来更新数据
    ):
        """初始化或更新用户的 profiles 信息"""
        users = users or {}
        progress_tid = users.get("progress_tid", None)
        trxs = self.get_all_contents(
            start_trx=progress_tid,
            trx_types=["person"],
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

    def trx_retweet_params(self, trx, nicknames: Dict = {}):
        """trans from trx to an object of new trx to send to chain.
        Returns:
            obj: object of new trx,can be used as: self.send_note(obj=obj).
        """

        # 从trx中筛选出引用的 trx_id
        refer_tid = None
        trxtype = utils.trx_type(trx)
        if trxtype == "reply":
            refer_tid = trx["Content"]["inreplyto"]["trxid"]
        elif trxtype in ("like", "dislike"):
            refer_tid = trx["Content"]["id"]
        refer_trx = None
        if refer_tid:
            refer_trx = self.trx(trx_id=refer_tid)
        params = utils.trx_retweet_params_init(trx=trx, refer_trx=refer_trx, nicknames=nicknames)
        return params
