import os
import time
from typing import Tuple

from PIL import Image
from flask import Blueprint, request
from flask.globals import current_app
from werkzeug.utils import secure_filename

from remote_inky.inky import WHITE, Inky
from remote_inky.utils import resize

bp = Blueprint("inky", __name__, url_prefix="")

ALLOWED_EXTENSIONS = ("jpg", "jpeg", "png")


@bp.route("/", methods=("GET",))
def home() -> str:
    return "Hello!"


@bp.route("/image", methods=("POST",))
def image() -> Tuple[str, int]:
    if "file" not in request.files:
        return "File missing", 419
    file = request.files["file"]

    if file.filename == "":
        return "No selected file", 419

    extension = file.filename.split(".")[-1].lower()
    if extension not in ALLOWED_EXTENSIONS:
        return f"Extension ({extension}) not supported", 403

    filename = secure_filename(file.filename)
    file_path = os.path.join("/tmp", filename)
    file.save(file_path)

    saturation = float(request.form.get("saturation", 0.5))

    image = resize(Image.open(file_path), (600, 448))
    inky: Inky = current_app.config["inky"]
    inky.set_image(image, saturation=saturation)
    inky.show()

    return f"Updated with saturation {saturation}!", 200


@bp.route("/clear", methods=("POST",))
def clear() -> Tuple[str, int]:
    inky: Inky = current_app.config["inky"]
    for _ in range(2):
        for y in range(inky.HEIGHT - 1):
            for x in range(inky.WIDTH - 1):
                inky.set_pixel(x, y, WHITE)

        inky.show()
        time.sleep(1)

    return "Screen cleared", 200
