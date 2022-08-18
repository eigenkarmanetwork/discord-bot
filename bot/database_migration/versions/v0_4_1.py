from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from database import DatabaseManager


def update(database: "DatabaseManager") -> None:
    with database as db:
        db.execute("ALTER TABLE pending_votes ADD COLUMN flavor TEXT")
        db.execute("UPDATE bot_settings SET value='0.4.1' WHERE setting='version'")
