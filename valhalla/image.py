import hashlib
from io import BytesIO

from fastapi import HTTPException
from PIL import Image, UnidentifiedImageError


def gen_skin_hash(image_data: bytes) -> str:
    try:
        with Image.open(BytesIO(image_data)) as image:
            if image.format != "PNG":
                raise HTTPException(400, f"Format not allowed: {image.format}")

            # Check size of image.
            # width should be same as or double the height
            # Width is then checked for predefined values
            # 64, 128, 256, 512, 1024

            # set of supported width sizes. Height is either same or half
            sizes = {64, 128, 256, 512, 1024}
            (width, height) = image.size
            valid = width / 2 == height or width == height

            if not valid or width not in sizes:
                raise HTTPException(400, f"Unsupported image size: {image.size}")

            # Create a hash of the image and use it as the filename.
            return hashlib.sha1(image.tobytes()).hexdigest()
    except UnidentifiedImageError as e:
        raise HTTPException(400, str(e))
