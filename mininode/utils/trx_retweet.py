import datetime
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

CLIENT_TRX_TYPES = [
    "encrypted",
    "person",
    "announce",
    "reply",
    "image_only",
    "image_text",
    "text_only",
    "like",
    "dislike",
    "other",
]


def timestamp_to_datetime(timestamp, rlt_type="dt"):
    ts = int(timestamp)
    n = 10 ** (len(str(ts)) - 10)
    dt = datetime.datetime.fromtimestamp(int(ts / n))
    if rlt_type == "dt":
        return dt
    return str(dt)


def _get_content(trx_content: Dict) -> Tuple[str, List]:
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
    try:
        name = nicknames[pubkey]["name"] + f"({pubkey[-10:-2]})"
    except:
        name = pubkey[-10:-2] or "某人"
    return name


def _quote_str(text: str) -> str:
    return "> " + text.replace("\n", "\n> ") + "\n"


def _init_profile_status(trx_content: Dict) -> str:
    _name = "昵称" if "name" in trx_content else ""
    _wallet = "钱包" if "wallet" in trx_content else ""
    _image = "头像" if "image" in trx_content else ""
    _profile = "、".join([i for i in [_name, _image, _wallet] if i])
    return _profile


def get_trx_type(trx: Dict) -> str:
    """get type of trx, trx is one of group content list"""
    typeurl = trx.get("TypeUrl")
    if typeurl == "quorum.pb.Person":
        return "person"
    elif typeurl != "quorum.pb.Object":
        return "encrypted"
    content = trx.get("Content", {})
    trxtype = content.get("type")
    if isinstance(trxtype, int):
        return "announce"
    elif isinstance(trxtype, str):
        if trxtype == "Note":
            if "inreplyto" in content:
                return "reply"
            if "image" in content:
                if "content" not in content:
                    return "image_only"
                else:
                    return "image_text"
            return "text_only"
        return trxtype.lower()  # "like","dislike","file"
    else:
        return "other"


def init_trx_retweet_params(
    trx: Dict, refer_trx: Optional[Dict] = None, nicknames: Optional[Dict] = None, without_images: bool = False
) -> Dict:
    if "Content" not in trx:
        return {}
    nicknames = nicknames or {}
    refer_trx = refer_trx or {}
    refer_pubkey = refer_trx.get("Publisher", "")
    refer_nickname = _get_nickname(refer_pubkey, nicknames)
    refer_text, refer_imgs = _get_content(refer_trx.get("Content", {}))
    refer_dt = timestamp_to_datetime(refer_trx.get("TimeStamp", 1661957509240230200))
    trx_content = trx["Content"]
    trxtype = get_trx_type(trx)
    text, imgs = _get_content(trx_content)
    nickname = _get_nickname(trx["Publisher"], nicknames)
    _dt = timestamp_to_datetime(trx.get("TimeStamp"))

    images = []
    lines = []

    if trxtype == "person":
        _profile = _init_profile_status(trx_content)
        lines.append(f"修改了个人信息：{_profile}。")
    elif trxtype == "file":
        lines.append("上传了文件。")
    elif trxtype == "announce":
        lines.append("处理了链上请求。")
    elif trxtype == "like":
        lines.append(f"点赞给 `{refer_nickname}` ")
    elif trxtype == "dislike":
        lines.append(f"点踩给 `{refer_nickname}` ")
    elif trxtype == "text_only":
        lines.insert(0, f"说：")
        lines.append(text)
    elif trxtype == "image_text":
        lines.insert(0, f"发布了图片，并且说：")
        lines.append(text)
        if not without_images:
            images.extend(imgs)
    elif trxtype == "image_only":
        lines.insert(0, f"发布了 {len(imgs)} 张图片。")
        if not without_images:
            images.extend(imgs)
    elif trxtype == "reply":
        if text and imgs:
            lines.insert(0, f"回复了 {len(imgs)} 张图片，并且说：")
            lines.append(text)
        elif text:
            lines.insert(0, f"回复说：")
            lines.append(text)
        elif imgs:
            lines.insert(0, f"回复了 {len(imgs)} 张图片。")
            if not without_images:
                images.extend(imgs)
        lines.append(f"\n回复给 `{refer_nickname}` ")

    if refer_text and refer_imgs:
        lines[-1] += f"{refer_dt} 所发布的文本及 {len(refer_imgs)} 张图片："
        lines.append(_quote_str(refer_text))
        if not without_images:
            images.extend(refer_imgs)
    elif refer_text:
        lines[-1] += f"{refer_dt} 所发布的内容："
        lines.append(_quote_str(refer_text))
    elif refer_imgs:
        lines[-1] += f"{refer_dt} 所发布的 {len(refer_imgs)} 张图片。"
        if not without_images:
            images.extend(refer_imgs)

    content = f"{nickname} {_dt} " + "\n".join(lines)
    return {"content": content, "images": images}
