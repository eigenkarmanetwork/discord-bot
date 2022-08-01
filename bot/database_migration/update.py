"""from database_migration.versions import (
    v0_1_0,
)
"""
from typing import TYPE_CHECKING
import warnings

if TYPE_CHECKING:
    from database import DatabaseManager

main_database_versions = {
    "0.1.0": None,
}


def update_database(database: "DatabaseManager") -> None:
    version = get_version(database)
    versions = list(main_database_versions.keys())
    if version not in versions:
        warnings.warn(f"Database version {version} doesn't exist in dictionary", Warning)
        return
    index = versions.index(version)
    for v in versions[index + 1 :]:
        print(f"Updating database from v{version} to v{v}")
        if main_database_versions[v]:  # If not None
            main_database_versions[v](database)  # type: ignore


def get_version(database: "DatabaseManager") -> str:
    with database as db:
        result = db.execute("SELECT value FROM bot_settings WHERE setting='version'")
        value = result.fetchone()
        return value["value"]
