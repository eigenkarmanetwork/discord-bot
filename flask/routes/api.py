from database import DatabaseManager
from flask import redirect, request, Response, url_for
import dotenv
import os
import requests
import secrets
import time

dotenv.load_dotenv()


def authorize_discord() -> Response:
    discord_code = request.args["code"]
    data = {
        "client_id": os.getenv("DISCORD_CLIENT_ID"),
        "client_secret": os.getenv("DISCORD_CLIENT_SECRET"),
        "grant_type": "authorization_code",
        "code": discord_code,
        "redirect_uri": "http://discord.eigentrust.net/authorize_discord",
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    r = requests.post("https://discord.com/api/v10/oauth2/token", data=data, headers=headers)
    r.raise_for_status()
    response = r.json()
    token_type = response["token_type"]
    token = response["access_token"]
    headers = {
        "Authorization": f"{token_type} {token}",
    }
    r = requests.get("https://discord.com/api/v10/users/@me", headers=headers)
    r.raise_for_status()
    response = r.json()
    nonce = secrets.token_hex()
    expires = int(time.time()) + (60 * 15)  # Expires in 15 minutes
    with DatabaseManager() as db:
        db.execute("DELETE FROM pending_connections WHERE id=:id", {"id": response["id"]})
        db.execute(
            "INSERT INTO pending_connections (id, nonce, expires) VALUES (?, ?, ?)",
            (response["id"], nonce, expires),
        )
    return redirect("/login")
