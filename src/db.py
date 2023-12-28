import discord

import sqlite3
from datetime import datetime
from textwrap import dedent
from pathlib import Path
from enum import Enum
from contextlib import closing


def get_db():
    p = Path.cwd()
    if p.name == "src":
        p = p.parent
    elif p.name == "cogs":
        p = p.parent.parent
    db = p.joinpath("db")
    db.mkdir(exist_ok=True)
    return sqlite3.connect(db.joinpath("main.sqlite"))


def init_db(db: sqlite3.Connection):
    cur = db.cursor()
    cur.execute(
        dedent(
            """
        CREATE TABLE IF NOT EXISTS rta_db(
            channel_id INTEGER,
            user_id INTEGER,
            date TEXT,
            created_at TEXT
        ) STRICT;
        """
        )
    )
    db.commit()


class SortType(Enum):
    ASC = "ASC"
    DESC = "DESC"


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
        if interaction.channel_id is None:
            cur.close()
            raise ValueError("channel_id is None")
        cur.execute(
            dedent(
                """
                INSERT INTO rta_db
                VALUES (?,?,?,?)
                """
            ),
            (
                interaction.channel_id,
                interaction.user.id,
                date.isoformat(),
                interaction.created_at.isoformat(),
            ),
        )
        cur.close()
        self.db.commit()

    def get_all_rta(self, sort_type: SortType = SortType.ASC):
        return self._get_rta(sort_type=sort_type)

    def get_all_rta_iter(self, sort_type: SortType = SortType.ASC):
        return self._get_rta(sort_type=sort_type, iter=True)

    def get_rta(self, channel_id: int, sort_type: SortType = SortType.ASC):
        return self._get_rta(channel_id, sort_type)

    def _get_rta(
        self,
        channel_id: int | None = None,
        sort_type: SortType = SortType.ASC,
        iter: bool = False
    ):
        # なんかキモい
        if not (
            isinstance(sort_type, SortType)
            and isinstance(channel_id, int) or channel_id is None
        ):
            raise ValueError("SQLインジェクションやめて!!!")

        where = ""
        if channel_id is not None:
            where = f"WHERE channel_id={channel_id} "

        with closing(self.db.cursor()) as cur:
            cur.execute(f"SELECT * FROM rta_db {where}ORDER BY date {sort_type.value};")
            return (yield from cur) if iter else cur.fetchall()


if __name__ == "__main__":
    d = BotDB(get_db())
    print(d.get_all_rta(SortType.ASC))
    d.db.close()
