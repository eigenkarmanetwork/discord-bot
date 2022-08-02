from flask import Flask
from routes import api, website

app = Flask(__name__)

app.add_url_rule("/", view_func=website.index)
app.add_url_rule("/authorize_discord", view_func=api.authorize_discord)
app.add_url_rule("/connect", view_func=api.connect)
app.add_url_rule("/connected.html", view_func=website.connected)
app.add_url_rule("/index.html", view_func=website.index)
app.add_url_rule("/login", view_func=website.login)
