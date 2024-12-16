import logging
import subprocess
from pathlib import Path

from mcelery.cos import download_cos_file, get_local_path, upload_cos_file
from mcelery.infer import celery_app, register_infer_tasks

from cos_file import get_cos_files

root_dir = Path("/app/talking-head")  # project dir in docker
s2a_dir = root_dir / "s2a"
dnr_dir = root_dir / "dnr"


@celery_app.task(
    lazy=False,
    name="talking_head_infer",
    queue="talking_head_infer",
    autoretry_for=(Exception,),
    default_retry_delay=10,
)
def talking_head_infer_task(
    audio_cos: str,
    speaker: str,
    output_cos: str,
) -> str:
    """
    根据音频生成数字人视频服务
    :param audio_cos: 音频文件
    :param speaker: 使用的数字人
    :param output_cos: 输出的视频文件 COS key
    :return: output_cos
    """
    audio_path = download_cos_file(audio_cos)
    video_path = get_local_path(output_cos)

    # 把推理要用的数据放在对应目录下, 当前 talking_head 目录写的很死
    # s2a_ckpt = "/app/talking-head-v0.2/s2a/exp_runs/xfmr-base/checkpoints/epoch1200.safetensors"
    # s2a_ckpt_cfg = "/app/talking-head-v0.2/s2a/exp_runs/xfmr-base/config.yaml"

    dnr_src_video_clip = [0]
    files = get_cos_files(speaker=speaker, dnr_src_video_clip=dnr_src_video_clip)
    for cos_key, path in files:
        download_cos_file(cos_key, rewriter=lambda _: root_dir / path)

    th_output_dir = Path(f"generated-xfmr") / speaker / audio_path.name

    s2a(th_output_dir, audio_path, speaker)
    dnr(th_output_dir, audio_path, speaker)
    ffmpeg(th_output_dir, audio_path, video_path)

    upload_cos_file(output_cos)
    # cleaning
    # shutil.rmtree(root_dir / f"generated-xfmr/{speaker}")
    return output_cos


register_infer_tasks()


def s2a(th_output_dir: Path, audio_path: Path, speaker: str):
    if not (th_output_dir / "avg/col0.npy").exists():
        logging.info("==================================")
        logging.info("audio to 3d start")
        cmd = ["python", "infer.py", "--input_audio", audio_path, "--speaker", speaker]
        try:
            subprocess.run(cmd, stderr=subprocess.PIPE, check=True, cwd=s2a_dir)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(e.stderr.decode()) from e
        logging.info(f"audio to 3d done")
    else:
        logging.info("s2a npy already exists")


def dnr(th_output_dir: Path, audio_path: Path, speaker: str):
    if not (th_output_dir / "col0-nr-tmp.mp4").exists():
        logging.info("==================================")
        logging.info("render start")
        cmd = ["python", "infer.py", "--input_audio", audio_path, "--speaker", speaker]
        try:
            subprocess.run(cmd, stderr=subprocess.PIPE, check=True, cwd=dnr_dir)
        except subprocess.CalledProcessError as e:
            raise RuntimeError(e.stderr.decode()) from e
        logging.info(f"render done")
    else:
        logging.info("dnr mp4 already exists")


def ffmpeg(th_output_dir: Path, audio_path: Path, video_path: Path):
    cmd = [
        "ffmpeg",
        "-i",
        th_output_dir / "col0-nr-tmp.mp4",
        "-i",
        audio_path,
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-y",
        video_path,
    ]
    try:
        subprocess.run(cmd, stderr=subprocess.PIPE, check=True)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(e.stderr.decode()) from e
