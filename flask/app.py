from database import DatabaseManager
from flask import Flask
from routes import api, website

app = Flask(__name__)

app.add_url_rule("/index.html", view_func=website.index)
app.add_url_rule("/", view_func=website.index)
app.add_url_rule("/authorize_discord", view_func=api.authorize_discord)
