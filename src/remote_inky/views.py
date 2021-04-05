import os
from typing import Tuple

from PIL import Image
from flask import Blueprint, request
from flask.globals import current_app
from werkzeug.utils import secure_filename

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

    image = Image.open(file_path)
    inky = current_app.config["inky"]
    inky.set_image(image, saturation=0.5)
    inky.show()

    return "Updated!", 200
