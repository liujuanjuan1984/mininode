import base64
import datetime
import io
import json
import logging
import os
import re
import uuid
from typing import Dict, List
from urllib import parse

import filetype
from PIL import Image

logger = logging.getLogger(__name__)
IMAGE_MAX_SIZE_KB = 200


def get_last_trxid_by_chain(trx_id: str, trxs: List, reverse=False):
    """get the last trx_id of trxs <type: list> which if different from given trx_id by chain index"""
    if reverse:
        _range = range(len(trxs))
    else:
        _range = range(-1, -1 * len(trxs), -1)
    for i in _range:
        tid = trxs[i]["TrxId"]
        if tid != trx_id:
            return tid
    return trx_id


def timestamp_to_datetime(timestamp, rlt_type="dt"):
    ts = int(timestamp)
    n = 10 ** (len(str(ts)) - 10)
    dt = datetime.datetime.fromtimestamp(int(ts / n))
    if rlt_type == "dt":
        return dt
    elif rlt_type == "str":
        return str(dt)


def _get_seed_query(seed_url: str) -> Dict:
    """从 seed_url 转换为 字典形式的参数列表"""
    if not seed_url.startswith("rum://seed?"):
        raise ValueError("invalid Seed URL")

    _q = parse.urlparse(seed_url).query
    _d = parse.parse_qs(_q)

    # 由于 Python 的实现中，每个 key 的 value 都是 列表，所以做了下述处理
    # TODO: 如果 u 参数的值有多个，该方法需升级
    query_dict = {}
    for k, v in _d.items():
        if len(v) == 1:
            query_dict[k] = v[0]
        else:
            raise ValueError(f"key:{k},value:{v},is not 1:1,update the code")
    return query_dict


def _check_b64str(b64str: str) -> bytes:
    """对 base64 字符串检查长度，并补位，转换为字节"""
    l = len(b64str)
    m = (4 - l % 4) % 4
    b64byte = b64str.encode() + b"=" * m
    return b64byte


def _b64_url_decode(b64str):
    b64byte = _check_b64str(b64str)
    b64byte = base64.urlsafe_b64decode(b64byte)
    return b64byte


def _decode_uuid(b64str):
    b64byte = _b64_url_decode(b64str)
    b64uuid = uuid.UUID(bytes=b64byte)
    return str(b64uuid)


def _decode_timestamp(b64str):
    b64byte = _b64_url_decode(b64str)
    bigint = int.from_bytes(b64byte, "big")
    return bigint


def _decode_cipher_key(b64str):
    b64byte = _b64_url_decode(b64str)
    return b64byte.hex()


def _decode_pubkey(b64str):
    b64byte = _b64_url_decode(b64str)
    pubkey = base64.standard_b64encode(b64byte).decode()
    return pubkey


def decode_seed_url(url):
    q = _get_seed_query(url)
    timestamp = _decode_timestamp(q.get("t"))

    info = {
        "group_id": _decode_uuid(q.get("g")),
        "group_name": q.get("a"),
        "app_key": q.get("y"),
        "owner": _decode_pubkey(q.get("k")),
        "chiperkey": _decode_cipher_key(q.get("c")),
        "url": q.get("u"),
        "created_at": timestamp_to_datetime(timestamp, "str"),
        "genesis_block_id": _decode_uuid(q.get("b")),
    }
    return info


def filename_init_from_bytes(file_bytes):
    extension = filetype.guess(file_bytes).extension
    name = f"{uuid.uuid4()}-{datetime.date.today()}"
    return ".".join([name, extension])


def filename_check(name):
    name = re.sub(r"([ :])", r"_", name)
    return name


def read_file_to_bytes(file_path):
    check_file(file_path)
    with open(file_path, "rb") as f:
        bytes_data = f.read()
    return bytes_data


def check_file(file_path):
    if not os.path.exists(file_path):
        raise ValueError(f"{file_path} file is not exists.")

    if not os.path.isfile(file_path):
        raise ValueError(f"{file_path} is not a file.")


def get_filebytes(path_bytes_string):
    _type = type(path_bytes_string)
    _size = len(path_bytes_string)
    is_file = False
    if _type == str:
        if os.path.exists(path_bytes_string):
            file_bytes = read_file_to_bytes(path_bytes_string)
            is_file = True
        else:
            file_bytes = base64.b64decode(path_bytes_string)
    elif _type == bytes:
        file_bytes = path_bytes_string
    else:
        raise TypeError(f"not support for type: {_type} and length: {_size}")
    return file_bytes, is_file


def filename_init(path_bytes_string):
    file_bytes, is_file = get_filebytes(path_bytes_string)
    if is_file:
        file_name = os.path.basename(path_bytes_string).encode().decode("utf-8")
    else:
        file_name = filename_init_from_bytes(file_bytes)
    return file_name


def get_url(base=None, endpoint=None, is_quote=False, **query_params):
    # url = parse.urljoin(base, endpoint) if base else endpoint
    url = ""
    if base:
        url = base
    if endpoint:
        url += endpoint

    if query_params:
        for k, v in query_params.items():
            if type(v) == bool:
                query_params[k] = json.dumps(v)
        query_ = parse.urlencode(query_params)
        if is_quote:
            query_ = parse.quote(query_, safe="?&/")
        return "?".join([url, query_])
    return url


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


