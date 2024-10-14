import uuid

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from infra.logger import logger
from middleware.auth import get_user_info
from models.file import query_file, create_infer_file
from models.model import query_model
from models.task import create_task
from routes.common import CommonSchemaConfig
from task.infer import publish_talking_head_infer_task, publish_text_task, AudioModeType

router = APIRouter(
    prefix="/infer",
)


class InferVideoResponse(BaseModel):
    task_id: int


@router.post("/video", response_model=InferVideoResponse)
async def infer_video(
    model_name: str,
    file_id: int,
    req: Request,
):
    user = get_user_info(req)
    user_id = user["user_id"]

    models = await query_model(name=model_name)
    model = models[0]

    if model is None:
        raise HTTPException(status_code=404, detail=f"model {model_name} not found")

    audio_file = await query_file(file_id=file_id, user_id=user_id)
    if audio_file is None:
        raise HTTPException(status_code=404, detail=f"file {file_id} not found")

    file = await create_infer_file(user_id, ".mp4")
    rst = publish_talking_head_infer_task(str(audio_file.id), model.video_model, file.key)
    task = await create_task(user_id, rst, video_file=file)

    return JSONResponse({"task_id": task.id})


class Text2VideoRequest(BaseModel):
    class Config(CommonSchemaConfig):
        pass

    text: str
    model_name: str
    audio_profile: str = "zh-CN-YunxiNeural (Male)"
    mode: AudioModeType = AudioModeType.RVC
    gen_srt: bool = Field(
        False,
        description="是否同步生成字幕文件，默认不生成。若为True,将在任务详情中返回 res.output_srt_file_id",
    )  # 是否同步生成 字幕文件


class Text2VideoResponse(BaseModel):
    task_id: int


@router.post("/text2video", response_model=Text2VideoResponse)
async def infer_text2video(body: Text2VideoRequest, req: Request):
    user = get_user_info(req)
    logger.debug("user: %s", user)
    user_id = user["user_id"]

    models = await query_model(name=body.model_name)
    if len(models) == 0:
        raise HTTPException(status_code=404, detail=f"model {body.model_name} not found")
    model = models[0]
    if model is None:
        raise HTTPException(status_code=404, detail=f"model {body.model_name} not found")

    uid = uuid.uuid4().hex
    audio_file = await create_infer_file(user_id, ".wav", uid)
    video_file = await create_infer_file(user_id, ".mp4", uid)
    if body.mode == AudioModeType.RVC:
        azure_audio_file = await create_infer_file(user_id, ".azure.wav", uid)
    else:
        azure_audio_file = None
    if body.gen_srt:
        srt_file = await create_infer_file(user_id, ".srt", uid)
    else:
        srt_file = None

    rst = publish_text_task(
        text=body.text,
        model_name=body.model_name,
        output_audio_cos=audio_file.key,
        azure_audio_profile=body.audio_profile,
        azure_output_audio_cos=azure_audio_file.key if azure_audio_file else None,
        pitch=model.audio_config.get("pitch", 0),
        speaker=model.video_model,
        output_video_cos=video_file.key,
        output_srt_cos=srt_file.key if srt_file else None,
    )
    task = await create_task(user_id, rst, audio_file=audio_file, video_file=video_file, srt_file=srt_file)
    return JSONResponse({"task_id": task.id})


class Text2AudioRequest(BaseModel):
    class Config(CommonSchemaConfig):
        pass

    text: str
    model_name: str
    audio_profile: str = "zh-CN-YunxiNeural (Male)"
    mode: AudioModeType = AudioModeType.RVC  # 1 for azure, 2 for gpt
    gen_srt: bool = Field(
        False,
        description="是否同步生成字幕文件，默认不生成。若为True,将在任务详情中返回 res.output_srt_file_id",
    )  # 是否同步生成 字幕文件


class Text2AudioResponse(BaseModel):
    task_id: int


@router.post("/text2audio", response_model=Text2AudioResponse)
async def infer_text2audio(body: Text2AudioRequest, req: Request):
    user = get_user_info(req)
    logger.debug("user: %s", user)
    user_id = user["user_id"]

    models = await query_model(name=body.model_name)
    model = models[0]
    if model is None:
        raise HTTPException(status_code=404, detail=f"model {body.model_name} not found")

    uid = uuid.uuid4().hex
    audio_file = await create_infer_file(user_id, ".wav", uid)
    if body.mode == AudioModeType.RVC:
        azure_audio_file = await create_infer_file(user_id, ".azure.wav", uid)
    else:
        azure_audio_file = None
    if body.gen_srt:
        srt_file = await create_infer_file(user_id, ".srt", uid)
    else:
        srt_file = None
    rst = publish_text_task(
        text=body.text,
        model_name=body.model_name,
        output_audio_cos=audio_file.key,
        azure_audio_profile=body.audio_profile,
        azure_output_audio_cos=azure_audio_file.key if azure_audio_file else None,
        pitch=model.audio_config.get("pitch", 0),
        speaker=None,
        output_video_cos=None,
        output_srt_cos=srt_file.key if srt_file else None,
    )
    task = await create_task(user_id, rst, audio_file=audio_file, srt_file=srt_file)
    return JSONResponse({"task_id": task.id})
