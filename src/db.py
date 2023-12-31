import discord

import sqlite3
from datetime import datetime
from textwrap import dedent
from pathlib import Path
from enum import Enum
from contextlib import closing

import utils


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
    cur.execute(dedent(
        """
        CREATE TABLE IF NOT EXISTS rta_db(
            id INTEGER PRIMARY KEY,
            guild_id INTEGER,
            channel_id INTEGER,
            created_user INTEGER,
            date REAL,
            created_at INTEGER
        ) STRICT;
        """
    ))
    cur.execute(dedent(
        """
        CREATE TABLE IF NOT EXISTS rta_ranking(
            id INTEGER,
            user_id INTEGER,
            diff REAL
        ) STRICT;
        """
    ))
    db.commit()
    db.row_factory = sqlite3.Row


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
        if interaction.channel_id is None:
            raise ValueError("channel_id is None")

        cur = self.db.cursor()
        id = utils.generate_secure_id(10)
        print(date.isoformat())
        cur.execute(
            dedent(
                """
                INSERT INTO rta_db
                VALUES (?,?,?,?,?,?);
                """
            ),
            (
                id,
                interaction.guild_id,
                interaction.channel_id,
                interaction.user.id,
                date.timestamp(),
                int(interaction.created_at.timestamp()),
            ),
        )
        cur.close()
        self.db.commit()
        return id

    def get_all_rta(self, sort_type: SortType = SortType.ASC) -> list[sqlite3.Row]:
        return list(self._get_rta(sort_type=sort_type))

    def get_all_rta_iter(self, sort_type: SortType = SortType.ASC):
        yield from self._get_rta(sort_type=sort_type)

    def get_rta(
        self,
        id: int | None = None,
        channel_id: int | None = None,
        timestamp: int | None = None,
        sort_type: SortType = SortType.ASC,
    ):
        return list(self._get_rta(id, channel_id, timestamp, sort_type))

    def get_near_rta(self, date: int, channel_id: int):
        if not (isinstance(date, int) and isinstance(channel_id, int)):
            raise ValueError("SQLインジェクションやめてね")
        with closing(self.db.cursor()) as cur:
            min_t = date - 60
            max_t = date + 60
            cur.execute(
                dedent(
                    """
                    SELECT * FROM rta_db
                    WHERE date >= ? AND date <= ? AND channel_id = ?;
                    """
                ),
                (min_t, max_t, channel_id),
            )
            return cur.fetchall()

    def _get_rta(
        self,
        id: int | None = None,
        channel_id: int | None = None,
        timestamp: int | None = None,
        sort_type: SortType = SortType.ASC,
    ):
        # なんかキモい
        if not (
            isinstance(sort_type, SortType)
            and (isinstance(id, int) or id is None)
            and (isinstance(timestamp, int) or timestamp is None)
            and (isinstance(channel_id, int) or channel_id is None)
        ):
            raise ValueError("SQLインジェクションやめて!!!")

        where = ""
        if id or channel_id or timestamp:
            where = "WHERE "
        argmap = ["id", "channel_id", "date"]
        for i, j in enumerate([id, channel_id, timestamp]):
            if j is None:
                continue
            where = where + f"{argmap[i]}={j} "
        if where:
            print(where)

        with closing(self.db.cursor()) as cur:
            cur.execute(f"SELECT * FROM rta_db {where}ORDER BY date {sort_type.value};")
            yield from cur

    def delete_rta(self, id: int):
        if not isinstance(id, int):
            raise ValueError
        cur = self.db.cursor()
        cur.execute("DELETE FROM rta_db WHERE id = ?", (id,))
        cur.close()
        self.db.commit()
        return True

    def append_ranking(self, id: int, user_id: int, time: float):
        if not self.get_rta(id):
            raise ValueError("そのidは存在しなかった")
        cur = self.db.cursor()
        cur.execute("SELECT * FROM rta_ranking WHERE id = ? AND user_id = ?;", (id, user_id))
        existing_row = cur.fetchone()

        if existing_row:
            # 存在する場合はUPDATE文で置き換える
            cur.execute(
                "UPDATE rta_ranking SET diff = ? WHERE id = ? AND user_id = ?;",
                (time, id, user_id),
            )
        else:
            # 存在しない場合は挿入
            cur.execute(
                "INSERT INTO rta_ranking VALUES (?, ?, ?);",
                (id, user_id, time)
            )

        cur.close()
        self.db.commit()

    def get_ranking(self, id: int):
        if not isinstance(id, int):
            raise ValueError
        cur = self.db.cursor()
        cur.execute(
            "SELECT user_id, diff FROM rta_ranking WHERE id = ? ORDER BY ABS(diff)",
            (id,)
        )
        d = cur.fetchall()
        cur.close()
        return d

    def get_high_score(self, rta_id: int, user_id: int, absolute: bool = False):
        if not (isinstance(rta_id, int) and isinstance(user_id, int)):
            raise ValueError
        cur = self.db.cursor()
        cur.execute(
            "SELECT diff FROM rta_ranking WHERE id = ? AND user_id = ?;",
            (rta_id, user_id),
        )
        d = cur.fetchone()
        cur.close()
        if absolute and d is not None:
            return abs(d["diff"])
        if d is not None:
            return d["diff"]


if __name__ == "__main__":
    d = BotDB.get_default_db()
    # a = d.get_high_score()
    a = d.get_all_rta()
    print(a)
    d.db.close()
