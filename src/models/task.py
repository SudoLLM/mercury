from enum import Enum
from typing import List, Optional, Dict, Any

import ormar
from celery.result import ResultBase, AsyncResult, GroupResult

from infra.db import BaseModel, base_ormar_config
from models.file import File


class TaskStatus(int, Enum):
    UNKNOWN = 0
    PENDING = 1
    SUCCEEDED = 2
    FAILED = 3


class Task(BaseModel):
    """
    在这里存储 all celery result ids in task.
    顺带还能兼容之前的 api.
    """

    ormar_config = base_ormar_config.copy(tablename="task")

    user_id: int = ormar.Integer(foreign_key=True, nullable=False)
    res: Dict[str, Any] = ormar.JSON(default={}, comment="all output files")
    celery_ids: List[str] = ormar.JSON(default={}, comment="all celery result ids in task")


def query_task(task_id: Optional[int], user_id=Optional[int]):
    q = Task.objects
    if task_id is not None:
        q = q.filter(id=task_id)
    if user_id is not None:
        q = q.filter(user_id=user_id)
    return q.first()


async def create_task(
    user_id: int, rst: ResultBase, audio_file: File = None, srt_file: File = None, video_file: File = None
) -> Task:
    res = {}
    if audio_file:
        res["output_audio_file_id"] = audio_file.id
        res["output_audio_file_key"] = audio_file.key
    if srt_file:
        res["output_srt_file_id"] = srt_file.id
        res["output_srt_file_key"] = srt_file.key
    if video_file:
        res["output_video_file_id"] = video_file.id
        res["output_video_file_key"] = video_file.key
    return await Task.objects.create(user_id=user_id, res=res, celery_ids=all_res_ids(rst))


def all_res_ids(rst: ResultBase) -> List[str]:
    """
    从最终的 rst 中获取所有中间 task rst
    """
    ids = []
    if rst.parent:
        ids.extend(all_res_ids(rst.parent))
    if isinstance(rst, AsyncResult):
        ids.append(rst.id)
    elif isinstance(rst, GroupResult):
        for r in rst.results:
            ids.extend(all_res_ids(r))
    return ids
