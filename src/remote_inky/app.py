import os

from flask import Flask, abort, request
from flask_cors import CORS


def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    CORS(app, origins="*")
    token = os.environ["TOKEN"]
    app.config.from_mapping(
        SECRET_KEY=os.environ["SECRET_KEY"],
        TOKEN=token,
    )

    from . import views

    app.register_blueprint(views.bp)

    from .extensions import configure_extensions

    configure_extensions(app)

    @app.before_request
    def before_request() -> None:
        request_token = request.headers.get("x-api-token")
        if request_token != token:
            abort(403)

    return app
