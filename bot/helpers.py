from database import DatabaseManager
import discord
import json


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
        "Thank you for adding the ETN Discord Bot!\nPlease use `!etn add_trust_react <emoji> <flavor>` to configure your server."
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
