#!/usr/bin/env python3

import aiofiles


async def async_write_bin(path, binary):
    """Asynchronous IO writes of binary data `binary` to disk on the file path `path`"""
    async with aiofiles.open(path, "wb") as f:
        await f.write(binary)
