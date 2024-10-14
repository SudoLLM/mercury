import os
import shutil
import uuid
from mimetypes import guess_type

from fastapi import APIRouter, HTTPException, Request, Response, UploadFile
from mcelery.cos import get_local_path, upload_cos_file, download_cos_file, cos_client, cos_bucket
from starlette.responses import RedirectResponse, FileResponse

from middleware.auth import get_user_info
from models.file import File, create_file


async def _download_file(file_id: int, user_id: int, media_type: str = None) -> Response:
    file = await File.objects.filter(id=file_id, user_id=user_id).first()
    if file is None:
        raise HTTPException(status_code=404, detail="file not found")

    if media_type is None:
        media_type = guess_type(file.name)[0] or "application/octet-stream"

    if os.getenv("DOWNLOAD_REDIRECT"):
        return RedirectResponse(
            url=cos_client.get_presigned_url(
                Bucket=cos_bucket,
                Key=file.key,
                Method="GET",
                Expired=300,
                Params={
                    "response-content-type": media_type,
                    "response-content-disposition": f"attachment; filename={file.name}",
                },
            )
        )

    return FileResponse(
        path=download_cos_file(file.key),
        media_type=media_type,
        filename=file.name,
    )


router = APIRouter(
    prefix="/file",
)


@router.post("/upload", response_model=File)
async def upload_video(
    file: UploadFile,
    req: Request,
):
    user = get_user_info(req)
    user_id = user["user_id"]

    key = f"upload/{uuid.uuid4().hex}"
    # write to local
    with get_local_path(key).open("wb") as writer:
        shutil.copyfileobj(file.file, writer)
    # create and upload
    file_model = await create_file(name=file.filename, key=key, user_id=user_id)
    upload_cos_file(key)
    return file_model


class DownloadResponse(Response):
    media_type = "application/octet-stream"
    schema = {}


@router.get("/download", response_class=DownloadResponse)
async def download_file(file_id: int, req: Request):
    user = get_user_info(req)
    user_id = user["user_id"]
    return await _download_file(file_id=file_id, user_id=user_id, media_type="application/octet-stream")
