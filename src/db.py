import sqlite3
from pathlib import Path


def get_db():
    p = Path.cwd()
    if p.name == "src":
        p = p.parent
    db = p.joinpath("db")
    db.mkdir(exist_ok=True)
    return sqlite3.connect(db.joinpath("main.db"))


class BotDB:
    def __init__(self, db: sqlite3.Connection) -> None:
        if not isinstance(db, sqlite3.Connection):
            raise ValueError("Invalid database.")
        self.db = db
