"""Development Commands"""
import datetime
import psutil

import hikari
import lightbulb
from lightbulb.utils import pag, nav

import wolfiebot
from wolfiebot.commands.quotes import get_quote_from_user
from wolfiebot.core.bank import Bank
from wolfiebot.database.database import UserData

plugin = lightbulb.Plugin("dev", "dev commands")


@plugin.command
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.command("dev", "dev commands")
@lightbulb.implements(lightbulb.PrefixCommandGroup, lightbulb.SlashCommandGroup)
async def _dev_group() -> None:
    """
    Command group for development-related commands.
    This command group is restricted to the bot owner.

    Returns:
        None
    """
    return None


@_dev_group.child
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.option("user", "User", type=hikari.User, required=True)
@lightbulb.command("balance", "Display user balance")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def _dev_balance(ctx: lightbulb.Context):
    user_id = ctx.options.user.id
    account = Bank(user_id)

    embed = hikari.Embed(
        title="Nocturnia Bank - Dev Tools",
        description=f"Available Balance: **{wolfiebot.CURRENCY_SYMBOL}{account.balance:,}**",
        color=0x000000,
    )
    embed.set_author(
        name=f"{ctx.options.user}", icon=ctx.options.user.display_avatar_url
    )
    await ctx.respond(embed)


@_dev_group.child
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.option("status", "Status Messsage", type=str, required=True)
@lightbulb.command("setstatus", "Set bot status")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def _set_status(ctx: lightbulb.Context):
    """
    Command to set the bot's status.

    This command is restricted to the bot owner
    and requires a status message to be provided as an option.

    Args:
        ctx (lightbulb.Context): The command invocation context.

    Returns:
        None
    """
    await plugin.bot.update_presence(
        status=hikari.Status.ONLINE,
        activity=hikari.Activity(
            name=ctx.options.status,
            type=hikari.ActivityType.PLAYING,
        ),
    )
    user = UserData(plugin.bot.get_me().id)
    user.edit("status", ctx.options.status)
    await ctx.respond(notify("presence updated!"))


@_dev_group.child
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.option("extension", "Extension", type=str, required=True)
@lightbulb.command("load", "Load an entension")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def _load_ext(ctx: lightbulb.Context):
    """
    Command to load an extension.

    This command is restricted to the bot owner
    and requires the name of the extension to be provided as an option.

    Args:
        ctx (lightbulb.Context): The command invocation context.

    Returns:
        None
    """
    plugin.bot.load_extensions(f"wolfiebot.{ctx.options.extension}")
    await ctx.respond(notify(f"{ctx.options.extension} loaded"))


@_dev_group.child
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.option("extension", "Extension", type=str, required=True)
@lightbulb.command("unload", "Unload an extension")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def _unload_ext(ctx: lightbulb.Context):
    """
    Command to unload an extension.

    This command is restricted to the bot owner
    and requires the name of the extension to be provided as an option.

    Args:
        ctx (lightbulb.Context): The command invocation context.

    Returns:
        None
    """
    plugin.bot.unload_extensions(f"wolfiebot.{ctx.options.extension}")
    await ctx.respond(notify(f"{ctx.options.extension} unloaded"))


@_dev_group.child
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.option("extension", "Extension", type=str, required=True)
@lightbulb.command("reload", "Reload an extension")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def _reload_ext(ctx: lightbulb.Context):
    """
    Command to reload an extension.

    This command is restricted to the bot owner
    and requires the name of the extension to be provided as an option.

    Args:
        ctx (lightbulb.Context): The command invocation context.

    Returns:
        None
    """
    plugin.bot.unload_extensions(f"wolfiebot.{ctx.options.extension}")
    plugin.bot.load_extensions(f"wolfiebot.{ctx.options.extension}")
    await ctx.respond(notify(f"{ctx.options.extension} reloaded :arrows_clockwise:"))


@_dev_group.child
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.option("toggle", "True/False", type=bool, required=True)
@lightbulb.command("voice", "Turn wolfie voice off")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def _voice(ctx: lightbulb.Context):
    """
    Command to turn off Wolfie voice.

    This command is restricted to the bot owner
    and requires a boolean toggle option (`True` or `False`) to be provided.
    It sets the voice state of the bot to the specified toggle value in the user data.

    Args:
        ctx (lightbulb.Context): The command invocation context.

    Returns:
        None
    """
    user = UserData(plugin.bot.get_me().id)
    user.edit("voice_state", ctx.options.toggle)
    await ctx.respond(notify(f"send voice set to {ctx.options.toggle}"))


