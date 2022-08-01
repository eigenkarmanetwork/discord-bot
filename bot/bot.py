from database import DatabaseManager
from helpers import join_message
import discord
import dotenv
import json
import os
import requests
import shlex


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
                admin = message.author.guild_permissions.administrator
                raw_command = shlex.split(message.clean_content[5:])
                command = raw_command[0]
                args = raw_command[1:]
                print(f"Received Command: `{command}`")
                if command.lower() == "ping":
                    await message.channel.send("Pong!")

                elif command.lower() == "add_trust_react":
                    if not admin:
                        await message.channel.send(f"Error: Only server administrators can use this command.")
                        return
                    if len(args) != 2:
                        await message.channel.send(f"Error: Expected 2 arguments, got {len(args)}")
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
                    with DatabaseManager() as db:
                        result = db.execute("SELECT * FROM guilds WHERE id=:id", {"id": message.guild.id})
                        row = result.fetchone()
                        assert row is not None
                        guild_reacts = json.loads(row["reactions"])
                    response = "Current trust reactions:"
                    for react in guild_reacts:
                        response += f"\n{react}: {guild_reacts[react]}"
                    await message.channel.send(response)

                elif command.lower() in ["remove_trust_react", "delete_trust_react"]:
                    if not admin:
                        await message.channel.send(f"Error: Only server administrators can use this command.")
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
                                await message.channel.send("Adds a reaction to use for trust.\nUsage: !etn add_trust_react <emoji> <flavor>")
                            case "list_trust_reacts":
                                await message.channel.send("Lists all reactions used for trust.")
                            case "remove_trust_react" | "delete_trust_react":
                                await message.channel.send("Removes a reaction to use for trust.\nUsage: !etn remove_trust_react <emoji>")
                            case _:
                                await message.channel.send(f"No help for: `{args[0]}`")
                    elif len(args) == 0:
                        await message.channel.send("Commands:\n\nadd_trust_react\nremove_trust_react\nlist_trust_reacts\nping\nhelp")
                    else:
                        await message.channel.send("Cannot provide help for multiple commands at once.")
                else:
                    await message.channel.send(f"Unknown Command: `{command}`")

        @self.client.event
        async def on_raw_reaction_add(payload: discord.raw_models.RawReactionActionEvent) -> None:
            print("Discord bot noticed a reaction was added!")
            print(f"Payload: {payload}")
            print(f"Emoji: {payload.emoji}")

        @self.client.event
        async def on_raw_reaction_remove(payload: discord.raw_models.RawReactionActionEvent) -> None:
            print("Discord bot noticed a reaction was removed!")


if __name__ == "__main__":
    discord_handler = DiscordHandler()
    discord_handler.client.run(os.getenv("DISCORD_TOKEN", None))
