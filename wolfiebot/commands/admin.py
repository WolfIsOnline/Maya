"""
Admin Commands
"""
import hikari
import lightbulb
from hikari.permissions import Permissions

import wolfiebot
from wolfiebot.database.database import GuildData

plugin = lightbulb.Plugin("commands.admin")


@plugin.command
@lightbulb.command("admin", "Admin commands")
@lightbulb.implements(lightbulb.PrefixCommandGroup, lightbulb.SlashCommandGroup)
async def admin(ctx: lightbulb.Context) -> None:
    """
    Admin group

    Args:
        ctx (lightbulb.Context): The command context.

    Returns:
        None
    """
    return None


@admin.child
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.command("set", "Set commands")
@lightbulb.implements(lightbulb.PrefixSubGroup, lightbulb.SlashSubGroup)
# pylint: disable=unused-argument
async def _set(ctx: lightbulb.Context):
    """
    Set group within the "Admin" group

    Args:
        ctx (lightbulb.Context): The command context.

    Returns:
        None
    """
    return None


@admin.child
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.command("lock", "Lock channel")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def _lock(ctx: lightbulb.Context) -> None:
    """
    Locks the channel where the command is invoked.

    Args:
        ctx (lightbulb.Context): The command context.

    Returns:
        None
    """
    channel_id = ctx.channel_id
    await plugin.bot.rest.edit_channel(
        channel_id,
        permission_overwrites=[
            hikari.channels.PermissionOverwrite(
                id=ctx.guild_id,
                type=hikari.channels.PermissionOverwriteType.ROLE,
                deny=(Permissions.SEND_MESSAGES),
            )
        ],
    )
    await ctx.respond(
        notify(f"{ctx.get_channel().mention} locked! :closed_lock_with_key:")
    )


@admin.child
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.command("unlock", "Unlock channel")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def _unlock(ctx: lightbulb.Context) -> None:
    """
    Unlocks the channel where the command is invoked.

    Args:
        ctx (lightbulb.Context): The command context.

    Returns:
        None
    """
    channel_id = ctx.channel_id
    await plugin.bot.rest.edit_channel(
        channel_id,
        permission_overwrites=[
            hikari.channels.PermissionOverwrite(
                id=ctx.guild_id,
                type=hikari.channels.PermissionOverwriteType.ROLE,
                allow=(Permissions.SEND_MESSAGES),
            )
        ],
    )
    await ctx.respond(notify(f"{ctx.get_channel().mention} unlocked! :unlock:"))


@_set.child
@lightbulb.option("channel", "Text channel", type=hikari.TextableChannel, required=True)
@lightbulb.command("quotes", "Set quotes channel")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def quotes(ctx: lightbulb.Context) -> None:
    """
    Sets the quotes channel for the guild.

    Args:
        ctx (lightbulb.Context): The command context.

    Returns:
        None
    """
    channel = ctx.options.channel
    guild_data = GuildData(guild_id=ctx.get_guild().id)
    guild_data.edit(name="quotes_channel", value=channel.id)
    await ctx.respond(notify(f"Quotes channel set to {channel.mention}"))


@_set.child
@lightbulb.option(
    "channel", "Voice channel", type=hikari.GuildVoiceChannel, required=True
)
@lightbulb.command("room", "Set parent room channel")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def room(ctx: lightbulb.Context) -> None:
    """
    Sets the parent room channel for automatic room creation.

    Args:
        ctx (lightbulb.Context): The command context.

    Returns:
        None
    """
    channel = ctx.options.channel
    guild_data = GuildData(guild_id=ctx.get_guild().id)
    guild_data.edit(name="autoroom_parent", value=channel.id)
    await ctx.respond(notify(f"Parent channel set to {channel.mention}"))


@_set.child
@lightbulb.option("channel", "Text channel", type=hikari.TextableChannel, required=True)
@lightbulb.command("logs", "Set logs channel")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def logs(ctx: lightbulb.Context) -> None:
    """
    Sets the logs channel.

    Args:
        ctx (lightbulb.Context): The command context.

    Returns:
        None
    """
    channel = ctx.options.channel
    guild_data = GuildData(guild_id=ctx.get_guild().id)
    guild_data.edit(name="logs_channel", value=channel.id)
    await ctx.respond(notify(f"Logs channel set to {channel.mention}"))


@_set.child
@lightbulb.option(
    "channel", "Select the welcome channel", type=hikari.TextableChannel, required=True
)
@lightbulb.command("welcome", "Set the welcome channel")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def welcome(ctx: lightbulb.Context) -> None:
    """
    Sets the welcome channel for new member greetings.

    Args:
        ctx (lightbulb.Context): The command context.

    Returns:
        None
    """
    channel = ctx.options.channel
    guild_data = GuildData(guild_id=ctx.get_guild().id)
    guild_data.edit(name="welcome_channel", value=channel.id)
    await ctx.respond(notify(f"Welcome channel set to {channel.mention}"))


@admin.child
@lightbulb.option("message_id", "Input the message ID", type=str, required=True)
@lightbulb.command("savequote", "Saves quote from message ID")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def save_quote(ctx: lightbulb.Context) -> None:
    """
    Saves a quote from a specific message ID.

    Args:
        ctx (lightbulb.Context): The command context.

    Returns:
        None
    """
    message = await plugin.bot.rest.fetch_message(
        ctx.channel_id, ctx.options.message_id
    )
    # pylint: disable=no-member
    await wolfiebot.core.quotes.commit(
        message.content, message.author.id, ctx.get_guild().id, ctx
    )


@admin.child
@lightbulb.option("role", "Select the role", type=hikari.Role)
@lightbulb.command("addrole", "Adds autorole to list")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def add_role(ctx: lightbulb.Context) -> None:
    """
    Adds a role to the autoroles list.

    Args:
        ctx (lightbulb.Context): The command context.

    Returns:
        None
    """
    role = ctx.options.role
    guild_data = GuildData(ctx.get_guild().id)
    roles = guild_data.retrieve(name="autoroles")
    if roles is not None:
        for _role in roles:
            if _role == role.id:
                await ctx.respond(f"{role.mention} has already been added!")
                return
    guild_data.append(name="autoroles", value=role.id)
    await ctx.respond(notify(f"{role.mention} added"))


@admin.child
@lightbulb.option("role", "Select the role", type=hikari.Role)
@lightbulb.command("removerole", "Removes autorole from list")
@lightbulb.implements(lightbulb.SlashSubCommand, lightbulb.PrefixSubCommand)
async def remove_role(ctx: lightbulb.Context) -> None:
    """
    Removes a role from the autoroles list.

    Args:
        ctx (lightbulb.Context): The command context.

    Returns:
        None
    """
    role = ctx.options.role
    guild_data = GuildData(guild_id=ctx.get_guild().id)
    guild_data.delete_element(name="autoroles", value=role.id)
    await ctx.respond(notify(f"{role.mention} removed"))


def notify(message: str) -> hikari.Embed:
    """
    Creates an embed template for admin commands.

    Args:
        message (str): The message to be displayed in the embed.

    Returns:
        hikari.Embed: The notification embed.
    """
    embed = hikari.Embed(title=message, description="", color=0xFF0000)
    embed.set_author(name="Admin Tools", icon=plugin.bot.get_me().display_avatar_url)
    return embed


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
