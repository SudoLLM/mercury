import os

import azure.cognitiveservices.speech as speechsdk
from mcelery.cos import get_local_path, upload_cos_file
from mcelery.infer import celery_app, register_infer_tasks

azure_speech_key = os.getenv("AZURE_SPEECH_KEY")
azure_speech_region = os.getenv("AZURE_SPEECH_REGION")


@celery_app.task(
    lazy=False, name="azure_infer", queue="azure_infer", autoretry_for=(Exception,), default_retry_delay=10
)
def azure_infer_task(text: str, audio_profile: str, output_cos: str) -> str:
    """
    微软 TTS 服务
    :param text: 音频文字内容
    :param audio_profile: 配置
    :param output_cos: 合成的音频文件 COS key
    :return: output_cos
    """

    dest = get_local_path(output_cos)

    speech_config = speechsdk.SpeechConfig(subscription=azure_speech_key, region=azure_speech_region)
    # remove all (xxx), example: "zh-CN-XiaoxiaoNeural (Female)" to be "zh-CN-XiaoxiaoNeural"
    speech_config.speech_synthesis_voice_name = audio_profile.split(" (")[0]
    audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True, filename=str(dest))

    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    speech_synthesis_result = speech_synthesizer.speak_text_async(text).get()
    if speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_synthesis_result.cancellation_details
        print("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            raise Exception(f"error details: {cancellation_details.error_details}")

    if speech_synthesis_result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        upload_cos_file(output_cos)
        return output_cos
    elif speech_synthesis_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_synthesis_result.cancellation_details
        print("Speech synthesis canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            raise Exception(cancellation_details.error_details)
    else:
        raise Exception(f"unknown reason: {speech_synthesis_result.reason}")


# 需要注册其他 task, 否则 chain 之后的任务会发送到错误的 queue
register_infer_tasks()
