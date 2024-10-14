from typing import List, Optional

from fastapi import APIRouter, HTTPException, Response, Request
from pydantic import BaseModel

import models.model as model_model
from infra.logger import logger
from middleware.auth import get_user_info
from routes.file import _download_file

router = APIRouter(
    prefix="/models",
)


@router.get("", response_model=List[model_model.Model])
async def get_models(model_id: Optional[int] = None, model_name: Optional[str] = None):
    res = await model_model.query_model(name=model_name, model_id=model_id)
    return res


class CreateModelReqBody(BaseModel):
    name: str
    audio_model: str
    video_model: str


@router.post("", response_model=model_model.Model)
async def create_model(body: CreateModelReqBody):
    return await model_model.create_model(
        name=body.name, audio_model=body.audio_model, video_model=body.video_model
    )


class UpdateModelReqBody(BaseModel):
    name: str
    audio_model: str
    video_model: str


@router.put("/{model_id}", response_model=model_model.Model)
async def update_model(model_id: int, body: UpdateModelReqBody):
    return await model_model.update_model(
        model_id,
        name=body.name,
        audio_model=body.audio_model,
        video_model=body.video_model,
    )


@router.delete("/{model_id}", response_model=int)
async def delete_model(model_id: int):
    return await model_model.delete_model(model_id)


class ImageResponse(Response):
    media_type = "image/*"
    schema = {}


@router.get("/preview_image", response_class=ImageResponse)
async def get_preview_image(req: Request, model_id: Optional[int] = None, model_name: Optional[str] = None):
    user = get_user_info(req)
    user_id = user["user_id"]

    res = await model_model.query_model(name=model_name, model_id=model_id)
    model = res[0]
    if model is None:
        raise HTTPException(status_code=404, detail="Model not found")

    logger.debug(model.video_config)

    if "preview_image_id" not in model.video_config:
        raise HTTPException(status_code=404, detail="preview_image_id not found")

    return await _download_file(file_id=model.video_config["preview_image_id"], user_id=user_id)
