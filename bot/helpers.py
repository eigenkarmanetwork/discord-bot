import discord


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
