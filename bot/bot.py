from database import DatabaseManager
from helpers import is_admin, join_message, send_dm
import asyncio
import discord
import dotenv
import emojis
import json
import os
import re
import requests
import shlex
import time


dotenv.load_dotenv()


DatabaseManager()  # Update database before startup


class DiscordHandler:
    def __init__(self):
        intents = discord.Intents.all()
        self.client = discord.Client(intents=intents)

        """
        All discord functions need to be under another function in order to use self.
        """

        @self.client.event
        async def on_ready() -> None:
            print("Discord bot is ready!")
            with DatabaseManager() as db:
                for guild in self.client.guilds:
                    result = db.execute("SELECT * FROM guilds WHERE id=:id", {"id": guild.id})
                    if not result.fetchone():
                        # Joined guild while offline!
                        db.execute(
                            "INSERT INTO guilds (id, name, reactions) VALUES (?, ?, ?)",
                            (guild.id, guild.name, "{}"),
                        )
                        await join_message(guild)

        @self.client.event
        async def on_guild_join(guild: discord.guild.Guild) -> None:
            print(f"Joined guild: {guild.id}")
            with DatabaseManager() as db:
                db.execute(
                    "INSERT INTO guilds (id, name, reactions) VALUES (?, ?, ?)", (guild.id, guild.name, "{}")
                )
            await join_message(guild)

        @self.client.event
        async def on_guild_remove(guild: discord.guild.Guild) -> None:
            print(f"Left guild: {guild.id}")
            with DatabaseManager() as db:
                db.execute("DELETE FROM guilds WHERE id=:id", {"id": guild.id})

        @self.client.event
        async def on_message(message: discord.message.Message) -> None:
            if message.clean_content[0:5].lower() == "!etn ":
                is_dm = True
                admin = False
                if not isinstance(message.channel, discord.channel.DMChannel):
                    is_dm = False
                    admin = is_admin(message.author)
                raw_command = shlex.split(message.content[5:])
                command = raw_command[0]
                args = raw_command[1:]
                print(f"Received Command: `{command}`")
                if command.lower() == "ping":
                    await message.channel.send("Pong!")

                elif command.lower() == "about":
                    await message.channel.send(
                        "EigenTrust.Net is your own personal karma system, letting you see what the people you trust think of others. You can allocate trust of different flavors to people using Discord reacts when they do something which you think is good and makes you want to upweight them in the trust graph, both from your personal point of view and from the view of anyone who trusts you."
                    )
                    return

                elif command.lower() == "add_admin_role":
                    if is_dm:
                        await message.channel.send("Error: You can only use this command in a server.")
                        return
                    if not admin:
                        await message.channel.send("Error: Only server and bot administrators can use this command.")
                        return
                    if len(args) != 1:
                        await message.channel.send(f"Error: Expected 1 argument, got {len(args)}")
                        return
                    is_valid_role = re.search("<@&[0-9]+>", args[0])
                    args[0] = is_valid_role[0]
                    if not is_valid_role:
                        print(f"Error got invalid role: {args[0]}")
                        await message.channel.send(f"Error: First argument must be a @role")
                        return
                    args[0] = is_valid_role[0]
                    with DatabaseManager() as db:
                        result = db.execute("SELECT * FROM guilds WHERE id=:id", {"id": message.guild.id})
                        row = result.fetchone()
                        assert row is not None
                        guild_admin_roles = json.loads(row["admin_roles"])
                        if args[0] not in guild_admin_roles:
                            guild_admin_roles.append(args[0])
                            new_roles = json.dumps(guild_admin_roles)
                            db.execute(
                                "UPDATE guilds SET admin_roles=:admin_roles WHERE id=:id",
                                {"admin_roles": new_roles, "id": message.guild.id},
                            )
                    response = "New admin roles:"
                    for role in guild_admin_roles:
                        response += f"\n{role}"
                    await message.channel.send(response)

                elif command.lower() in ["remove_admin_role", "delete_admin_role"]:
                    if is_dm:
                        await message.channel.send("Error: You can only use this command in a server.")
                        return
                    if not admin:
                        await message.channel.send("Error: Only server and bot administrators can use this command.")
                        return
                    if len(args) != 1:
                        await message.channel.send(f"Error: Expected 1 argument, got {len(args)}")
                        return
                    is_valid_role = re.search("<@&[0-9]+>", args[0])
                    args[0] = is_valid_role[0]
                    if not is_valid_role:
                        print(f"Error got invalid role: {args[0]}")
                        await message.channel.send(f"Error: First argument must be a @role")
                        return
                    with DatabaseManager() as db:
                        result = db.execute("SELECT * FROM guilds WHERE id=:id", {"id": message.guild.id})
                        row = result.fetchone()
                        assert row is not None
                        guild_admin_roles = json.loads(row["admin_roles"])
                        if args[0] not in guild_admin_roles:
                            await message.channel.send(f"{args[0]} is not an admin bot role.")
                            return
                        guild_admin_roles.remove(args[0])
                        new_roles = json.dumps(guild_admin_roles)
                        db.execute(
                            "UPDATE guilds SET admin_roles=:admin_roles WHERE id=:id",
                            {"admin_roles": new_roles, "id": message.guild.id},
                        )
                    response = "New admin roles:"
                    for role in guild_admin_roles:
                        response += f"\n{role}"
                    if not guild_admin_roles:
                        response += "\nEigenAdmin"
                    await message.channel.send(response)

                elif command.lower() == "list_admin_roles":
                    if is_dm:
                        await message.channel.send("Error: You can only use this command in a server.")
                        return
                    with DatabaseManager() as db:
                        result = db.execute("SELECT * FROM guilds WHERE id=:id", {"id": message.guild.id})
                        row = result.fetchone()
                        assert row is not None
                        guild_admin_roles = json.loads(row["admin_roles"])
                    response = "Current admin roles:"
                    for role in guild_admin_roles:
                        response += f"\n{role}"
                    if not guild_admin_roles:
                        response += "\nEigenAdmin"
                    await message.channel.send(response)

                elif command.lower() == "add_trust_react":
                    if is_dm:
                        await message.channel.send("Error: You can only use this command in a server.")
                        return
                    if not admin:
                        await message.channel.send("Error: Only server and bot administrators can use this command.")
                        return
                    if len(args) != 2:
                        await message.channel.send(f"Error: Expected 2 arguments, got {len(args)}")
                        return
                    custom_emojis = [str(e) for e in message.guild.emojis]
                    if args[0] not in custom_emojis and emojis.count(args[0]) == 0:
                        await message.channel.send(f"Error: {args[0]} is not an emoji.")
                        return
                    r = requests.get("http://www.eigentrust.net:31415/categories")
                    categories = json.loads(r.text)
                    if args[1].lower() not in categories:
                        await message.channel.send(f"Error: The flavor `{args[1]}` does not exist.")
                        return
                    with DatabaseManager() as db:
                        result = db.execute("SELECT * FROM guilds WHERE id=:id", {"id": message.guild.id})
                        row = result.fetchone()
                        assert row is not None
                        guild_reacts = json.loads(row["reactions"])
                        guild_reacts[args[0]] = args[1].lower()
                        new_reacts = json.dumps(guild_reacts)
                        db.execute(
                            "UPDATE guilds SET reactions=:reacts WHERE id=:id",
                            {"reacts": new_reacts, "id": message.guild.id},
                        )
                    response = "New reactions:"
                    for react in guild_reacts:
                        response += f"\n{react}: {guild_reacts[react]}"
                    await message.channel.send(response)

                elif command.lower() == "list_trust_reacts":
                    if is_dm:
                        await message.channel.send("Error: You can only use this command in a server.")
                        return
                    with DatabaseManager() as db:
                        result = db.execute("SELECT * FROM guilds WHERE id=:id", {"id": message.guild.id})
                        row = result.fetchone()
                        assert row is not None
                        guild_reacts = json.loads(row["reactions"])
                    response = "Current trust reactions:"
                    for react in guild_reacts:
                        response += f"\n{react}: {guild_reacts[react]}"
                    if not guild_reacts:
                        response += "\nNo reactions configured."
                    await message.channel.send(response)

                elif command.lower() in ["remove_trust_react", "delete_trust_react"]:
                    if is_dm:
                        await message.channel.send("Error: You can only use this command in a server.")
                        return
                    if not admin:
                        await message.channel.send("Error: Only server and bot administrators can use this command.")
                        return
                    if len(args) != 1:
                        await message.channel.send(f"Error: Expected 1 arguments, got {len(args)}")
                        return
                    with DatabaseManager() as db:
                        result = db.execute("SELECT * FROM guilds WHERE id=:id", {"id": message.guild.id})
                        row = result.fetchone()
                        assert row is not None
                        guild_reacts = json.loads(row["reactions"])
                        if args[0] not in guild_reacts:
                            await message.channel.send(f"{args[0]} is not a trust reaction.")
                            return
                        del guild_reacts[args[0]]
                        new_reacts = json.dumps(guild_reacts)
                        db.execute(
                            "UPDATE guilds SET reactions=:reacts WHERE id=:id",
                            {"reacts": new_reacts, "id": message.guild.id},
                        )
                    response = "New reactions:"
                    for react in guild_reacts:
                        response += f"\n{react}: {guild_reacts[react]}"
                    if not guild_reacts:
                        response += "\nNo reactions configured."
                    await message.channel.send(response)

                elif command.lower() == "help":
                    if len(args) == 1:
                        match args[0]:
                            case "ping":
                                await message.channel.send(
                                    "Makes the ETN bot say `Pong!` as soon as possible."
                                )
                            case "help":
                                await message.channel.send("Attempts to give help for any given command.")
                            case "add_trust_react":
                                await message.channel.send(
                                    "Adds a reaction to use for trust.\nUsage: !etn add_trust_react <emoji> <flavor>"
                                )
                            case "list_trust_reacts":
                                await message.channel.send("Lists all reactions used for trust.")
                            case "remove_trust_react" | "delete_trust_react":
                                await message.channel.send(
                                    "Removes a reaction to use for trust.\nUsage: !etn remove_trust_react <emoji>"
                                )
                            case _:
                                await message.channel.send(f"No help for: `{args[0]}`")
                    elif len(args) == 0:
                        await message.channel.send(
                            "Commands:\n\nabout\nadd_trust_react\nremove_trust_react\nlist_trust_reacts\nping\nhelp"
                        )
                    else:
                        await message.channel.send("Cannot provide help for multiple commands at once.")
                else:
                    await message.channel.send(f"Unknown Command: `{command}`")

        @self.client.event
        async def on_raw_reaction_add(payload: discord.raw_models.RawReactionActionEvent) -> None:
            print("Discord bot noticed a reaction was added!")
            print(f"Payload: {payload}")
            print(f"Emoji: {payload.emoji}")
            if not payload.guild_id:
                print("Reaction not in a server.")
                return
            with DatabaseManager() as db:
                voter_id = payload.user_id
                message = await payload.member.guild.get_channel(payload.channel_id).fetch_message(
                    payload.message_id
                )
                votee_id = message.author.id
                if voter_id == votee_id:
                    print("User cannot vote for themselves.")
                    return None
                result = db.execute("SELECT * FROM guilds WHERE id=:id", {"id": payload.guild_id})
                row = result.fetchone()
                if not row:
                    print("Server is not connected?")
                    return
                reacts = json.loads(row["reactions"])
                if str(payload.emoji) not in reacts:
                    print("Not a trust reaction")
                    return
                result = db.execute("SELECT * FROM connections WHERE id=:id", {"id": voter_id})
                row = result.fetchone()
                if not row:
                    await send_dm(
                        payload.member,
                        "Your Discord is not connected to the ETN.  "
                        + "Please connect your account at http://discord.eigentrust.net/ to vote.",
                    )
                    return
                result = db.execute("SELECT * FROM connections WHERE id=:id", {"id": votee_id})
                row = result.fetchone()
                if not row:
                    result = db.execute("SELECT * FROM missed_votes WHERE id=:id", {"id": votee_id})
                    row = result.fetchone()
                    if not row:
                        db.execute("INSERT INTO missed_votes (id, count) VALUES (?, 1)", (votee_id,))
                        votee_user = await self.client.fetch_user(votee_id)
                        votee_name = f"{votee_user.name}#{votee_user.discriminator}"
                        await send_dm(
                            payload.member,
                            f"Unable to vote for {votee_name}.  "
                            + "They have not connected their Discord to the ETN.",
                        )
                    else:
                        db.execute(
                            "UPDATE missed_votes SET count=:count WHERE id=:id",
                            {"id": votee_id, "count": row["count"] + 1},
                        )
                        if row["count"] + 1 == 5:
                            await send_dm(
                                message.author,
                                f"Hello {message.author.name}, other Discord users have attempted to vote "
                                + "for you on the EigenTrust Network.  However, they were unsuccessful as "
                                + "you have not linked your Discord to the ETN.  To learn what the ETN is "
                                + "about please say to me `!etn about`.  If you would like to join and do "
                                + "not have an ETN account, please go to http://www.eigentrust.net/ and "
                                + "register.  If you do have an account, and would like to link your "
                                + "Discord, please go to http://discord.eigentrust.net/",
                            )
                    return

                data = {
                    "username": str(voter_id),
                    "service_name": os.getenv("ETN_SERVICE_NAME"),
                    "service_key": os.getenv("ETN_SERVICE_KEY"),
                }
                headers = {
                    "Content-Type": "application/json",
                }
                r = requests.post(
                    "http://www.eigentrust.net:31415/get_current_key", data=json.dumps(data), headers=headers
                )
                if r.status_code not in [200, 404]:  # If not an exceptable error code:
                    print(f"{r.status_code}: {r.text}")
                    r.raise_for_status()
                if r.status_code == 404:
                    if r.text != "No key available.":
                        print(f"{r.status_code}: {r.text}")
                        r.raise_for_status()
                    db.execute(
                        "INSERT INTO pending_votes (voter_id, message_id, channel_id, guild_id, votee_id) VALUES (?, ?, ?, ?, ?)",
                        (voter_id, payload.message_id, payload.channel_id, payload.guild_id, votee_id),
                    )
                    await send_dm(
                        payload.member,
                        "Due to your security settings, you'll need to enter your password to vote for "
                        + f"{message.author.name}#{message.author.discriminator}.  Please go to "
                        + f"http://discord.eigentrust.net/vote?voter={voter_id}&votee={votee_id}"
                        + f"&message={payload.message_id} to vote",
                    )
                    return
                assert r.status_code == 200
                data = json.loads(r.text)
                password = data["password"]
                password_type = data["password_type"]
                expires = data["expires"]
                if expires - 10 < time.time() and password_type == "session_key":
                    # If session key is about to expire, wait for it to expire and recall this funciton.
                    # This will make the user be caught by the "Please enter your password" message instead
                    # of trying to get this vote in before time runs out.
                    await asyncio.sleep(10)
                    return await on_raw_reaction_add(payload)
                data = {
                    "service_name": os.getenv("ETN_SERVICE_NAME"),
                    "service_key": os.getenv("ETN_SERVICE_KEY"),
                    "to": str(votee_id),
                    "from": str(voter_id),
                    "password": password,
                    "password_type": password_type,
                }
                headers = {
                    "Content-Type": "application/json",
                }
                r = requests.post(
                    "http://www.eigentrust.net:31415/vote", data=json.dumps(data), headers=headers
                )
                if r.status_code != 200:
                    await send_dm(
                        payload.member, f"Error casting vote: `{r.text}` Error Code: `{r.status_code}`."
                    )
                    return

        @self.client.event
        async def on_raw_reaction_remove(payload: discord.raw_models.RawReactionActionEvent) -> None:
            print("Discord bot noticed a reaction was removed!")
            print(f"Payload: {payload}")
            guild = self.client.get_guild(payload.guild_id)
            voter_id = payload.user_id
            message = await guild.get_channel(payload.channel_id).fetch_message(payload.message_id)
            votee_id = message.author.id


if __name__ == "__main__":
    discord_handler = DiscordHandler()
    discord_handler.client.run(os.getenv("DISCORD_TOKEN", None))
