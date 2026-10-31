import io
import uuid

from django.core.files.base import ContentFile
from PIL import Image, ImageOps

MAX_UPLOAD_SIZE = 15 * 1024 * 1024
MAX_IMAGES = 10
MAX_SIDE = 1280
THUMBNAIL_SIDE = 400
QUALITY = 80
FORMATS = ["JPEG", "PNG", "WEBP", "GIF", "AVIF"]


class InvalidImage(Exception):
    pass


def webp(image):
    buffer = io.BytesIO()
    image.save(buffer, format="WEBP", quality=QUALITY)
    return ContentFile(buffer.getvalue(), name=f"{uuid.uuid4().hex}.webp")


def load(upload):
    if upload.size > MAX_UPLOAD_SIZE:
        raise InvalidImage("Ein Bild ist zu gross (max. 15 MB).")
    try:
        with Image.open(upload, formats=FORMATS) as original:
            image = ImageOps.exif_transpose(original)
            image.load()
    except (OSError, ValueError, Image.DecompressionBombError):
        raise InvalidImage("Eine Datei ist kein gültiges Bild.")

    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGBA")
    return image


def thumbnail(image):
    side = min(THUMBNAIL_SIDE, *image.size)
    return webp(ImageOps.fit(image, (side, side), method=Image.Resampling.LANCZOS))


def resized(upload):
    image = load(upload)
    image.thumbnail((MAX_SIDE, MAX_SIDE), Image.Resampling.LANCZOS)
    return image


def compress(uploads):
    if len(uploads) > MAX_IMAGES:
        raise InvalidImage(f"Du kannst höchstens {MAX_IMAGES} Bilder hochladen.")

    first, *rest = [resized(upload) for upload in uploads]
    files = [(webp(image), *image.size) for image in [first, *rest]]
    return files, thumbnail(first), *first.size
