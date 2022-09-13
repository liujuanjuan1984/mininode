"""image"""
import base64
import datetime
import io
import logging
import os
import re
import uuid
from typing import Dict, List, Union

import filetype
from PIL import Image
from pygifsicle import gifsicle

logger = logging.getLogger(__name__)


# 将一张或多张图片处理成 RUM 支持的图片对象列表, 要求总大小小于 200kb，此为链端限定
IMAGE_MAX_SIZE_KB = 200  # 200 kb 每条trx中所包含的图片总大小限制为 200
# 单条 trx 最多4 张图片；此为 rum app 客户端限定：第三方 app 调整该限定
IMAGE_MAX_NUM = 4
CHUNK_SIZE = 150 * 1024  # 150 kb，文件切割为多条trxs时，每条trx所包含的文件字节流上限


def _read_file_to_bytes(file_path: str) -> bytes:
    """read the file data as bytes"""
    if not os.path.exists(file_path):
        raise ValueError(f"{file_path} file is not exists.")
    if not os.path.isfile(file_path):
        raise ValueError(f"{file_path} is not a file.")
    with open(file_path, "rb") as read_f:
        data = read_f.read()
    return data


def get_filebytes(path_bytes_string) -> bytes:
    """get the filebytes"""
    _size = len(path_bytes_string)
    is_file = False
    if isinstance(path_bytes_string, str):
        if os.path.exists(path_bytes_string):
            file_bytes = _read_file_to_bytes(path_bytes_string)
            is_file = True
        else:
            file_bytes = base64.b64decode(path_bytes_string)
    elif isinstance(path_bytes_string, bytes):
        file_bytes = path_bytes_string
    else:
        raise TypeError(f"not support for type: {type(path_bytes_string)} and length: {_size}")
    return file_bytes, is_file


def _zip_gif(gif: str, max_size: int = IMAGE_MAX_SIZE_KB, is_cover: bool = False):
    """压缩动图(gif)到指定大小(kb)以下

    gif: gif 格式动图本地路径
    max_size: 指定压缩大小, 默认 200kb
    is_cover: 是否覆盖原图, 默认不覆盖

    返回压缩后图片字节. 该方法需要安装 gifsicle 软件和 pygifsicle 模块
    """

    max_size = max_size or IMAGE_MAX_SIZE_KB
    size = os.path.getsize(gif) / 1024
    if size < max_size:
        return _read_file_to_bytes(gif)

    destination = None
    if not is_cover:
        destination = f"{os.path.splitext(gif)[0]}-zip.gif"

    percent = 0.9
    while size >= max_size:
        gifsicle(
            gif,
            destination=destination,
            optimize=True,
            options=["--lossy=80", "--scale", str(percent)],
        )
        if not is_cover:
            gif = destination
        size = os.path.getsize(gif) / 1024
        percent -= 0.05

    return _read_file_to_bytes(gif)


def _zip_image_bytes(img_bytes: bytes, max_size=IMAGE_MAX_SIZE_KB, file_type=None):
    """zip image bytes and return bytes; default changed to .jpeg"""
    file_type = file_type or filetype.guess(img_bytes).extension

    with io.BytesIO(img_bytes) as io_image:
        size = len(io_image.getvalue()) // 1024
        if size < max_size:
            return img_bytes
        while size >= max_size:
            img = Image.open(io_image)
            x_size, y_size = img.size
            out = img.resize((int(x_size * 0.95), int(y_size * 0.95)), Image.ANTIALIAS)
            io_image.close()
            io_image = io.BytesIO()
            try:
                out.save(io_image, "jpeg")
            except:
                out.save(io_image, file_type)
            size = len(io_image.getvalue()) // 1024
        return io_image.getvalue()


def zip_image(path_bytes_string, max_size: int = IMAGE_MAX_SIZE_KB):
    """zip image"""
    file_bytes, is_file = get_filebytes(path_bytes_string)
    file_type = filetype.guess(file_bytes).extension
    try:
        if file_type == "gif" and is_file:
            img_bytes = _zip_gif(path_bytes_string, max_size=max_size, is_cover=False)
        else:
            img_bytes = _zip_image_bytes(file_bytes, max_size=max_size, file_type=file_type)
    except Exception as err:
        logger.warning("zip_image %s", err)
        img_bytes = file_bytes
    return img_bytes


def _pack_img_content(img: Union[Dict, str, bytes], max_size: int = IMAGE_MAX_SIZE_KB):
    """pack image content"""
    name = None
    if isinstance(img, bytes):
        content = img
    elif isinstance(img, str):
        if os.path.exists(img):
            content = _read_file_to_bytes(img)
            name = os.path.basename(img).encode().decode("utf-8")
        else:
            content = base64.b64decode(img)
    elif isinstance(img, dict):
        if "content" not in img:
            raise ValueError("img dict must have content key")
        content = base64.b64decode(img["content"])
        name = img.get("name")

    file_type = filetype.guess(content).extension

    if name is None:
        _uid = f"{uuid.uuid4()}-{datetime.date.today()}"
        name = ".".join([_uid, file_type])
    name = re.sub(r"([ :])", r"_", name)

    if file_type == "gif":
        content = _zip_gif(img, max_size=max_size, is_cover=False)
    else:
        content = _zip_image_bytes(content, max_size=max_size, file_type=file_type)

    return {
        "name": name,
        "content": content,
        "mediaType": filetype.guess(content).mime,
    }


def pack_images(images: List):
    """pack images"""
    max_size = int(IMAGE_MAX_SIZE_KB // min(len(images), IMAGE_MAX_NUM))
    return [_pack_img_content(img, max_size=max_size) for img in images]


def pack_profile_image(image):
    """pack the image for profile"""
    file_bytes = zip_image(image, 200)
    return {"content": file_bytes, "mediaType": filetype.guess(file_bytes).mime}
