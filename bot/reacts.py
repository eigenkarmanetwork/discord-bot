from database import DatabaseManager
from helpers import create_temp_user, send_dm
from typing import TYPE_CHECKING
import urllib.parse
import asyncio
import discord
import emojis
import json
import os
import requests
import time


if TYPE_CHECKING:
    from bot import DiscordHandler


async def process_add_reaction(
    self: "DiscordHandler", payload: discord.raw_models.RawReactionActionEvent
) -> None:
    react_name = str(payload.emoji)
    if payload.emoji.is_unicode_emoji():
        react_name = emojis.decode(str(payload.emoji))
    if react_name in [":mag:"]:
        await process_magnifying_glass(self, payload)
        return
    await process_possible_trust_react(self, payload)


async def process_possible_trust_react(
    self: "DiscordHandler", payload: discord.raw_models.RawReactionActionEvent
) -> None:
    with DatabaseManager() as db:
        voter_id = payload.user_id
        message = await payload.member.guild.get_channel(payload.channel_id).fetch_message(payload.message_id)
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
        flavor = reacts[str(payload.emoji)]
        result = db.execute("SELECT * FROM connections WHERE id=:id", {"id": voter_id})
        row = result.fetchone()
        if not row:
            row = create_temp_user(voter_id)
        result = db.execute("SELECT * FROM connections WHERE id=:id", {"id": votee_id})
        row = result.fetchone()
        if not row:
            row = create_temp_user(votee_id)

        data = {
            "username": str(voter_id),
            "service_name": os.getenv("ETN_SERVICE_NAME"),
            "service_key": os.getenv("ETN_SERVICE_KEY"),
        }
        headers = {
            "Content-Type": "application/json",
        }
        r = requests.post(
            "https://www.eigenkarma.net:31415/get_current_key", data=json.dumps(data), headers=headers
        )
        if r.status_code not in [200, 404]:  # If not an exceptable error code:
            print(f"{r.status_code}: {r.text}")
            r.raise_for_status()
        if r.status_code == 404:
            if r.text != "No key available.":
                print(f"{r.status_code}: {r.text}")
                r.raise_for_status()
            db.execute(
                "INSERT INTO pending_votes (voter_id, message_id, channel_id, guild_id, votee_id, flavor) VALUES (?, ?, ?, ?, ?, ?)",
                (voter_id, payload.message_id, payload.channel_id, payload.guild_id, votee_id, flavor),
            )
            await send_dm(
                payload.member,
                "Due to your security settings, you'll need to enter your password to vote for "
                + f"{message.author.name}#{message.author.discriminator}.  Please go to "
                + f"http://discord.eigentrust.net/vote?voter={voter_id}&votee={votee_id}"
                + f"&message={payload.message_id}&flavor={urllib.parse.quote(flavor)} to vote.",
            )
            return
        assert r.status_code == 200
        data = json.loads(r.text)
        password = data["password"]
        password_type = data["password_type"]
        expires = int(data["expires"] if data["expires"] else 0)
        if expires - 10 < time.time() and password_type == "session_key":
            # If session key is about to expire, wait for it to expire and recall this funciton.
            # This will make the user be caught by the "Please enter your password" message instead
            # of trying to get this vote in before time runs out.
            await asyncio.sleep(10)
            return await process_add_reaction(self, payload)
        data = {
            "service_name": os.getenv("ETN_SERVICE_NAME"),
            "service_key": os.getenv("ETN_SERVICE_KEY"),
            "to": str(votee_id),
            "from": str(voter_id),
            "password": password,
            "password_type": password_type,
            "flavor": flavor,
        }
        headers = {
            "Content-Type": "application/json",
        }
        r = requests.post("https://www.eigenkarma.net:31415/vote", data=json.dumps(data), headers=headers)
        if r.status_code != 200:
            await send_dm(payload.member, f"Error casting vote: `{r.text}` Error Code: `{r.status_code}`.")
            return


