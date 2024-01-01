import math
import re
import datetime as dt
from random import randint

import aiohttp
import discord
import yarl
from discord import app_commands as ac
from discord.ext import commands, tasks
from discord.ext.commands import Bot

import db

main_db = db.BotDB.get_default_db()


class CommonCommands(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @ac.command(name="ping", description="Ping!!!")
    async def ping(self, ctx: discord.Interaction):
        sec = round(self.bot.latency * 1000)
        embed = discord.Embed(
            title="Pong!!", description=str(sec) + "ms", color=discord.Colour.blue()
        )

        value = dt.datetime.now(dt.timezone.utc) - ctx.created_at
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

        header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}  # NOQA
        try:
            async with aiohttp.ClientSession(headers=header) as session:
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


class RTACog(commands.Cog):
    jst = dt.timezone(dt.timedelta(hours=9))

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.receiving = []
        self.receiving_ch = []

        now = dt.datetime.utcnow().time()
        start = now.replace(
            second=(now.second - now.second % 5) + 5,
            microsecond=0,
        )
        self.task_starter.change_interval(time=start)
        self.task_starter.count = 1
        self.task_starter.start()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        ch_id = message.channel.id
        if ch_id not in self.receiving_ch or message.author.bot:
            return
        rta = main_db.get_rta(self.receiving[self.receiving_ch.index(ch_id)])[0]
        rta_date = dt.datetime.fromtimestamp(rta["date"], tz=dt.UTC)
        diff = rta_date - message.created_at
        time_diff = round(diff.total_seconds(), 3)

        embed = discord.Embed(
            title="結果", description=f"{time_diff}秒の差"
        )
        uid = message.author.id
        high_sc = main_db.get_high_score(rta["id"], user_id=uid, absolute=True)

        if high_sc is None or high_sc > abs(time_diff):
            main_db.append_ranking(rta["id"], uid, time_diff)
            embed.title = "記録更新"
        await message.reply(embed=embed)

    def cog_unload(self):
        self.check_rta.cancel()

    @tasks.loop()
    async def task_starter(self):
        print("今の時間は", dt.datetime.now(tz=self.jst))
        self.check_rta.start()
        self.task_starter.stop()

    @tasks.loop(seconds=5)
    async def check_rta(self):
        for i in main_db.get_all_rta_iter():
            time = dt.datetime.fromtimestamp(i["date"])
            dur = time - dt.datetime.utcnow()
            time_diff = math.floor(dur.total_seconds())
            if time_diff > 15:
                continue

            ch = self.bot.get_channel(i["channel_id"])
            if not isinstance(ch, discord.TextChannel):
                raise Exception

            # 終了後の時
            if time_diff <= -15:
                embed = discord.Embed(title="終わった *!!!*")
                try:
                    self.receiving.remove(i["id"])
                    self.receiving_ch.remove(i["channel_id"])
                except ValueError:
                    pass
                main_db.delete_rta(i["id"])
                embed2 = discord.Embed(title="ランキング", color=discord.Color.blue())
                for j, k in enumerate(main_db.get_ranking(i["id"])):
                    embed2.add_field(
                        name=f"{j+1}位 <@!{k['user_id']}>",
                        value=f"{k['diff']}秒"
                    )
                await ch.send(embeds=[embed, embed2])
                return

            # 30秒前の時
            if i["id"] in self.receiving:
                continue
            embed = discord.Embed(
                title="RTA開始",
                description=f"設定された時刻は<t:{int(i['date'])}>です")
            self.receiving.append(i["id"])
            self.receiving_ch.append(i["channel_id"])
            await ch.send(embed=embed)

    @ac.command(name="add_rta", description="RTAのスケジュールを追加します")
    @ac.guild_only()
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
        if year is None:
            year = dt.datetime.today().year

        date = dt.datetime(year, month, day, hour, minute, second, tzinfo=self.jst)
        diff = date - dt.datetime.now(tz=dt.UTC)
        if diff.total_seconds() < 20:
            embed = discord.Embed(
                title="エラー！", description="もっと遅い時間にして",
                color=discord.Color.red()
            )
        elif main_db.get_near_rta(int(date.timestamp()), ctx.channel_id):  # type: ignore
            embed = discord.Embed(
                title="エラー!", description="時間が被っています",
                color=discord.Color.red()
            )
        else:
            main_db.add_rta(date, ctx)
            embed = discord.Embed(
                title="設定しました",
                description=f"<t:{int(date.timestamp())}:f>に設定しました",
                color=discord.Color.blue()
            )
        await ctx.response.send_message(embed=embed)

    @ac.command(name="get_rta", description="設定されたスケジュールを表示")
    @ac.describe(sort="ソートの順番")
    @ac.choices(
        sort=[ac.Choice(name="昇順", value="ASC"), ac.Choice(name="降順", value="DESC")]
    )
    @ac.guild_only()
    async def get_rta(self, ctx: discord.Interaction, sort: str):
        sort_type = db.SortType(sort)
        if ctx.channel_id is None:
            raise

        all_rta = main_db.get_all_rta(sort_type=sort_type)
        data = filter(lambda x: x["guild_id"] == ctx.guild_id, all_rta)
        resp = discord.Embed(title="このサーバーでの結果", colour=discord.Colour.blurple())
        for i, j in enumerate(data):
            date = int(j["date"])
            ch = j["channel_id"]
            resp.add_field(name=f"{i+1}. <#{ch}>", value=f"<t:{date}:f>")
        await ctx.response.send_message(embed=resp)


async def setup(bot: Bot):
    print("Common Commands added")
    await bot.add_cog(CommonCommands(bot))
    await bot.add_cog(RTACog(bot))


async def teardown(bot: Bot):
    main_db.db.close()
    print("db closed")
