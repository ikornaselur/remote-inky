from flask import Flask

from remote_inky.inky import Inky


def configure_extensions(app: Flask) -> None:
    app.config["inky"] = Inky()
