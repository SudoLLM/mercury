import asyncio
import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from infra.rqueue import RQueue
from pydantic import BaseModel
import requests
from middleware.auth import getUserInfo
from infra.logger import logger
from models.file import query_file
from models.task import Task, TaskStatus, create_task, update_task
from models.model import create_model, query_model, Model, update_model
from routes.common import CommonSchemaConfig
from utils.file import createDir

TRAIN_AUDIO_KEY = "TRAIN_AUDIO"
TRAIN_VIDEO_KEY = "TRAIN_VIDEO"

class TrainAudioTask():
    def __init__(self, task_id: int, model_name: str, ref_dir_name: str, epoch: int):
        self.task_id = task_id
        self.model_name = model_name
        self.ref_dir_name = ref_dir_name
        self.epoch = epoch

async def train_audio_task_handler(task: TrainAudioTask, retry_count: int):
    try:
        logger.debug(f"starting training audio request: task: {task}")
        models = await query_model(name=task.model_name)
        model = None
        if len(models) == 0:
            model = await create_model(name=task.model_name)
        else:
            model = models[0]
        # cosy voice
        await slice_for_cosy_voice(task.model_name, task.task_id,task.ref_dir_name)
        await train_rvc(task.model_name, task.task_id, task.epoch, task.ref_dir_name)
        await update_model(model.id, audio_model=task.model_name + ".pth")
        await update_task(task.task_id, status=TaskStatus.SUCCEEDED)
    except Exception as e:
        logger.error(f"training audio failed, task: {task} error: {e}")
        if retry_count < 3:
            return False
        else:
            await update_task(task.task_id, status=TaskStatus.FAILED)
    return True
    
class TrainVideoTask():
    def __init__(self, task_id: int, speaker: str):
        self.task_id = task_id
        self.speaker = speaker

async def train_video_task_handler(task: TrainVideoTask, retry_count: int = 0):
    try:
        # talking-head是否存在正在进行的任务
        logger.debug(f"starting training video request, task: {task}")
        response = requests.get("http://0.0.0.0:8000/talking-head/train-ready")
        if not response.ok:
            raise Exception("talking-head response error, code: {response.status_code}")
        if not response.json().get("ready", False):
            raise Exception("talking-head is not ready")
    
        # taking-head start train
        response = requests.post(
            "http://0.0.0.0:8000/talking-head/train",
            json={
                "speaker": task.speaker,
                "callback_url": f"http://0.0.0.0:3333/internal/task/{task.id}",
                "callback_method": "put",
            },
            headers={"Content-Type": "application/json"},
        )
        if not response.ok:
            raise Exception("talking-head response error, code: {response.status_code}")
        
        await update_task(task.task_id, status=TaskStatus.SUCCEEDED)
    except Exception as e:
        logger.error(f"training video failed, task: {task} error: {e}")
        if retry_count < 3:
            return False
        else:
            await update_task(task.task_id, status=TaskStatus.FAILED)

    return True

train_audio_queue = RQueue(TRAIN_AUDIO_KEY, train_audio_task_handler, 60 * 2, 60)
train_video_queue = RQueue(TRAIN_VIDEO_KEY, train_video_task_handler, 60 * 20, 60 * 5)


router = APIRouter(
    prefix="/train",
    include_in_schema=False,
)


def gen_output_dir(model: str, user_id: int, task_id: int):
    output_dir_path = os.path.join(
        "/data",
        "prod",
        str(user_id),
        model,
        "generated",
        str(task_id),
    )
    createDir(output_dir_path)
    return output_dir_path


class TrainAudioRequestBody(BaseModel):
    class Config(CommonSchemaConfig):
        pass

    model_name: str
    epoch: Optional[int] = 200
    file_ids: List[int]

# 切分音频作为 cosyvoice 参考音频
async def slice_for_cosy_voice(model_name: str, task_id: int, ref_dir_name: str):
    output_dir_name = os.path.join(
        "/home/ubuntu/Projects/CosyVoice/mercury_workspace",
        model_name,
    )
    createDir(output_dir_name)
    
    response = requests.post(
        "http://0.0.0.0:3336/audio/slice_audio",
        json={
            "audio_file": ref_dir_name,
            "output_dir": output_dir_name,
            "min_length": 8,
            "max_length": 12,
            "keep_silent": 0.5,
            "sliding_slice": False
        },
        headers={"Content-Type": "application/json"},
    )
    
    if not response.ok:
        raise Exception("slice audio failed, code: {response.status_code}")
    
# 训练rvc模型
async def train_rvc(model_name: str, task_id: int, model_id: int, ref_dir_name: str, epoch: int):
    response = requests.post(
        "http://127.0.0.1:3334/train?name="
        + model_name
        + "&ref_dir_name="
        + ref_dir_name
        + "&epoch="
        + str(epoch)
    )

    if not response.ok:
        raise Exception("response error, code: {response.status_code}")

@router.post("/audio_model")
async def train_audio_model(
    req: Request,
    body: TrainAudioRequestBody,
):
    user = getUserInfo(req)
    task = await create_task()

    ref_dir_name = os.path.join(
        "/home/ubuntu/Projects/Retrieval-based-Voice-Conversion-WebUI/reference",
        body.model_name,
    )

    # delete ref_dir_name
    shutil.rmtree(ref_dir_name, ignore_errors=True)

    createDir(ref_dir_name)

    for file_id in body.file_ids:
        file = await query_file(file_id)
        file_name = os.path.basename(file.path)
        new_file_path = os.path.join(ref_dir_name, file_name)
        shutil.copy(file.path, new_file_path)
        
    train_audio_queue.append(TrainAudioTask(task.id, body.model_name, ref_dir_name, body.epoch))

    return JSONResponse(
        {
            "task_id": task.id,
        }
    )

class TrainVideoRequestBody(BaseModel):
    class Config(CommonSchemaConfig):
        pass

    model_name: str
    speaker: str
    file_ids: List[int]

@router.post("/video_model")
async def train_video_model(
    req: Request,
    body: TrainVideoRequestBody,
):
    user = getUserInfo(req)

    models = await query_model(name=body.model_name)

    task = await create_task()
    model = None
    if len(models) == 0:
        model = await create_model(name=body.model_name)
    else:
        model = models[0]

    await update_model(model.id, video_model=body.speaker)

    ref_dir_name = os.path.join(
        "/home/chaiyujin/talking-head-v0.1/user-data/clip",
        body.speaker,
    )

    # delete ref_dir_name
    shutil.rmtree(ref_dir_name, ignore_errors=True)

    createDir(ref_dir_name)

    count = 0

    for file_id in body.file_ids:
        file = await query_file(file_id)
        file_name = str(count).zfill(2) + ".mp4"
        new_file_path = os.path.join(ref_dir_name, file_name)
        shutil.copy(file.path, new_file_path)
        count = count + 1

    # query request
    train_video_queue.append(TrainVideoTask(task.id, body.speaker))

    return JSONResponse(
        {
            "task_id": task.id,
        }
    )