def zip_gif(gif, kb=IMAGE_MAX_SIZE_KB, cover=False):
    """压缩动图(gif)到指定大小(kb)以下

    gif: gif 格式动图本地路径
    kb: 指定压缩大小, 默认 200kb
    cover: 是否覆盖原图, 默认不覆盖

    返回压缩后图片字节. 该方法需要安装 gifsicle 软件和 pygifsicle 模块
    """
    from pygifsicle import gifsicle

    kb = kb or IMAGE_MAX_SIZE_KB
    size = os.path.getsize(gif) / 1024
    if size < kb:
        return read_file_to_bytes(gif)

    destination = None
    if not cover:
        destination = f"{os.path.splitext(gif)[0]}-zip.gif"

    n = 0.9
    while size >= kb:
        gifsicle(
            gif,
            destination=destination,
            optimize=True,
            options=["--lossy=80", "--scale", str(n)],
        )
        if not cover:
            gif = destination
        size = os.path.getsize(gif) / 1024
        n -= 0.05

    return read_file_to_bytes(gif)


def zip_image_bytes(img_bytes, kb=IMAGE_MAX_SIZE_KB):
    """zip image bytes and return bytes; default changed to .jpeg"""

    kb = kb or IMAGE_MAX_SIZE_KB
    guess_extension = filetype.guess(img_bytes).extension

    with io.BytesIO(img_bytes) as im:
        size = len(im.getvalue()) // 1024
        if size < kb:
            return img_bytes
        while size >= kb:
            img = Image.open(im)
            x, y = img.size
            out = img.resize((int(x * 0.95), int(y * 0.95)), Image.ANTIALIAS)
            im.close()
            im = io.BytesIO()
            try:
                out.save(im, "jpeg")
            except:
                out.save(im, guess_extension)
            size = len(im.getvalue()) // 1024
        return im.getvalue()


def zip_image(path_bytes_string, kb=IMAGE_MAX_SIZE_KB):
    file_bytes, is_file = get_filebytes(path_bytes_string)

    try:
        if filetype.guess(file_bytes).extension == "gif" and is_file:
            img_bytes = zip_gif(path_bytes_string, kb=kb, cover=False)
        else:
            img_bytes = zip_image_bytes(file_bytes, kb=kb)
    except Exception as e:
        logger.warning(f"zip_image {e}")
    return img_bytes


def trx_typeurl(trx):
    typeurl = trx.get("TypeUrl")
    if typeurl == "quorum.pb.Person":
        return "Person"
    elif typeurl == "quorum.pb.Object":
        return "Object"
    return typeurl


def trx_type(trx: Dict):
    """get type of trx, trx is one of group content list"""
    typeurl = trx_typeurl(trx)
    if not typeurl:
        return "encrypted"
    if typeurl == "Person":
        return "person"
    content = trx.get("Content", {})
    trxtype = content.get("type", "other")
    if type(trxtype) == int:
        return "announce"
    if trxtype == "Note":
        if "inreplyto" in content:
            return "reply"
        if "image" in content:
            if "content" not in content:
                return "image_only"
            else:
                return "image_text"
        return "text_only"
    return trxtype.lower()  # "like","dislike","other"


def _init_profile_status(trx_content):
    _name = "昵称" if "name" in trx_content else ""
    _wallet = "钱包" if "wallet" in trx_content else ""
    _image = "头像" if "image" in trx_content else ""
    _profile = "、".join([i for i in [_name, _image, _wallet] if i])
    return _profile


def _get_content(trx_content):
    _text = trx_content.get("content", "")
    _imgs = []
    if "image" in trx_content:
        imgs = trx_content["image"]
        if type(imgs) == list:
            _imgs = imgs
        elif type(imgs) == dict:
            _imgs = [imgs]
        else:
            raise ParamValueError(f"type {type(imgs)} is not supported.")
    return _text, _imgs


def get_nickname(pubkey, nicknames):
    try:
        name = nicknames[pubkey]["name"] + f"({pubkey[-10:-2]})"
    except:
        name = pubkey[-10:-2] or "某人"
    return name


def _quote_str(text):
    return "".join(["> ", "\n> ".join(text.split("\n")), "\n"]) if text else ""


def trx_retweet_params_init(trx, refer_trx=None, nicknames={}, without_images=False):
    if "Content" not in trx:
        return None

    refer_trx = refer_trx or {}
    refer_pubkey = refer_trx.get("Publisher", "")
    refer_nickname = get_nickname(refer_pubkey, nicknames)
    refer_text, refer_imgs = _get_content(refer_trx.get("Content", {}))
    refer_dt = timestamp_to_datetime(refer_trx.get("TimeStamp", 1661957509240230200))
    trx_content = trx["Content"]
    trxtype = trx_type(trx)
    text, imgs = _get_content(trx_content)
    nickname = get_nickname(trx["Publisher"], nicknames)
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

    content = f"{nickname} {_dt}" + "\n".join(lines)
    return {"content": content, "images": images}
