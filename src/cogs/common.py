import re
from datetime import datetime, timezone
from random import randint

import aiohttp
import discord
import yarl
from discord import app_commands as ac
from discord.ext import commands, tasks
from discord.ext.commands import Bot

import db

main_db = db.BotDB.get_default_db()


class CommonComands(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.task_starter()

    def task_starter(self):
        self.check_rta.start()

    def cog_unload(self):
        self.check_rta.cancel()

    @ac.command(name="ping", description="Ping!!!")
    async def ping(self, ctx: discord.Interaction):
        sec = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="Pong!!", description=str(sec) + "ms", color=discord.Colour.blue()
        )

        value = datetime.now(timezone.utc) - ctx.created_at
        embed.add_field(
            name="nowDate-timestamp", value=str(value.microseconds / 1000) + "ms"
        )
        await ctx.response.send_message(embed=embed)

    @ac.command(name="random", description="random.randint()")
    async def random(self, ctx: discord.Interaction):
        await ctx.response.send_message(randint(1, 100))

    @ac.command(name="extract_url", description="短縮URLを展開します")
    async def extract_url(self, ctx: discord.Interaction, url: str):
        if not re.match(r".*://", url):
            url = "https://" + url

        async def validate(url):
            IP_REGEX = r"^((25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])$"  # NOQA
            try:
                parsed = yarl.URL(url)
            except ValueError:
                return False
            return (
                parsed.host is not None
                and parsed.scheme in ("http", "https")
                and parsed.host != "localhost"
                and not re.match(IP_REGEX, parsed.host)
            )

        if not await validate(url):
            embed = discord.Embed(title="失敗", description="無効なURLかIPアドレスで指定されています")
            await ctx.response.send_message(embed=embed)
            return

        try:
            async with aiohttp.ClientSession() as session:
                async with session.head(url, allow_redirects=True) as resp:
                    history = list(map(lambda x: x.url, resp.history)) + [resp.url]
                    status = resp.status
        except Exception:
            embed = discord.Embed(title="エラー！", description="リクエストに失敗した")
            await ctx.response.send_message(embed=embed)
            return

        if len(history) == 1:
            embed = discord.Embed(title="結果", description="リダイレクトは無かった")
        else:
            desc = [f"{ind+1}. {url}" for ind, url in enumerate(history)]
            embed = discord.Embed(title="結果", description="\n".join(desc))
            embed.set_footer(text=f"ステータスコード: {status}")
        await ctx.response.send_message(embed=embed)

    @ac.command(name="add_rta", description="RTAのスケジュールを追加します")
    async def add_rta(
        self,
        ctx: discord.Interaction,
        month: int,
        day: int,
        hour: int,
        minute: int,
        year: int | None = None,
        second: int = 0,
    ):
        if not ctx.permissions.administrator:
            embed = discord.Embed(
                title="権限が不足しています", description="サーバーの管理権限を持っている人のみが追加できます"
            )
            await ctx.response.send_message(embed=embed, ephemeral=True)
            return
        if year is None:
            year = datetime.today().year
        date = datetime(year, month, day, hour, minute, second)
        main_db.add_rta(date, ctx)
        await ctx.response.send_message("success")

    @ac.command(name="get_rta", description="設定されたスケジュールを表示")
    @ac.describe(sort="ソートの順番")
    @ac.choices(
        sort=[ac.Choice(name="昇順", value="ASC"), ac.Choice(name="降順", value="DESC")]
    )
    async def get_rta(self, ctx: discord.Interaction, sort: str):
        sort_type = db.SortType(sort)
        if ctx.channel_id is None:
            raise
        data = main_db.get_rta(ctx.channel_id, sort_type)
        resp = discord.Embed(title="このサーバーでの結果", description="aaaa")
        await ctx.response.send_message(embed=resp)

    @tasks.loop(seconds=5)
    async def check_rta(self):
        ch = self.bot.get_all_channels()
        for i in ch:
            if i.type == discord.ChannelType.text:
                pass


async def setup(bot: Bot):
    print("Common Comands added")
    await bot.add_cog(CommonComands(bot))


async def teardown(bot: Bot):
    main_db.db.close()
    print("db closed")
