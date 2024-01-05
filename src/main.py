from os import getenv
import sys

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
    if len(sys.argv) == 2 and sys.argv[1] == "-n":
        print("skipped")
    else:
        await bot.tree.sync()
        print("Synced")


@bot.event
async def setup_hook():
    await bot.load_extension("cogs.common")
    await bot.load_extension("cogs.generate_image")


@bot.tree.command(name="reload", description="extensionをreload")
async def reload_all(ctx: discord.Interaction, sync: bool):
    if ctx.user.id != int(getenv("ADMIN_ID", 0)):
        await ctx.response.send_message("You are not admin of this bot!!!!!!!!!")
        return

    await bot.reload_extension("cogs.common")
    await bot.reload_extension("cogs.generate_image")
    embed = discord.Embed(
        title="Success*!*",
        description="リロードした",
        color=discord.Colour.blue()
    )
    await ctx.response.send_message(embed=embed)
    if sync:
        await bot.tree.sync()


if __name__ == "__main__":
    dotenv.load_dotenv()
    bot.run(getenv("APP_TOKEN", ""))
    main_db.db.close()
    print("closed")
