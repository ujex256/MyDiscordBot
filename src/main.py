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


@bot.event
async def on_message(message: discord.Message):
    """メッセージをおうむ返しにする処理"""

    if message.author.bot:  # ボットのメッセージは無視
        return

    await message.reply(message.content)


if __name__ == "__main__":
    dotenv.load_dotenv()
    bot.run(getenv("APP_TOKEN"))
