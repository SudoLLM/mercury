from typing import List, Optional
from fastapi import APIRouter
import models.task as task_model


router = APIRouter(
    prefix="/tasks",
)


@router.get("", response_model=List[task_model.Task])
async def get_tasks(task_id: Optional[int] = None):
    res = await task_model.query_task(task_id)
    return res


@router.post("", response_model=task_model.Task)
async def create_task():
    return await task_model.create_task()


@router.put("/{task_id}", response_model=task_model.Task)
async def update_task(task_id: int, task: task_model.Task):
    return await task_model.update_task(task_id, status=task.status)


@router.delete("/{task_id}", response_model=int)
async def delete_task(task_id: int):
    return await task_model.delete_task(task_id)
