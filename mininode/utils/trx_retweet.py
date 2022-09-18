"""trx retweet"""

import datetime
import logging
from typing import Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

CLIENT_TRX_TYPES = [
    "encrypted",
    "person",
    "announce",
    "reply",
    "reply_image_only",
    "reply_image_text",
    "reply_text_only",
    "image_only",
    "image_text",
    "text_only",
    "like",
    "dislike",
    "other",
]


def timestamp_to_datetime(timestamp: Union[str, int, float], rlt_type="dt"):
    """timestamp to datetime"""
    int_timstamp = int(timestamp)
    length = 10 ** (len(str(int_timstamp)) - 10)
    datetime_rlt = datetime.datetime.fromtimestamp(int(int_timstamp / length))
    if rlt_type == "dt":
        return datetime_rlt
    return str(datetime_rlt)


def _get_content(trx_content: Dict) -> Tuple[str, List]:
    """get content from trx"""
    _text = trx_content.get("content", "")
    _imgs = []
    if "image" in trx_content:
        imgs = trx_content["image"]
        if isinstance(imgs, list):
            _imgs = imgs
        elif isinstance(imgs, dict):
            _imgs = [imgs]
        else:
            raise ValueError(f"type {type(imgs)} is not supported.")
    return _text, _imgs


def _get_nickname(pubkey: str, nicknames: Dict) -> str:
    """get nickname from nicknames by pubkey"""
    try:
        name = nicknames[pubkey]["name"] + f"({pubkey[-10:-2]})"
    except Exception as err:
        name = pubkey[-10:-2] or "某人"
    return name


def _quote_str(text: str) -> str:
    """quote text"""
    return "> " + text.replace("\n", "\n> ") + "\n"


def _init_profile_status(trx_content: Dict) -> str:
    """init status string from trx_content about profile"""
    _name = "昵称" if "name" in trx_content else ""
    _wallet = "钱包" if "wallet" in trx_content else ""
    _image = "头像" if "image" in trx_content else ""
    _profile = "、".join([i for i in [_name, _image, _wallet] if i])
    return _profile


def get_trx_type(trx: Dict, deep_to_reply=False) -> str:
    """get type of trx, trx is one of group content list"""
    typeurl = trx.get("TypeUrl")
    if typeurl == "quorum.pb.Person":
        return "person"
    if typeurl != "quorum.pb.Object":
        return "encrypted"

    content = trx.get("Content", {})
    trxtype = content.get("type", "other")
    if isinstance(trxtype, int):
        return "announce"
    if not isinstance(trxtype, str):
        return trxtype
    if trxtype != "Note":
        return trxtype.lower()  # "like","dislike","file"

    if "inreplyto" in content:
        if not deep_to_reply:
            return "reply"
        if "image" in content:
            if "content" not in content:
                result = "reply_image_only"
            else:
                result = "reply_image_text"
        else:
            result = "reply_text_only"
        return result

    if "image" in content:
        if "content" not in content:
            result = "image_only"
        else:
            result = "image_text"
    else:
        result = "text_only"
    return result


def init_trx_retweet_params(
    trx: Dict,
    refer_trx: Optional[Dict] = None,
    nicknames: Optional[Dict] = None,
    without_images: bool = False,
    without_quote_text: bool = False,
    without_timestamp: bool = False,
) -> Dict:
    """init params for trx retweet"""
    if "Content" not in trx:
        return {}
    nicknames = nicknames or {}
    refer_trx = refer_trx or {}
    refer_pubkey = refer_trx.get("Publisher", "")
    refer_nickname = _get_nickname(refer_pubkey, nicknames)
    refer_text, refer_imgs = _get_content(refer_trx.get("Content", {}))
    refer_dt = str(timestamp_to_datetime(refer_trx.get("TimeStamp", 1661957509240230200))) + " "
    trx_content = trx["Content"]
    trxtype = get_trx_type(trx, deep_to_reply=True)
    text, imgs = _get_content(trx_content)
    nickname = _get_nickname(trx["Publisher"], nicknames)
    _dt = str(timestamp_to_datetime(trx.get("TimeStamp"))) + " "
    if without_timestamp:
        refer_dt = _dt = ""

    images = []
    lines = []

    info = {
        "person": f"修改了个人信息：{_init_profile_status(trx_content)}。",
        "file": "上传了文件。",
        "announce": "处理了链上请求。",
        "like": f"点赞给 `{refer_nickname}` ",
        "dislike": f"点踩给 `{refer_nickname}` ",
        "text_only": "说：\n" + text,
        "image_text": "发布了图片，并且说：\n" + text,
        "image_only": f"发布了 {len(imgs)} 张图片。",
        "reply_image_text": f"回复了 {len(imgs)} 张图片，并且说：\n" + text,
        "reply_text_only": "回复说：" + text,
        "reply_image_only": f"回复了 {len(imgs)} 张图片。",
    }

    if trxtype in info:
        lines.append(info[trxtype])

    if trxtype.find("reply") >= 0:
        lines.append(f"\n回复给 `{refer_nickname}` ")

    if refer_text and refer_imgs:
        lines[-1] += f"{refer_dt}所发布的文本及 {len(refer_imgs)} 张图片："
    elif refer_text:
        lines[-1] += f"{refer_dt}所发布的内容："
    elif refer_imgs:
        lines[-1] += f"{refer_dt}所发布的 {len(refer_imgs)} 张图片。"

    if not without_images:
        images.extend(imgs + refer_imgs)
    if not without_quote_text and refer_text:
        lines.append(_quote_str(refer_text))

    content = f"{nickname} {_dt}" + "\n".join(lines)
    return {"content": content, "images": images}
