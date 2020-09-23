#!/usr/bin/env python3

import asyncio
import os.path
import urllib.parse
# from collections import namedtuple
from typing import Any, AnyStr, List, NamedTuple, Optional, Text, Tuple

import aiohttp  # type: ignore

from .aio import async_write_bin


class FWRes(NamedTuple):
    url: Text
    filepath: Optional[Text]
    http_status: int
    write_success: bool


def _get_filepath_from_url(url: Text, dirpath: Text) -> Text:
    """Returns filepath from base file name in URL and directory path."""
    url_path_list = urllib.parse.urlsplit(url)
    abs_filepath = url_path_list.path
    basepath = os.path.split(abs_filepath)[-1]
    return os.path.join(dirpath, basepath)


async def async_fetch(session: Any, url: AnyStr) -> Tuple[AnyStr, Any, Any]:
    """Asynchronous I/O HTTP GET request with a ClientSession instantiated
    from the aiohttp library."""
    async with session.get(url) as response:
        status = response.status
        if status != 200:
            binary = None
        else:
            binary = await response.read()
        return url, status, binary


async def async_fetch_and_write(session: Any, url: Text, dirpath: Text) -> FWRes:
    """Asynchronous I/O HTTP GET request with a ClientSession instantiated
    from the aiohttp library, followed by an asynchronous I/O file write of
    the binary to disk with the aiofiles library.

    :returns `FWRes` namedtuple with url, filepath, http_status, write_success fields"""
    url, status, binary = await async_fetch(session, url)
    if status != 200:
        filepath = None
        write_success = False
    else:
        filepath = _get_filepath_from_url(url, dirpath)
        await async_write_bin(filepath, binary)
        write_success = True

    return FWRes(
        url=url, filepath=filepath, http_status=status, write_success=write_success
    )


async def create_async_get_request_session_and_run(
    urls: List[Text], dirpath: Text
) -> List[Any]:
    """Creates an aiohttp library ClientSession and performs asynchronous GET requests +
    binary file writes with the binary response from the GET request.

    :returns list of asyncio Tasks that include `FWRes` namedtuple instances
    (defined in async_fetch_and_write)"""
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in urls:
            # use asyncio.ensure_future instead of .run() here to maintain
            # Py3.6 compatibility
            task = asyncio.ensure_future(async_fetch_and_write(session, url, dirpath))
            tasks.append(task)
        await asyncio.gather(*tasks, return_exceptions=True)
        return tasks
