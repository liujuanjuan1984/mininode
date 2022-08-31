import base64
import logging
from dataclasses import dataclass
from typing import Dict

import filetype

from mininode import utils

logger = logging.getLogger(__name__)

# 将一张或多张图片处理成 RUM 支持的图片对象列表, 要求总大小小于 200kb，此为链端限定
IMAGE_MAX_SIZE_KB = 200  # 200 kb 每条trx中所包含的图片总大小限制为 200
# 单条 trx 最多4 张图片；此为 rum app 客户端限定：第三方 app 调整该限定
IMAGE_MAX_NUM = 4
CHUNK_SIZE = 150 * 1024  # 150 kb，文件切割为多条trxs时，每条trx所包含的文件字节流上限


@dataclass
class ImgContent:
    name: str = None
    mediaType: str = None
    content: str = None

    def __init__(self, path_bytes_string, kb=None):

        if type(path_bytes_string) == dict:
            d = path_bytes_string
            self.content = base64.b64decode(d.get("content"))
            if not self.content:
                err = f"ImgContent  type: {type(path_bytes_string)} ,content got null "
                raise ValueError(err)
            _bytes, _ = utils.get_filebytes(self.content)
            self.name = d.get("name", utils.filename_init(_bytes))
            self.mediaType = d.get("mediaType", filetype.guess(_bytes).mime)

        else:
            kb = kb or IMAGE_MAX_SIZE_KB
            self.name = utils.filename_init(path_bytes_string)
            file_bytes = utils.zip_image(path_bytes_string, kb)
            self.mediaType = filetype.guess(file_bytes).mime
            self.content = file_bytes
