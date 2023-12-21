import sqlite3
from pathlib import Path


def get_db():
    p = Path.cwd()
    if p.name == "src":
        p = p.parent
    db = p.joinpath("db")
    db.mkdir(exist_ok=True)
    return sqlite3.connect(db.joinpath("main.sqlite"))


def init_db(db: sqlite3.Connection):
    cur = db.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS rta_db(
            guild_id INTEGER,
            channel_id INTEGER,
            user_id INTEGER,
            date TEXT,
            created_at TEXT
        ) STRICT;
        """
    )
    db.commit()


class BotDB:
    def __init__(self, db: sqlite3.Connection) -> None:
        if not isinstance(db, sqlite3.Connection):
            raise ValueError("Invalid database.")
        self.db = db
        init_db(self.db)


if __name__ == "__main__":
    BotDB(get_db())
