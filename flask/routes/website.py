from flask import render_template_string
import os


def render_template(file, **context):
    with open(os.path.join('flask', 'templates', file), 'r') as f:
        return render_template_string(f.read(), **context)

def index():
    return render_template("index.html")
