from discord.ext import commands
import discord
import dotenv

from os import getenv


intents = discord.Intents.default()
intents.message_content = True  # メッセージの内容を取得する権限


# Botをインスタンス化
bot = commands.Bot(
    command_prefix="$",  # $コマンド名でコマンドを実行できるようになる
    case_insensitive=True,  # コマンドの大文字小文字を区別しない ($hello も $Hello も同じ!)
    intents=intents  # 権限を設定
)


@bot.event
async def on_ready():
    print("Bot is ready!")
    await bot.tree.sync()
    print("Synced")


@bot.tree.command(name="ping", description="Ping!!!")
async def ping(ctx: discord.Interaction):
    sec = round(bot.latency * 1000)
    embed = discord.Embed(
        title="Pong!!",
        description=str(sec) + "ms",
        color=discord.Colour.blue()
    )
    await ctx.response.send_message(embed=embed)


if __name__ == "__main__":
    dotenv.load_dotenv()
    bot.run(getenv("APP_TOKEN"))
