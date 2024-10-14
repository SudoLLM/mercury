import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from infra.db import database, metadata, engine
from middleware.auth import AuthMiddleware
from middleware.exception import ExceptionMiddleware
from routes.file import router as file_router
from routes.infer import router as infer_router
from routes.model import router as model_router
from routes.task import router as task_router
from routes.user import router as user_router

os.environ["PROJECT_ROOT"] = os.path.dirname(os.path.abspath(__file__))


@asynccontextmanager
async def lifespan(_: FastAPI):
    await database.connect()  # establish connection
    metadata.create_all(engine)  # init tables

    yield
    await database.disconnect()


app = FastAPI(lifespan=lifespan)

app.add_middleware(AuthMiddleware)
app.add_middleware(ExceptionMiddleware)

app.include_router(task_router)
app.include_router(infer_router)
app.include_router(file_router)
app.include_router(user_router)
app.include_router(model_router)
