from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from database import DatabaseManager


def update(database: "DatabaseManager") -> None:
    with database as db:
        db.execute("ALTER TABLE guilds ADD COLUMN admin_roles TEXT DEFAULT '[]'")
        db.execute("UPDATE bot_settings SET value='0.4.0' WHERE setting='version'")
