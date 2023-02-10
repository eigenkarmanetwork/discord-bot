from database import DatabaseManager
from typing import Optional
import discord
import json
import os
import requests
import sqlite3


async def join_message(guild: discord.guild.Guild) -> None:
    channels = guild.text_channels
    use_channel = None
    for channel in channels:
        if channel.name == "general":
            use_channel = channel
            break
    if not use_channel:
        use_channel = channels[0]

    await use_channel.send(
        "Thank you for adding the EKN Discord Bot!\n"
        + "Please use `!ekn add_trust_react <emoji> <flavor>` to configure your server.\n"
        + "\n"
        + "For a list of flavors, please use `!ekn list_flavors`.\n"
        + "To change who can edit the EKN bot please use `!ekn add_admin_role <role mention>`.\n"
        + "For a list of other commands, please use `!ekn help`."
    )


async def send_dm(member: discord.abc.User, msg: str) -> None:
    if member.dm_channel:
        await member.dm_channel.send(msg)
        return
    dm_channel = await member.create_dm()
    await dm_channel.send(msg)


def is_admin(member: discord.member.Member) -> bool:
    admin = member.guild_permissions.administrator
    if not admin:
        with DatabaseManager() as db:
            result = db.execute("SELECT * FROM guilds WHERE id=:id", {"id": member.guild.id})
            guild = result.fetchone()
            assert guild is not None
            guild_admin_roles = json.loads(guild["admin_roles"])
            if len(guild_admin_roles) == 0:
                return "EigenAdmin" in [role.name for role in member.roles]
            member_roles = [f"<@&{role.id}>" for role in member.roles]
            for role in member_roles:
                if role in guild_admin_roles:
                    return True
    return admin


def create_temp_user(username: str | int) -> Optional[sqlite3.Row]:
    data = {
        "service_name": os.getenv("ETN_SERVICE_NAME"),
        "service_key": os.getenv("ETN_SERVICE_KEY"),
        "service_user": username,
    }
    headers = {
        "Content-Type": "application/json",
    }
    r = requests.post(
        "https://eigenkarma.net:31415/register_temp_user", data=json.dumps(data), headers=headers
    )
    r.raise_for_status()
    data["username"] = data["service_user"]
    del data["service_user"]
    r = requests.post("https://eigenkarma.net:31415/get_current_key", data=json.dumps(data), headers=headers)
    r.raise_for_status()
    response = json.loads(r.text)
    key = response["password"]
    key_type = response["password_type"]
    expires = response["expires"]
    with DatabaseManager() as db:
        db.execute(
            "INSERT INTO connections (id, key, key_type, expires) VALUES (?, ?, ?, ?)",
            (int(username), key, key_type, expires),
        )
        result = db.execute("SELECT * FROM connections WHERE id=:id", {"id": int(username)})
        return result.fetchone()
