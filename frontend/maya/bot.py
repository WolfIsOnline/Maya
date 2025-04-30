import asyncio
import discord
import requests

from dotenv import load_dotenv, find_dotenv

import maya
from maya.core.logs import log

load_dotenv(find_dotenv())

bot = discord.Bot(debug_guilds=[maya.DEBUG_GUILD], owner_id=int(maya.OWNER_ID))

extensions = ["user", "polls", "dev"]
for ext in extensions:
    bot.load_extension(f"maya.extensions.{ext}")


@bot.event
async def on_ready():
    """Called when bot is ready"""
    log.info("%s ready....", (bot.user))
    log.info("-----------")


@bot.event
async def on_guild_join(guild: discord.Guild):
    """Add guild id to database when bot joins a guild

    Args:
        guild (discord.Guild): guild object
    """
    request = requests.post(
        url=f"{maya.BACKEND_URL}/guilds",
        json={"guild_id": guild.id},
        timeout=10,
    )
    log.info("Content: %s, Status: %s", request.content, request.status_code)
    log.info("%s joined %s (%s)", bot.user, guild.name, guild.id)


@bot.event
async def on_guild_remove(guild: discord.Guild):
    """Log when bot leaves server, probably not a good idea to remove guild from database

    Args:
        guild (discord.Guild): _description_
    """
    log.info("%s left %s (%s)", bot.user, guild.name, guild.id)


async def main():
    """Start maya"""
    async with bot:
        await bot.start(maya.DISCORD_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
