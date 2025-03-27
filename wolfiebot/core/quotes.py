"""Controls the quotes"""
import re
import hikari

import lightbulb
import wolfiebot

from wolfiebot.database.database import GuildData

plugin = lightbulb.Plugin("core.quotes")


def validate(quote) -> bool:
    """
    Validates a quote by checking if it is not empty or consists only of whitespace.

    Args:
        quote (str or list): The quote to be validated.
            If a list is provided, the first element is used.

    Returns:
        bool: True if the quote is valid (not empty or whitespace-only),
            False otherwise.
    """
    if quote:
        quote = quote[0]
        if quote == "" or quote.isspace():
            return False
        return True
    return False


def is_unknown(quote_user_id) -> bool:
    """
    Checks if the quote user ID is unknown.

    Args:
        quote_user_id (any): The quote user ID to be checked.

    Returns:
        bool: True if the quote user ID is unknown (empty or evaluates to False),
            False otherwise.
    """
    if quote_user_id:
        return False
    return True


async def commit(content, author_id, guild_id, quote_id, ctx=None) -> None:
    """
    Commits a quote to the database and sends an embed message.

    Args:
        content (str): The content containing the quote.
        author_id (int): The ID of the author.
        guild_id (int): The ID of the guild.
        quote_id (int): The ID of the quote.
        ctx (Optional[hikari.CommandContext]): The command context (default: None).
    """

    quote = re.split('"|“|”', content)[1::2]
    quote_user_id = re.split("<@|>", content)[1::2]

    if validate(quote) is True:
        quote = quote[0]
        submitted_user = await plugin.bot.rest.fetch_user(author_id)
        if is_unknown(quote_user_id) is False:
            quote_user_id = quote_user_id[0]
            quote_user = await plugin.bot.rest.fetch_user(quote_user_id)
            desc_format = quote_user.mention
        else:
            quote_user = "Unknown"
            quote_user_id = -1
            desc_format = "Unknown"
    else:
        return

    guild_data = GuildData(guild_id=guild_id)
    guild_data.append(
        name="quotes",
        value={
            "quote": quote,
            "quote_user_id": int(quote_user_id),
            "quote_user": str(quote_user),
            "submitted_user": str(submitted_user),
            "submitted_user_id": author_id,
            "quote_id": quote_id,
        },
    )
    total_quotes = len(guild_data.retrieve(name="quotes"))
    embed = hikari.Embed(
        title="Quote Added",
        description=f'"{quote}" - {desc_format}',
        color=wolfiebot.DEFAULT_COLOR,
    )

    embed.set_author(name=f"Quote #{total_quotes}")
    quotes_channel = guild_data.retrieve(name="quotes_channel")
    if ctx is None:
        await plugin.bot.rest.create_message(quotes_channel, embed)
    else:
        await ctx.respond(embed)


@plugin.listener(hikari.GuildMessageCreateEvent)
async def listen(event):
    """
    Listens for guild message create events and commits quotes if conditions are met.

    Args:
        event (hikari.GuildMessageCreateEvent): The guild message create event.

    Returns:
        None

    Raises:
        None
    """
    channel_id = GuildData(event.guild_id).retrieve(name="quotes_channel")
    if event.channel_id != channel_id or event.is_bot is True:
        return
    if not event.content.startswith('"') and not event.content.startswith("“"):
        return
    await commit(
        content=event.content,
        author_id=event.author_id,
        guild_id=event.guild_id,
        quote_id=event.message.id,
    )


def load(bot: lightbulb.BotApp) -> None:
    """
    Loads the plugin into the bot.

    Args:
        bot (lightbulb.BotApp): The bot instance.

    Returns:
        None
    """
    bot.add_plugin(plugin)


def unload(bot: lightbulb.BotApp) -> None:
    """
    Unloads the plugin from the bot.

    Args:
        bot (lightbulb.BotApp): The bot instance.

    Returns:
        None
    """
    bot.remove_plugin(plugin)
