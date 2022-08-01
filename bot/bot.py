import asyncio
import discord
import dotenv
import os
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
            print("Discord bot received a message!")
            if message.clean_content[0:5].lower() == "!etn ":
                command = message.clean_content[5:]
                print(f"Received Command: `{command}`")
                if command.lower() == "ping":
                    await message.channel.send("Pong!")

        @self.client.event
        async def on_raw_reaction_add(payload: discord.raw_models.RawReactionActionEvent) -> None:
            print("Discord bot noticed a reaction was added!")

        @self.client.event
        async def on_raw_reaction_remove(payload: discord.raw_models.RawReactionActionEvent) -> None:
            print("Discord bot noticed a reaction was removed!")

if __name__ == "__main__":
    discord_handler = DiscordHandler()
    discord_handler.client.run(os.getenv("DISCORD_TOKEN", None))
