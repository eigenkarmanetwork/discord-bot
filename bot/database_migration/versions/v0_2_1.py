from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from database import DatabaseManager


def update(database: "DatabaseManager") -> None:
    with database as db:
        db.execute("ALTER TABLE connections DROP COLUMN username")
        db.execute("UPDATE bot_settings SET value='0.2.1' WHERE setting='version'")
