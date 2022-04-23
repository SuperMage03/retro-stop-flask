import os
from flask import Flask
from extensions import db


def create_app():
    app = Flask(
            __name__,
            root_path=os.getcwd(),
            static_url_path="/",
            static_folder="/static",
            template_folder="/template"
            )

    set_config(app)
    register_extensions(app)
    return app


def register_extensions(app):
    db.init_app(app)


def set_config(app):
    if app.config["ENV"] == "production":
        app.config.from_object("config.ProductionConfig")
    elif app.config["ENV"] == "testing":
        app.config.from_object("config.TestingConfig")
    else:
        app.config.from_object("config.DevelopmentConfig")


app = create_app()

from app.auth import auth

app.register_blueprint(auth, url_prefix="/auth")

from app.sell import sell

app.register_blueprint(sell, url_prefix="/sell")

from app.buy import buy

app.register_blueprint(buy, url_prefix="/buy")
