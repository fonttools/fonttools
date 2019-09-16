import os.path
import urllib.parse

import aiohttp
import asyncio
import aiofiles


def _get_filepath_from_url(url, dirpath):
    url_path_list = urllib.parse.urlsplit(url)
    abs_filepath = url_path_list.path
    basepath = os.path.split(abs_filepath)[-1]
    return os.path.join(dirpath, basepath)


async def async_write(path, binary):
    async with aiofiles.open(path, "wb") as f:
        await f.write(binary)


async def async_fetch(session, url):
    async with session.get(url) as response:
        status = response.status
        if status != 200:
            binary = None
        else:
            binary = await response.read()
        return url, status, binary


async def async_fetch_and_write(session, url, dirpath):
    url, status, binary = await async_fetch(session, url)
    if status != 200:
        filepath = None
        return url, filepath, False
    else:
        filepath = _get_filepath_from_url(url, dirpath)
        await async_write(filepath, binary)
        return url, filepath, True


async def create_async_get_request_session_and_run(urls, dirpath):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in urls:
            # use asyncio.ensure_future instead of .run() here to maintain
            # Py3.6 compatibility
            task = asyncio.ensure_future(async_fetch_and_write(session, url, dirpath))
            tasks.append(task)
        await asyncio.gather(*tasks, return_exceptions=True)
        return tasks
