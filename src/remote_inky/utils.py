from typing import Any, Tuple

from PIL import Image


def resize(image: Any, resolution: Tuple[int, int]) -> Any:
    goal_ratio = resolution[0] / resolution[1]
    image_ratio: float = image.size[0] / image.size[1]

    if image_ratio > goal_ratio:
        resized = image.resize(
            (int(resolution[1] * image_ratio), resolution[1]), Image.ANTIALIAS
        )
        crop_width = resized.size[0] - resolution[0]
        if crop_width % 2 == 0:
            left_side = right_side = crop_width // 2
        else:
            left_side = crop_width // 2
            right_side = left_side + 1
        cropped = resized.crop(
            (left_side, 0, resized.size[0] - right_side, resized.size[1])
        )
    else:
        resized = image.resize(
            (resolution[0], int(resolution[0] // image_ratio)), Image.ANTIALIAS
        )
        crop_height = resized.size[1] - resolution[1]
        if crop_height % 2 == 0:
            top_side = bottom_side = crop_height // 2
        else:
            top_side = crop_height // 2
            bottom_side = top_side + 1
        cropped = resized.crop(
            (0, top_side, resized.size[0], resized.size[1] - bottom_side)
        )

    return cropped
