import os

from datetime import datetime, timezone


def get_file_modtime(path):
    """Returns ISO formatted file modification time in local system timezone"""
    return (
        datetime.fromtimestamp(os.stat(path).st_mtime, timezone.utc)
        .astimezone()
        .isoformat()
    )


def file_exists(path):
    """Validates file path as existing local file"""
    return os.path.isfile(path)
