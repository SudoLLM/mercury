import uuid
from typing import Optional

import ormar

from infra.db import BaseModel, base_ormar_config


class File(BaseModel):
    ormar_config = base_ormar_config.copy(tablename="file")

    name: str = ormar.String(max_length=255, nullable=False, comment="raw file name")
    key: str = ormar.String(max_length=255, nullable=True, comment="file key in cos")
    user_id: int = ormar.Integer(foreign_key=True, nullable=False)


def query_file(file_id: Optional[int], user_id=Optional[int]):
    q = File.objects
    if file_id is not None:
        q = q.filter(id=file_id)
    if user_id is not None:
        q = q.filter(user_id=user_id)
    return q.first()


async def create_file(name: str, key: str, user_id: int) -> File:
    return await File.objects.create(name=name, key=key, user_id=user_id)


async def create_infer_file(user_id: int, suffix: str, uid: str = None) -> File:
    name = (uid or uuid.uuid4().hex) + suffix
    key = f"infer/{name}"
    return await File.objects.create(name=name, key=key, user_id=user_id)
