from database import DatabaseManager
from flask import redirect, request, Response
from helpers import get_params
import dotenv
import json
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
    user_id = response["id"]
    nonce = secrets.token_hex()
    expires = int(time.time()) + (60 * 15)  # Expires in 15 minutes
    with DatabaseManager() as db:
        db.execute("DELETE FROM pending_connections WHERE id=:id", {"id": response["id"]})
        db.execute(
            "INSERT INTO pending_connections (id, nonce, expires) VALUES (?, ?, ?)",
            (user_id, nonce, expires),
        )
    return redirect(f"/login?id={user_id}&nonce={nonce}")


def connect() -> Response:
    username, password, id, nonce = get_params(["username", "password", "id", "nonce"])
    with DatabaseManager() as db:
        result = db.execute(
            "SELECT * FROM pending_connections WHERE id=:id AND nonce=:nonce",
            {"id": id, "nonce": nonce},
        )
        row = result.fetchone()
        if not row:
            return Response("Connection attempt does not exist.", 404)
        if row["expires"] < time.time():
            return Response("Connection attempt has expired.", 404)
    data = {
        "service_name": os.getenv("ETN_SERVICE_NAME"),
        "service_key": os.getenv("ETN_SERVICE_KEY"),
        "service_user": id,
        "username": username,
        "password": password,
        "password_type": "raw_password",
    }
    headers = {
        "Content-Type": "application/json",
    }
    r = requests.post(
        "https://www.eigentrust.net:31415/register_connection", data=json.dumps(data), headers=headers
    )
    if r.status_code != 200:
        return Response(r.text, r.status_code)
    response = json.loads(r.text)
    key = response["password"]
    key_type = response["password_type"]
    expires = response["expires"]
    if key_type == "password_hash":
        key = None
        key_type = None

    with DatabaseManager() as db:
        db.execute("DELETE FROM pending_connections WHERE id=:id", {"id": id})
        result = db.execute("SELECT * FROM connections WHERE id=:id", {"id": id})
        if result.fetchone():
            db.execute("DELETE FROM connections WHERE id=:id", {"id": id})
            db.commit()
        else:
            db.execute(
                "INSERT INTO connections (id, key, key_type, expires) VALUES (?, ?, ?, ?)",
                (id, key, key_type, expires),
            )
    return Response("Success.", 200)


def cast_vote() -> Response:
    password, voter_id, votee_id, message_id = get_params(["password", "voter_id", "votee_id", "message_id"])
    with DatabaseManager() as db:
        result = db.execute(
            "SELECT * FROM pending_votes WHERE voter_id=:voter_id AND votee_id=:votee_id AND message_id=:message_id",
            {"voter_id": voter_id, "votee_id": votee_id, "message_id": message_id},
        )
        vote_row = result.fetchone()
        if not vote_row:
            return Response("Vote does not exist, has it already been authorized?", 404)
    data = {
        "service_name": os.getenv("ETN_SERVICE_NAME"),
        "service_key": os.getenv("ETN_SERVICE_KEY"),
        "to": votee_id,
        "from": voter_id,
        "password": password,
        "password_type": "raw_password",
    }
    headers = {
        "Content-Type": "application/json",
    }
    r = requests.post("https://www.eigentrust.net:31415/vote", data=json.dumps(data), headers=headers)
    if r.status_code != 200:
        return Response(r.text, r.status_code)
    with DatabaseManager() as db:
        db.execute(
            "DELETE FROM pending_votes WHERE voter_id=:voter_id AND votee_id=:votee_id AND message_id=:message_id",
            {"voter_id": voter_id, "votee_id": votee_id, "message_id": message_id},
        )
    return Response(r.text, r.status_code)


def lookup() -> Response:
    password, _for, _from = get_params(["password", "for", "from"])
    data = {
        "service_name": os.getenv("ETN_SERVICE_NAME"),
        "service_key": os.getenv("ETN_SERVICE_KEY"),
        "for": _for,
        "from": _from,
        "password": password,
        "password_type": "raw_password",
    }
    headers = {
        "Content-Type": "application/json",
    }
    r = requests.post("https://www.eigentrust.net:31415/get_vote_count", data=json.dumps(data), headers=headers)
    if r.status_code != 200:
        return Response(r.text, r.status_code)
    response_data = json.loads(r.text)
    assert response_data is not None

    response = {"votes": response_data["votes"]}

    r = requests.post("https://www.eigentrust.net:31415/get_score", data=json.dumps(data), headers=headers)
    if r.status_code != 200:
        return Response(r.text, r.status_code)
    response_data = json.loads(r.text)
    assert response_data is not None

    response["score"] = response_data["score"]

    return Response(json.dumps(response), 200)
