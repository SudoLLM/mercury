from typing import Any, Optional, Dict

import ormar

from infra.db import BaseModel, base_ormar_config


class Model(BaseModel):
    ormar_config = base_ormar_config.copy(tablename="model")

    name: str = ormar.String(max_length=100, unique=True)
    audio_model: Optional[str] = ormar.String(default="", max_length=100, comment="RVC model path")
    audio_config: Dict[str, Any] = ormar.JSON(default={}, comment="pitch")
    video_model: Optional[str] = ormar.String(default="", max_length=100, comment="talking head speaker")
    video_config: Dict[str, Any] = ormar.JSON(default={}, comment="preview_image_id")


def query_model(name: Optional[str] = None, model_id: Optional[int] = None):
    q = Model.objects
    if name is not None:
        q = q.filter(name=name)
    if model_id is not None:
        q = q.filter(id=model_id)
    return q.all()


async def create_model(**kwargs: Any):
    return await Model.objects.create(**kwargs)


async def update_model(model_id: int, **kwargs: Any):
    model = await Model.objects.get(id=model_id)
    model = await model.update(**kwargs)
    return model


def delete_model(model_id: int):
    return Model.objects.delete(id=model_id)
