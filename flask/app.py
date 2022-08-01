from database import DatabaseManager
from flask import Flask
from routes import website

app = Flask(__name__)

app.add_url_rule("/index.html", view_func=website.index)
