from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from database import DatabaseManager


def update(database: "DatabaseManager") -> None:
    with database as db:
        db.execute("CREATE TABLE IF NOT EXISTS missed_votes (id INTEGER PRIMARY KEY, count INTEGER)")
        db.execute(
            "CREATE TABLE IF NOT EXISTS pending_votes "
            + "(voter_id INTEGER, message_id INTEGER, channel_id INTEGER, guild_id INTEGER, votee_id INTEGER)"
        )
        db.execute("UPDATE bot_settings SET value='0.3.0' WHERE setting='version'")
