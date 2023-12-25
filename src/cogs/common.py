from discord.ext import commands, tasks
from discord import app_commands
import discord

from random import randint
from datetime import datetime
from datetime import timezone

import db


main_db = db.BotDB.get_default_db()


class CommonComands(commands.Cog):
    def __init__(self, bot: discord.Client):
        self.bot = bot
        self.task_starter()

    def task_starter(self):
        print("roop")
        if self.roop.is_running():
            self.roop.restart()
            print("restarted")
        else:
            self.roop.start()
            print("started")

    def cog_unload(self):
        self.roop.cancel()

    @app_commands.command(name="ping", description="Ping!!!")
    async def ping(self, ctx: discord.Interaction):
        print("sai")
        sec = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="Pong!!",
            description=str(sec) + "ms",
            color=discord.Colour.blue()
        )

        value = datetime.now(timezone.utc) - ctx.created_at
        embed.add_field(name="nowDate-timestamp", value=str(value.microseconds / 1000) + "ms")
        await ctx.response.send_message(embed=embed)

    @app_commands.command(name="random", description="random.randint()")
    async def random(self, ctx: discord.Interaction):
        await ctx.response.send_message(randint(1, 100))

    @app_commands.command(name="add_rta", description="RTAのスケジュールを追加します")
    async def add_rta(
        self,
        ctx: discord.Interaction,
        month: int,
        day: int,
        hour: int,
        minute: int,
        year: int | None = None,
        second: int = 0
    ):
        if not ctx.permissions.administrator:
            embed = discord.Embed(
                title="権限が不足しています",
                description="サーバーの管理権限を持っている人のみが追加できます"
            )
            await ctx.response.send_message(embed=embed, ephemeral=True)
        if year is None:
            year = datetime.today().year
        date = datetime(year, month, day, hour, minute, second)
        main_db.add_rta(date, ctx)
        await ctx.response.send_message("success")

    @tasks.loop(seconds=5)
    async def roop(self):
        ch = self.bot.get_all_channels()
        for i in ch:
            if i.type == discord.ChannelType.text:
                await i.send("headddday")


async def setup(bot: commands.Bot):
    print("Common Comands added")
    await bot.add_cog(CommonComands(bot))


async def teardown(bot: commands.Bot):
    main_db.db.close()
    print("db closed")
