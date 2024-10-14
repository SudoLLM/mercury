import os
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Request, Response, UploadFile
from starlette.responses import FileResponse

import models.file as file_model
from infra.file import WORKSPACE, save_file
from middleware.auth import get_user_info

router = APIRouter(
    prefix="/file",
)


@router.post("/upload", response_model=file_model.File)
async def upload_video(
    file: UploadFile,
    model_name: str,
    req: Request,
):
    user = get_user_info(req)
    user_id = user["user_id"]

    raw_dir_path = os.path.join(
        WORKSPACE,
        str(user_id),
        model_name,
        "_raw",
    )

    file_path = os.path.join(raw_dir_path, file.filename)

    await save_file(file, file_path)
    return await file_model.create_file(file_path, user_id)


class DownloadResponse(Response):
    media_type = "application/octet-stream"
    schema = {}


@router.get("/download", response_class=DownloadResponse)
async def download_file(file_id: int, req: Request):
    user = get_user_info(req)
    user_id = user["user_id"]

    res = await file_model.query_file(file_id)
    if not res:
        raise HTTPException(status_code=404, detail="file not found")

    if res.user_id != user_id:
        raise HTTPException(status_code=403, detail="no permission")
    base_name = os.path.basename(res.path)
    encoded_basename = quote(base_name)

    return FileResponse(
        res.path,
        media_type="application/octet-stream",
        filename=encoded_basename,
    )