async def process_magnifying_glass(
    self: "DiscordHandler", payload: discord.raw_models.RawReactionActionEvent
) -> None:
    with DatabaseManager() as db:
        voter_id = payload.user_id
        message = await payload.member.guild.get_channel(payload.channel_id).fetch_message(payload.message_id)
        votee_id = message.author.id
        if voter_id == votee_id:
            print("User cannot inspect themselves.")
            return None
        result = db.execute("SELECT * FROM guilds WHERE id=:id", {"id": payload.guild_id})
        row = result.fetchone()
        if not row:
            print("Server is not connected?")
            return
        reacts = json.loads(row["reactions"])
        categories = list(reacts.values())
        result = db.execute("SELECT * FROM connections WHERE id=:id", {"id": voter_id})
        row = result.fetchone()
        if not row:
            row = create_temp_user(voter_id)
        result = db.execute("SELECT * FROM connections WHERE id=:id", {"id": votee_id})
        row = result.fetchone()
        if not row:
            row = create_temp_user(votee_id)

        data = {
            "username": str(voter_id),
            "service_name": os.getenv("ETN_SERVICE_NAME"),
            "service_key": os.getenv("ETN_SERVICE_KEY"),
        }
        headers = {
            "Content-Type": "application/json",
        }
        r = requests.post(
            "https://www.eigenkarma.net:31415/get_current_key", data=json.dumps(data), headers=headers
        )
        if r.status_code not in [200, 404]:  # If not an exceptable error code:
            print(f"{r.status_code}: {r.text}")
            r.raise_for_status()
        if r.status_code == 404:
            if r.text != "No key available.":
                print(f"{r.status_code}: {r.text}")
                r.raise_for_status()
            await send_dm(
                payload.member,
                "Due to your security settings, you'll need to enter your password to see your "
                + f"trust score for {message.author.name}#{message.author.discriminator}.  Please go to "
                + f"http://discord.eigentrust.net/lookup.html?for={votee_id}&from={voter_id} to see your "
                + "trust score for them.",
            )
            return
        assert r.status_code == 200
        data = json.loads(r.text)
        password = data["password"]
        password_type = data["password_type"]
        expires = int(data["expires"] if data["expires"] else 0)
        if expires - 10 < time.time() and password_type == "session_key":
            # If session key is about to expire, wait for it to expire and recall this funciton.
            # This will make the user be caught by the "Please enter your password" message instead
            # of trying to get this check in before time runs out.
            await asyncio.sleep(10)
            return await process_add_reaction(self, payload)
        data = {
            "service_name": os.getenv("ETN_SERVICE_NAME"),
            "service_key": os.getenv("ETN_SERVICE_KEY"),
            "for": str(votee_id),
            "from": str(voter_id),
            "password": password,
            "password_type": password_type,
        }
        headers = {
            "Content-Type": "application/json",
        }
        r = requests.post(
            "https://www.eigenkarma.net:31415/get_vote_count", data=json.dumps(data), headers=headers
        )
        if r.status_code != 200:
            await send_dm(
                payload.member, f"Error checking vote count: `{r.text}` Error Code: `{r.status_code}`."
            )
            return
        vote_count = str(json.loads(r.text)["votes"])
        r = requests.post(
            "https://www.eigenkarma.net:31415/get_score", data=json.dumps(data), headers=headers
        )
        if r.status_code != 200:
            await send_dm(
                payload.member, f"Error getting trust score: `{r.text}` Error Code: `{r.status_code}`."
            )
            return
        trust_score = str(json.loads(r.text)["score"])
        response = (
            f"You have voted for {message.author.name}#{message.author.discriminator} (ID "
            + f"{votee_id}) {vote_count} "
            + ("times" if vote_count != "1" else "time") + ".\n"
            + f"Their general score within your trust network is {trust_score}."
        )
        for flavor in categories:
            if flavor == "general":
                continue
            data["flavor"] = flavor
            r = requests.post(
                "https://www.eigenkarma.net:31415/get_vote_count", data=json.dumps(data), headers=headers
            )
            if r.status_code != 200:
                await send_dm(
                    payload.member, f"Error checking vote count: `{r.text}` Error Code: `{r.status_code}`."
                )
                return
            vote_count = str(json.loads(r.text)["votes"])
            r = requests.post(
                "https://www.eigenkarma.net:31415/get_score", data=json.dumps(data), headers=headers
            )
            if r.status_code != 200:
                await send_dm(
                    payload.member, f"Error getting trust score: `{r.text}` Error Code: `{r.status_code}`."
                )
                return
            trust_score = str(json.loads(r.text)["score"])
            response += (
                f"\n\nYou have voted for {message.author.name}#{message.author.discriminator} (ID "
                + f"{votee_id}) {vote_count} "
                + ("times" if vote_count != "1" else "time") + f" in the {flavor} flavor.\n"
                + f"Their {flavor} score within your trust network is {trust_score}."
            )
        await send_dm(payload.member, response)


