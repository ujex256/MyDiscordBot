from os import getenv

import discord
import dotenv
from discord.ext import commands

import db

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", case_insensitive=True, intents=intents)
main_db = db.BotDB.get_default_db()


@bot.event
async def on_ready():
    print("Bot is ready!")
    await bot.tree.sync()
    print("Synced")


@bot.event
async def setup_hook():
    await bot.load_extension("cogs.common")


@bot.tree.command(name="reload", description="extensionをreload")
async def reload_all(ctx: discord.Interaction):
    await bot.reload_extension("cogs.common")
    embed = discord.Embed(title="Success*!*", description="リロードした")
    await ctx.response.send_message(embed=embed)


if __name__ == "__main__":
    dotenv.load_dotenv()
    bot.run(getenv("APP_TOKEN", ""))
    main_db.db.close()
    print("closed")
