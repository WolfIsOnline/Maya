"""
User Commands
"""

import datetime
import sys
import hikari
import lightbulb
import wolfiebot


from wolfiebot import constants
from wolfiebot.database.database import UserData
from wolfiebot.ai.ai_manager import AIManager

plugin = lightbulb.Plugin("commands.user")


@plugin.command
@lightbulb.command("clear", constants.MAYA_CLEAR_MEMORY_DESC)
@lightbulb.implements(lightbulb.SlashCommand, lightbulb.PrefixCommand)
async def clear_chat(ctx: lightbulb.Context):
    UserData(user_id=ctx.author.id).delete(name="thread_id")
    await ctx.respond(notify(constants.MAYA_CLEAR_MEMORY))


@plugin.command
@lightbulb.option("user", constants.USER_SELECT_DESC, type=hikari.User, required=False)
@lightbulb.command("avatar", "Get users avatar", aliases="pfp")
@lightbulb.implements(lightbulb.SlashCommand, lightbulb.PrefixCommand)
async def avatar(ctx: lightbulb.Context):
    """Get the avatar URL of a user.

    If no user is specified, it will return the avatar URL of the invoking user.

    Args:
        ctx (lightbulb.Context): The context object representing the invocation.
    """
    try:
        avatar_url = ctx.options.user.display_avatar_url

    except AttributeError:
        avatar_url = ctx.author.display_avatar_url

    await ctx.respond(f"{avatar_url}")


@plugin.command
@lightbulb.command("info", f"Info about {wolfiebot.AI_NAME}")
@lightbulb.implements(lightbulb.SlashCommand, lightbulb.PrefixCommand)
async def info(ctx: lightbulb.Context):
    """
    Provides information about the Wolfie bot.

    Args:
        ctx (lightbulb.Context): The command context.
    """
    python_version = sys.version_info
    embed = hikari.Embed(
        title=f"About {wolfiebot.AI_NAME}",
        description=wolfiebot.__description__,
        color=wolfiebot.DEFAULT_COLOR,
    )
    embed.add_field(f"{wolfiebot.AI_NAME} version", wolfiebot.__version__, inline=True)
    embed.add_field(
        "Python",
        f"[{python_version.major}.{python_version.minor}.{python_version.micro}](https://python.org)",
        inline=True,
    )
    embed.add_field(
        "Hikari",
        f"[{hikari.__version__}](https://github.com/hikari-py/hikari)",
        inline=True,
    )
    await ctx.respond(embed=embed)


@plugin.command
@lightbulb.option("user", "Select a member", type=hikari.User, required=False)
@lightbulb.command("profile", "Info about Wolfie")
@lightbulb.implements(lightbulb.SlashCommand, lightbulb.PrefixCommand)
async def profile(ctx: lightbulb.Context):
    user_id = ctx.author.id
    user_data = UserData(user_id=user_id)
    embed = hikari.Embed(title=f"{ctx.author}'s Profile", color=wolfiebot.DEFAULT_COLOR)
    embed.add_field("Level", user_data.retrieve("level"), inline=True)
    embed.add_field("XP", user_data.retrieve("xp"), inline=True)
    embed.add_field("Balance", user_data.retrieve("balance"))
    embed.add_field("Casino Balance", user_data.retrieve("casino_balance"))


@plugin.command
@lightbulb.option("prompt", "Enter what you want to create.", type=str, required=True)
@lightbulb.command("image", "Create an AI generated Image", auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand, lightbulb.PrefixCommand)
async def image(ctx: lightbulb.Context):
    prompt = ctx.options.prompt
    manager = AIManager(ctx.author.id)
    ai_image = manager.create_image(prompt)
    embed = hikari.Embed(color=wolfiebot.DEFAULT_COLOR)
    embed.set_image(ai_image)
    embed.set_author(
        name=f"Requested By: {ctx.author}", icon=ctx.author.display_avatar_url
    )
    embed.set_footer(text=f'"{prompt}"')
    embed.timestamp = datetime.datetime.now().astimezone()
    await ctx.respond(embed=embed)


def notify(message):
    """
    Create an embed notification.

    Args:
        message (str): The message to be displayed in the embed.

    Returns:
        hikari.Embed: The embed object with the provided message.
    """
    embed = hikari.Embed(title=message, description="", color=wolfiebot.DEFAULT_COLOR)
    embed.set_author(
        name="Wolfie Commands", icon=plugin.bot.get_me().display_avatar_url
    )
    return embed


def load(bot: lightbulb.BotApp):
    """
    Loads the plugin into the bot.

    Parameters:
    - bot (lightbulb.BotApp): The bot instance.

    """
    bot.add_plugin(plugin)


def unload(bot: lightbulb.BotApp):
    """
    Unloads the plugin from the specified bot.

    Args:
        bot (lightbulb.BotApp): The bot instance to unload the plugin from.

    Returns:
        None
    """
    bot.remove_plugin(plugin)