async def process_remove_reaction(
    self: "DiscordHandler", payload: discord.raw_models.RawReactionActionEvent
) -> None:
    with DatabaseManager() as db:
        guild = self.client.get_guild(payload.guild_id)
        voter_id = payload.user_id
        member = self.client.get_user(voter_id)
        message = await guild.get_channel(payload.channel_id).fetch_message(payload.message_id)
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
        flavor = reacts[str(payload.emoji)]
        result = db.execute("SELECT * FROM connections WHERE id=:id", {"id": voter_id})
        row = result.fetchone()
        if not row:
            row = create_temp_user(voter_id)
        result = db.execute("SELECT * FROM connections WHERE id=:id", {"id": votee_id})
        row = result.fetchone()
        if not row:
            row = create_temp_user(votee_id)

        data: dict[str, str | int | None] = {
            "username": str(voter_id),
            "service_name": os.getenv("ETN_SERVICE_NAME"),
            "service_key": os.getenv("ETN_SERVICE_KEY"),
        }
        headers = {
            "Content-Type": "application/json",
        }
        r = requests.post(
            "https://www.eigenkarma.net:31415/get_current_key", data=json.dumps(data), headers=headers
        )
        if r.status_code not in [200, 404]:  # If not an exceptable error code:
            print(f"{r.status_code}: {r.text}")
            r.raise_for_status()
        if r.status_code == 404:
            if r.text != "No key available.":
                print(f"{r.status_code}: {r.text}")
                r.raise_for_status()
            db.execute(
                "INSERT INTO pending_votes (voter_id, message_id, channel_id, guild_id, votee_id, flavor) VALUES (?, ?, ?, ?, ?, ?)",
                (voter_id, payload.message_id, payload.channel_id, payload.guild_id, votee_id, flavor),
            )
            await send_dm(
                member,
                "Due to your security settings, you'll need to enter your password to vote for "
                + f"{message.author.name}#{message.author.discriminator}.  Please go to "
                + f"http://discord.eigentrust.net/vote?voter={voter_id}&votee={votee_id}"
                + f"&message={payload.message_id}&amount=-1&flavor={urllib.parse.quote(flavor)} to vote.",
            )
            return
        assert r.status_code == 200
        data = json.loads(r.text)
        password = data["password"]
        password_type = data["password_type"]
        expires = int(data["expires"] if data["expires"] else 0)
        if expires - 10 < time.time() and password_type == "session_key":
            # If session key is about to expire, wait for it to expire and recall this funciton.
            # This will make the user be caught by the "Please enter your password" message instead
            # of trying to get this vote in before time runs out.
            await asyncio.sleep(10)
            return await process_add_reaction(self, payload)
        data = {
            "service_name": os.getenv("ETN_SERVICE_NAME"),
            "service_key": os.getenv("ETN_SERVICE_KEY"),
            "to": str(votee_id),
            "from": str(voter_id),
            "password": password,
            "password_type": password_type,
            "flavor": flavor,
            "amount": -1,
        }
        headers = {
            "Content-Type": "application/json",
        }
        r = requests.post("https://www.eigenkarma.net:31415/vote", data=json.dumps(data), headers=headers)
        if r.status_code != 200:
            await send_dm(member, f"Error casting vote: `{r.text}` Error Code: `{r.status_code}`.")
            return