@_dev_group.child
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.command("info", "Detailed information")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def _info(ctx: lightbulb.Context):
    """
    Command to display detailed information about the system.

    This command is restricted to the bot owner.
    It retrieves and displays information about CPU usage, memory usage, and the operating system.
    The information is formatted into an embed and sent as a response.

    Args:
        ctx (lightbulb.Context): The command invocation context.

    Returns:
        None
    """
    cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
    min_cpu_percent = round(min(cpu_percent))
    max_cpu_percent = round(max(cpu_percent))
    avg_cpu_percent = round(sum(cpu_percent) / len(cpu_percent))

    memory = psutil.virtual_memory()
    total_memory_gb = round(memory.total / (1024**3), 2)
    available_memory_gb = round(memory.available / (1024**3), 2)
    used_memory_gb = round(memory.used / (1024**3), 2)

    os_info = psutil.sys.platform
    boot_time = psutil.boot_time()
    os_uptime = datetime.datetime.now() - datetime.datetime.fromtimestamp(boot_time)

    memory_format = f"Total: {total_memory_gb}GB\nAvailable: {available_memory_gb}GB\nUsed: {used_memory_gb}GB"
    cpu_format = (
        f"Min: {min_cpu_percent}%\nAVG: {avg_cpu_percent}%\nMax: {max_cpu_percent}%"
    )
    os_format = f"OS: {os_info}\nUptime: {os_uptime}"
    description = f"Memory Usage:\n```{memory_format}```\nCPU Usage:\n ```{cpu_format}```\nOS Info:\n```{os_format}```"
    embed = hikari.Embed(description=description, color=0x000000)
    await ctx.respond(embed)


@_dev_group.child
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.option("user", "Select User", type=hikari.User, required=True)
@lightbulb.command("all_quotes", "Get all quotes from user")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def _all_quotes(ctx: lightbulb.Context):
    """
    Retrieve all quotes from a specific user within the guild and display them in pages.

    Args:
        ctx (lightbulb.Context): The command context.
    """
    user_id = ctx.options.user.id
    guild_id = ctx.get_guild().id
    _quotes = await get_quote_from_user(user_id=user_id, guild_id=guild_id)
    pages = pag.StringPaginator(max_lines=20)
    for index, quote in enumerate(_quotes, start=1):
        pages.add_line(f'**{index}.** "{quote}"')

    navigator = nav.ButtonNavigator(pages.build_pages())
    await navigator.run(ctx)


@_dev_group.child
@lightbulb.add_checks(lightbulb.owner_only)
@lightbulb.option("level", "level", type=int, required=True)
@lightbulb.option("user", "Select User", type=hikari.User, required=True)
@lightbulb.command("set_level", "Set level multiplier", auto_defer=True)
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def _set_level(ctx: lightbulb.Context) -> None:
    """
    Set the level for a user.

    Sets the level of a user to the specified value by adjusting their experience points.
    The required experience points for the specified level are calculated using
    the level multiplier.

    Args:
        ctx (lightbulb.Context): The command invocation context.
    """
    level = ctx.options.level
    user = ctx.options.user
    guild_id = ctx.get_guild().id
    channel_id = ctx.get_channel().id
    exp_required = await wolfiebot.core.levels.get_exp_required(level)
    await wolfiebot.core.levels.set_exp(
        user_id=user.id, exp=exp_required, channel_id=channel_id, guild_id=guild_id
    )
    await ctx.respond("✅", delete_after=1)


def notify(message):
    """
    Creates an embed notification.

    Parameters:
    - message (str): The content of the notification.

    Returns:
    - hikari.Embed: The embed notification.

    This function creates an embed notification with the given message and returns it.
    The embed is styled with a black color and includes the author name set as 'Dev Tools'
    with the bot's display avatar as the icon.
    """
    embed = hikari.Embed(title=message, description="", color=0x000000)
    embed.set_author(name="Dev Tools", icon=plugin.bot.get_me().display_avatar_url)
    return embed


def load(bot: lightbulb.BotApp):
    """
    Loads the plugin into the bot.

    Parameters:
    - bot (lightbulb.BotApp): The bot instance.

    This function adds the plugin to the bot, allowing it to be used and respond to commands.
    """
    bot.add_plugin(plugin)


def unload(bot: lightbulb.BotApp):
    """
    Unloads the plugin from the bot.

    Parameters:
    - bot (lightbulb.BotApp): The bot instance.

    This function removes the plugin from the bot, disabling its functionality and commands.
    """
    bot.remove_plugin(plugin)
