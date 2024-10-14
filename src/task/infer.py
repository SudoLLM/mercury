from enum import Enum
from typing import Tuple, Optional

from celery import group
from celery.result import AsyncResult, GroupResult
from mcelery.infer import register_infer_tasks

from infra.logger import logger


class AudioModeType(int, Enum):
    RVC = 1
    COSYVOICE = 2


def cosy_cos_helper(model_name: str) -> Tuple[str, str]:
    """
    根据模型名称找到 cosy 对应的参考文本 & 参考视频 COS key
    :param model_name: 模型名
    :return: 参考文本, 参考视频 COS key
    """
    return f"model/cosy/{model_name}.lab", f"model/cosy/{model_name}.wav"


def rvc_cos_helper(model_name: str) -> Tuple[str, str]:
    """
    根据 rvc 模型名称找到对应的 index & model weight COS key
    :param model_name: 模型名
    :return: index, model weight COS key
    """
    return f"model/rvc/{model_name}.index", f"model/rvc/{model_name}.pth"


cosy_infer_task, azure_infer_task, rvc_infer_task, srt_infer_task, talking_head_infer_task = register_infer_tasks()


def publish_cosy_infer_task(text: str, model_name: str, output_cos: str, mode: int = 1) -> AsyncResult:
    prompt_text_cos, prompt_wav_cos = cosy_cos_helper(model_name)
    return cosy_infer_task.delay(text, prompt_text_cos, prompt_wav_cos, output_cos, mode)


def publish_azure_infer_task(text: str, audio_profile: str, output_cos: str) -> AsyncResult:
    return azure_infer_task.delay(text, audio_profile, output_cos)


def publish_rvc_infer_task(audio_cos: str, model_name: str, pitch: int, output_cos: str) -> AsyncResult:
    index_cos, model_cos = rvc_cos_helper(model_name)
    return rvc_infer_task.delay(audio_cos, index_cos, model_cos, pitch, output_cos)


def publish_srt_infer_task(audio_cos: str, text: str, output_cos: str) -> AsyncResult:
    return srt_infer_task.delay(audio_cos, text, output_cos)


def publish_talking_head_infer_task(audio_cos: str, speaker: str, output_cos: str) -> AsyncResult:
    return talking_head_infer_task.delay(audio_cos, speaker, output_cos)


def publish_text_task(
    text: str,
    model_name: str,
    output_audio_cos: str,
    azure_audio_profile: str,
    azure_output_audio_cos: Optional[str],
    pitch: int,
    speaker: Optional[str],
    output_video_cos: Optional[str],
    output_srt_cos: Optional[str],
) -> GroupResult | AsyncResult:
    if azure_output_audio_cos:
        azure = azure_infer_task.s(text, azure_audio_profile, azure_output_audio_cos)
        index_cos, model_cos = rvc_cos_helper(model_name)
        rvc = rvc_infer_task.s(index_cos, model_cos, pitch, output_audio_cos)
        tts = azure | rvc
    else:
        prompt_text_cos, prompt_wav_cos = cosy_cos_helper(model_name)
        tts = cosy_infer_task.s(text, prompt_text_cos, prompt_wav_cos, output_audio_cos, mode=1)
    if output_video_cos and output_srt_cos:
        assert speaker is not None
        talking_head = talking_head_infer_task.s(speaker, output_video_cos)
        srt = srt_infer_task.s(text, output_srt_cos)
        task = tts | group(talking_head, srt)
    elif output_video_cos:
        assert speaker is not None
        talking_head = talking_head_infer_task.s(speaker, output_video_cos)
        task = tts | talking_head
    elif output_srt_cos:
        srt = srt_infer_task.s(text, output_srt_cos)
        task = tts | srt
    else:
        task = tts

    rst = task.delay()
    logger.info(f"task id: {rst.id}, task: {task}")
    return rst
