"""Logging server events"""
import hikari
import lightbulb
import pytz

from wolfiebot.database.database import GuildData

plugin = lightbulb.Plugin("core.logs")

TIME_FORMAT = "%b %m, %Y @ %I:%M:%S%p %Z"
TIMEZONE = "America/New_york"
REMOVE_COLOR = 0xFFFFFF
ADDITION_COLOR = 0x2ECC71
CHANGE_COLOR = 0x1ABC9C
IMPORTANT_COLOR = 0xE74C3C


@plugin.listener(hikari.MemberCreateEvent)
async def member_join(event) -> None:
    """
    Handles the member join event.

    Args:
        event: The member join event.

    Returns:
        None
    """
    member = event.user
    guild_id = event.guild_id
    creation_date = member.created_at.astimezone(pytz.timezone(TIMEZONE)).strftime(
        TIME_FORMAT
    )
    embed = hikari.Embed(
        color=ADDITION_COLOR, title="Member Joined", description=f"{member} joined"
    )
    embed.set_author(name=f"{member}", icon=member.display_avatar_url)
    embed.add_field(name="Account created", value=creation_date)
    embed.set_footer(text=f"Account ID: {member.id}")
    log_channel = GuildData(guild_id=guild_id).retrieve(name="logs_channel")
    await plugin.bot.rest.create_message(log_channel, embed)


@plugin.listener(hikari.MemberDeleteEvent)
async def member_leave(event) -> None:
    """
    Handles the member leave event.

    Args:
        event: The member leave event.

    Returns:
        None
    """
    member = event.user
    guild_id = event.guild_id
    try:
        await event.app.rest.fetch_ban(guild_id, member)
        return
    except hikari.errors.NotFoundError:
        pass
    embed = hikari.Embed(
        color=REMOVE_COLOR, title="Member Left", description=f"{member} has left"
    )
    embed.set_author(name=f"{member}", icon=member.display_avatar_url)
    embed.set_footer(text=f"Account ID: {member.id}")
    log_channel = GuildData(guild_id=guild_id).retrieve(name="logs_channel")
    await plugin.bot.rest.create_message(log_channel, embed)


@plugin.listener(hikari.GuildMessageUpdateEvent)
async def member_edit(event) -> None:
    """
    Handles the member edit event.

    Args:
        event: The member edit event.

    Returns:
        None
    """
    try:
        if event.author or event.author.is_bot is True:
            return
    except AttributeError:
        return

    member = event.author

    guild_id = event.guild_id
    embed = hikari.Embed(color=CHANGE_COLOR, title="Message Edited")
    embed.add_field("Original:", event.old_message.content)
    embed.add_field("New:", event.message.content)
    embed.set_author(name=f"{member}", icon=member.display_avatar_url)
    embed.set_footer(text=f"Message ID: {event.message.id}")
    log_channel = GuildData(guild_id=guild_id).retrieve(name="logs_channel")
    await plugin.bot.rest.create_message(log_channel, embed)


@plugin.listener(hikari.GuildMessageDeleteEvent)
async def member_delete(event) -> None:
    """
    Handles the member delete event.

    Args:
        event: The member delete event.

    Returns:
        None
    """
    if event.old_message is None or event.old_message.author.is_bot is True:
        return

    member = event.old_message.author
    guild_id = event.guild_id
    embed = hikari.Embed(
        color=REMOVE_COLOR,
        title="Message Deleted",
        description=event.old_message.content,
    )
    embed.add_field("Channel:", f"<#{event.channel_id}>")
    embed.set_author(name=f"{member}", icon=member.display_avatar_url)
    embed.set_footer(text=f"Message ID: {event.old_message.id}")
    log_channel = GuildData(guild_id=guild_id).retrieve(name="logs_channel")
    await plugin.bot.rest.create_message(log_channel, embed)


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
