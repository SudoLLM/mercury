import os
import shutil

from fastapi import UploadFile

from utils.file import create_dir

WORKSPACE = "/data/prod"


async def save_file(upload_file: UploadFile, file_path: str):
    file_dir = os.path.dirname(file_path)

    create_dir(file_dir)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)


def get_file_absolute_path(file_path: str):
    return os.path.join(WORKSPACE, file_path)
