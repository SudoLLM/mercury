import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from infra.db import database, metadata, engine
from middleware.auth import AuthMiddleware
from middleware.exception import ExceptionMiddleware
from routes.file import router as file_router
from routes.infer import infer_text2audio_queue, infer_audio2video_queue, infer_text2video_queue
from routes.infer import router as infer_router
from routes.internal import router as internal_router
from routes.model import router as model_router
from routes.task import router as task_router
from routes.train import router as train_router
from routes.train import train_audio_queue, train_video_queue
from routes.user import router as user_router

os.environ["PROJECT_ROOT"] = os.path.dirname(os.path.abspath(__file__))


@asynccontextmanager
async def lifespan(_: FastAPI):
    await database.connect()  # establish connection
    metadata.create_all(engine)  # init tables

    infer_text2audio_queue.schedule_task_processing()
    infer_audio2video_queue.schedule_task_processing()
    infer_text2video_queue.schedule_task_processing()
    train_audio_queue.schedule_task_processing()
    train_video_queue.schedule_task_processing()

    yield
    await database.disconnect()


app = FastAPI(lifespan=lifespan)

app.add_middleware(AuthMiddleware)
app.add_middleware(ExceptionMiddleware)

app.include_router(task_router)
app.include_router(infer_router)
app.include_router(file_router)
app.include_router(user_router)
app.include_router(internal_router)
app.include_router(model_router)
app.include_router(train_router)
