from discord.ext import commands
from discord import app_commands
import discord
import dotenv

from random import randint
from datetime import datetime
from datetime import timezone
from os import getenv


intents = discord.Intents.default()
intents.message_content = True


bot = commands.Bot(
    command_prefix="",
    case_insensitive=True,
    intents=intents
)


@bot.event
async def on_ready():
    print("Bot is ready!")
    await bot.add_cog(CommonComands(bot))
    await bot.tree.sync()
    print("Synced")


class CommonComands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Ping!!!")
    async def ping(self, ctx: discord.Interaction):
        sec = round(bot.latency * 1000)
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
    async def add_rta(self, ctx: discord.Interaction):
        if not ctx.permissions.administrator:
            embed = discord.Embed(
                title="権限が不足しています",
                description="サーバーの管理権限を持っている人のみが追加できます"
            )
            await ctx.response.send_message(embed=embed, ephemeral=True)


if __name__ == "__main__":
    dotenv.load_dotenv()
    bot.run(getenv("APP_TOKEN"))
