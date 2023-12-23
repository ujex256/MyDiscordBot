import discord

import sqlite3
from datetime import datetime
from textwrap import dedent
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
    cur.execute(dedent(
        """
        CREATE TABLE IF NOT EXISTS rta_db(
            guild_id INTEGER,
            channel_id INTEGER,
            user_id INTEGER,
            date TEXT,
            created_at TEXT
        ) STRICT;
        """
    ))
    db.commit()


class BotDB:
    def __init__(self, db: sqlite3.Connection) -> None:
        if not isinstance(db, sqlite3.Connection):
            raise ValueError("Invalid database.")
        self.db = db
        init_db(self.db)

    @classmethod
    def get_default_db(cls):
        return cls(get_db())

    def add_rta(self, date: str | datetime, interaction: discord.Interaction):
        if isinstance(date, str):
            date = datetime.fromisoformat(date)

        cur = self.db.cursor()
        print(date.isoformat())
        cur.execute(
            dedent(
                """
                INSERT INTO rta_db
                VALUES (?,?,?,?,?)
                """
            ),
            (
                interaction.guild_id,
                interaction.channel_id,
                interaction.user.id,
                date.isoformat(),
                interaction.created_at.isoformat(),
            ),
        )
        self.db.commit()

    def get_rta(self):
        cur = self.db.cursor()
        cur.execute("SELECT * FROM rta_db")
        d = cur.fetchall()
        cur.close()
        return d


if __name__ == "__main__":
    d = BotDB(get_db())
    print(d.get_rta())
    d.db.close()
