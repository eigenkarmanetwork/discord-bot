from database_migration.update import update_database
import os
import sqlite3
import threading


class DatabaseManager:
    def __init__(self):
        self.path = "database.db"
        self.lock = threading.Lock()
        self.connected = False
        self.conn = None
        self.cur = None
        update_database(self)

    def open(self) -> None:
        self.lock.acquire()
        while not self.connected:
            self._open()

    def _open(self) -> None:
        try:
            if not os.path.isfile(self.path):
                self._create_database()
            self.conn = sqlite3.connect(self.path)
            self.conn.row_factory = sqlite3.Row
            self.cur = self.conn.cursor()
            self.connected = True
        except sqlite3.Error as e:
            print(f"Database Error: {e}")

    def close(self) -> None:
        if self.conn:
            self.conn.commit()
            if self.cur:
                self.cur.close()
            self.conn.close()
        self.conn = None
        self.cur = None
        self.connected = False
        self.lock.release()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def _create_database(self) -> None:
        conn = sqlite3.connect(self.path)
        cur = conn.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS bot_settings (setting TEXT PRIMARY KEY UNIQUE, value TEXT)")
        cur.execute("CREATE TABLE IF NOT EXISTS guilds (id INT PRIMARY KEY UNIQUE, name TEXT, reactions TEXT)")
        conn.commit()
        cur.execute("INSERT INTO bot_settings (setting, value) VALUES ('version', '0.1.0')")
        conn.commit()
        cur.close()
        conn.close()
        print("Created database!")

    def execute(self, sql: str, params=None) -> sqlite3.Cursor:
        if not self.connected:
            raise RuntimeError("Cannot run execute on a closed database!")
        if params:
            return self.cur.execute(sql, params)
        return self.cur.execute(sql)

    def commit(self):
        self.conn.commit()
