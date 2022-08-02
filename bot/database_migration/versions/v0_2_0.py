from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from database import DatabaseManager


def update(database: "DatabaseManager") -> None:
    with database as db:
        db.execute("CREATE TABLE IF NOT EXISTS pending_connections (id INTEGER PRIMARY KEY UNIQUE, nonce TEXT, expires INTEGER)")
        db.execute("CREATE TABLE IF NOT EXISTS connections (id INTEGER PRIMARY KEY UNIQUE, username TEXT, key TEXT, key_type TEXT, expires INTEGER)")
        db.execute("UPDATE bot_settings SET value='0.2.0' WHERE setting='version'")
