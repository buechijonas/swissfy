import json
import subprocess
import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path

from django.core.files.base import ContentFile
from PIL import Image

from . import images

MAX_UPLOAD_SIZE = 250 * 1024 * 1024
MAX_DURATION = 60
MAX_SIDE = 1280
CRF = 28
AUDIO_BITRATE = "96k"
TRANSCODE_TIMEOUT = 600


class InvalidVideo(Exception):
    pass


@contextmanager
def local_path(upload):
    if hasattr(upload, "temporary_file_path"):
        yield upload.temporary_file_path()
        return
    with tempfile.NamedTemporaryFile() as file:
        for chunk in upload.chunks():
            file.write(chunk)
        file.flush()
        yield file.name


def probe(path):
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-select_streams",
                "v:0",
                "-show_entries",
                "stream=codec_type:format=duration",
                "-of",
                "json",
                path,
            ],
            capture_output=True,
            check=True,
            timeout=30,
        )
        info = json.loads(result.stdout)
        return info["streams"], float(info["format"]["duration"])
    except (subprocess.SubprocessError, ValueError, KeyError):
        raise InvalidVideo("Die Datei ist kein gültiges Video.")


def validate(upload):
    if upload.size > MAX_UPLOAD_SIZE:
        raise InvalidVideo("Das Video ist zu gross (max. 250 MB).")
    with local_path(upload) as path:
        streams, duration = probe(path)
    if not streams:
        raise InvalidVideo("Die Datei ist kein gültiges Video.")
    if duration > MAX_DURATION + 0.5:
        raise InvalidVideo(f"Das Video ist zu lang (max. {MAX_DURATION} Sekunden).")
    upload.name = uuid.uuid4().hex
    return upload


def transcode(source):
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / "video.mp4"
        frame = Path(directory) / "frame.png"
        scale = (
            f"scale=w='min({MAX_SIDE},iw)':h='min({MAX_SIDE},ih)'"
            ":force_original_aspect_ratio=decrease:force_divisible_by=2"
        )
        ffmpeg = ["ffmpeg", "-v", "error", "-y"]
        commands = [
            [
                *ffmpeg,
                *("-i", source, "-t", str(MAX_DURATION), "-vf", scale),
                *("-c:v", "libx264", "-preset", "veryfast", "-crf", str(CRF)),
                *("-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", AUDIO_BITRATE, "-ac", "2"),
                *("-movflags", "+faststart", str(output)),
            ],
            [*ffmpeg, "-i", str(output), "-frames:v", "1", str(frame)],
        ]
        try:
            for command in commands:
                subprocess.run(command, capture_output=True, check=True, timeout=TRANSCODE_TIMEOUT)
            with Image.open(frame) as image:
                poster = image.convert("RGB")
        except (subprocess.SubprocessError, OSError) as error:
            raise InvalidVideo(str(error))

        video = ContentFile(output.read_bytes(), name=f"{uuid.uuid4().hex}.mp4")
        return video, images.thumbnail(poster), *poster.size
