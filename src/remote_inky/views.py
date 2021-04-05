from flask import Blueprint

bp = Blueprint("inky", __name__, url_prefix="")


@bp.route("/", methods=("GET",))
def home() -> str:
    return "Hello!"
