from database import DatabaseManager
from helpers import is_admin, join_message, send_dm
from reacts import process_add_reaction, process_remove_reaction
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
            if message.clean_content[0:5].lower() == "!ekn ":
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
                        "EigenKarma.Net is your own personal karma system, letting you see what the people you trust think of others. You can allocate trust of different flavors to people using Discord reacts when they do something which you think is good and makes you want to upweight them in the trust graph, both from your personal point of view and from the view of anyone who trusts you."
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

                elif command.lower() == "list_flavors":
                    r = requests.get("https://www.eigenkarma.net:31415/categories")
                    categories = json.loads(r.text)
                    await message.channel.send("Available Flavors:\n\n" + ("\n".join(categories)))

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
                    if emojis.decode(args[0]) == ":mag:":
                        await message.channel.send(f"Error: {args[0]} is a reserved react.")
                        return
                    r = requests.get("https://www.eigenkarma.net:31415/categories")
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
                                    "Adds a reaction to use for trust.\nUsage: !ekn add_trust_react <emoji> <flavor>"
                                )
                            case "list_trust_reacts":
                                await message.channel.send("Lists all reactions used for trust.")
                            case "remove_trust_react" | "delete_trust_react":
                                await message.channel.send(
                                    "Removes a reaction to use for trust.\nUsage: !ekn remove_trust_react <emoji>"
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
            await process_add_reaction(self, payload)

        @self.client.event
        async def on_raw_reaction_remove(payload: discord.raw_models.RawReactionActionEvent) -> None:
            print("Discord bot noticed a reaction was removed!")
            print(f"Payload: {payload}")
            print(f"Emoji: {payload.emoji}")
            if not payload.guild_id:
                print("Reaction not in a server.")
                return
            await process_remove_reaction(self, payload)


if __name__ == "__main__":
    discord_handler = DiscordHandler()
    discord_handler.client.run(os.getenv("DISCORD_TOKEN", None))
