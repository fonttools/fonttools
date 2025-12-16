#!/usr/bin/env python3

import os
from typing import AnyStr, Text, Union

import aiofiles  # type: ignore


async def async_write_bin(
    path: Union[AnyStr, "os.PathLike[Text]"], binary: bytes
) -> None:
    """Asynchronous IO writes of binary data `binary` to disk on the file path `path`"""
    async with aiofiles.open(path, "wb") as f:  # type: ignore
        await f.write(binary)
