import asyncio
import discord
import dotenv
import os
import shlex
import threading

dotenv.load_dotenv()

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

        @self.client.event
        async def on_message(message: discord.message.Message) -> None:
            if message.clean_content[0:5].lower() == "!etn ":
                raw_command = shlex.split(message.clean_content[5:])
                command = raw_command[0]
                args = raw_command[1:]
                print(f"Received Command: `{command}`")
                if command.lower() == "ping":
                    await message.channel.send("Pong!")
                elif command.lower() == "help":
                    if len(args) == 1:
                        match args[0]:
                            case "ping":
                                await message.channel.send("Makes the ETN bot say `Pong!` as soon as possible.")
                            case "help":
                                await message.channel.send("Attempts to give help for any given command.")
                            case _:
                                await message.channel.send(f"No help for: `{args[0]}`")
                    elif len(args) == 0:
                        await message.channel.send("Commands:\n\nping\nhelp")
                    else:
                        await message.channel.send("Cannot provide help for multiple commands at once.")
                else:
                    await message.channel.send(f"Unknown Command: `{command}`")

        @self.client.event
        async def on_raw_reaction_add(payload: discord.raw_models.RawReactionActionEvent) -> None:
            print("Discord bot noticed a reaction was added!")

        @self.client.event
        async def on_raw_reaction_remove(payload: discord.raw_models.RawReactionActionEvent) -> None:
            print("Discord bot noticed a reaction was removed!")

if __name__ == "__main__":
    discord_handler = DiscordHandler()
    discord_handler.client.run(os.getenv("DISCORD_TOKEN", None))
