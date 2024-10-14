from fastapi import APIRouter
from pydantic import BaseModel

import models.task as task_model
from infra.logger import logger

router = APIRouter(
    prefix="/internal",
)


class Body(BaseModel):
    status: int  # 1 WAIT 2 PENDING 3 SUCCESS 4 ERROR

    class Config:
        extra = "allow"


@router.put("/task/{task_id}", include_in_schema=False)
async def get_tasks(task_id: int, task: Body):
    logger.debug(f"task_id: {task_id}, task: {task}")

    m = {
        2: task_model.TaskStatus.PENDING,
        3: task_model.TaskStatus.SUCCEEDED,
        4: task_model.TaskStatus.FAILED,
    }
    if m[task.status] is None:
        return {"error": f"Unknown status: {task.status}"}
    return await task_model.update_task(task_id, status=m[task.status])
