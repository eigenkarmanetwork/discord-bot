from flask import render_template_string, Response
import os


def render_template(file, **context) -> Response:
    with open(os.path.join("flask", "templates", file), "r") as f:
        return render_template_string(f.read(), **context)


def index() -> Response:
    return render_template("index.html")


def login() -> Response:
    return render_template("login.html")


def connected() -> Response:
    return render_template("connected.html")


def vote() -> Response:
    return render_template("vote.html")


def voted() -> Response:
    return render_template("voted.html")
