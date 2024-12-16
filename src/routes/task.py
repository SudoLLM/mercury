from typing import Dict

from celery.result import AsyncResult
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from middleware.auth import get_user_info
from models.task import query_task, TaskStatus

router = APIRouter(
    prefix="/tasks",
)


class TaskResponse(BaseModel):
    id: int
    res: Dict[str, int]
    status: TaskStatus
    res_status: Dict[str, str]


res_keys = ["output_audio_file", "output_srt_file", "output_video_file"]


@router.get("", response_model=TaskResponse)
async def get_task(task_id: int, req: Request):
    user = get_user_info(req)
    user_id = user["user_id"]

    task = await query_task(task_id=task_id, user_id=user_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"task {task_id} not found")

    status = TaskStatus.SUCCEEDED
    res, res_status = {}, {}
    for rid in task.celery_ids:
        r = AsyncResult(rid)
        # set status
        if status == TaskStatus.SUCCEEDED:
            if r.state == "FAILURE":
                status = TaskStatus.FAILED
            elif r.state == "PENDING":
                status = TaskStatus.PENDING
            elif r.state != "SUCCESS":
                status = TaskStatus.UNKNOWN
        # set res_status
        res_status[rid] = r.state
        
    # set res
    for id_k in ["output_audio_file_id", "output_srt_file_id", "output_video_file_id"]:
        if id_k in task.res:
            res[id_k] = task.res[id_k]

    return TaskResponse(id=task.id, res=res, status=status, res_status=res_status)
