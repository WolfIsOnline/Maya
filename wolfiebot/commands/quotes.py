"""Quotes commands"""
import random
from typing import List

import hikari
import lightbulb

from wolfiebot.database.database import GuildData

plugin = lightbulb.Plugin("commands.owner")


@plugin.command
@lightbulb.option("user", "Select a member", type=hikari.User, required=False)
@lightbulb.command("quote", "Get a random quote")
@lightbulb.implements(lightbulb.SlashCommand, lightbulb.PrefixCommand)
async def quote(ctx: lightbulb.Context):
    """
    Get a random quote.

    If a user is specified, it retrieves a random quote from that user.
    Otherwise, it retrieves a random quote from all quotes.

    Args:
        ctx (lightbulb.Context): The context object representing the invocation.

    Returns:
        None
    """
    guild_id = ctx.get_guild().id
    user = ctx.options.user
    if user is not None:
        user_quotes = await get_quote_from_user(user_id=user.id, guild_id=guild_id)
        user_quote = await get_random_quote(quotes=user_quotes)
        name = f"<@{user.id}>"
    else:
        wildcard_quote = await get_random_wildcard_quote(guild_id=guild_id)
        quote_user_id = wildcard_quote.get("quote_user_id")
        user_quote = wildcard_quote.get("quote")
        if quote_user_id == -1:
            name = "Anonymous"
        else:
            name = f"<@{quote_user_id}>"

    await ctx.respond(f'"{user_quote}" - {name}')


async def get_quote_from_user(user_id: int, guild_id: int) -> List[str]:
    """
    Retrieves quotes from a specific user within a guild.

    Args:
        user_id (int): The ID of the user.
        guild_id (int): The ID of the guild.

    Returns:
        List[str]: A list of quotes submitted by the user within the guild.
    """
    guild_data = GuildData(guild_id=guild_id)
    quotes = guild_data.retrieve(name="quotes")
    user_quotes = []
    for _quote in quotes:
        if _quote.get("quote_user_id") == user_id:
            user_quotes.append(_quote.get("quote"))
    return user_quotes


async def get_random_wildcard_quote(guild_id: int):
    """
    Retrieves a random quote from the wildcard quotes in a guild.

    Args:
        guild_id (int): The ID of the guild.

    Returns:
        dict: A random wildcard quote from the guild.
    """
    guild_data = GuildData(guild_id=guild_id)
    quotes = guild_data.retrieve(name="quotes")
    _quote = random.choice(quotes)
    return _quote


async def get_random_quote(quotes: List[str]) -> str:
    """
    Retrieves a random quote from the given list of quotes.

    Args:
        quotes (List[str]): A list of quotes.

    Returns:
        str: A random quote from the list.
    """
    _quote = random.choice(quotes)
    return _quote


def load(bot: lightbulb.BotApp) -> None:
    """
    Loads the plugin into the bot.

    Args:
        bot (lightbulb.BotApp): The bot instance.
    """
    bot.add_plugin(plugin)


def unload(bot: lightbulb.BotApp) -> None:
    """
    Unloads the plugin from the bot.

    Args:
        bot (lightbulb.BotApp): The bot instance.
    """
    bot.remove_plugin(plugin)
