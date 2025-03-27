import hikari
import lightbulb

import wolfiebot
from wolfiebot import constants
from wolfiebot.database.database import GuildData
from wolfiebot.ai.ai_manager import AIManager
from wolfiebot.logger import Logger

plugin = lightbulb.Plugin("core.welcome")

log = Logger(__name__, wolfiebot.LOG_LEVEL)


@plugin.listener(hikari.MemberCreateEvent)
async def user_join(event):
    """Handles the user join event and sends a welcome message.

    Args:
        event: The event object representing the user join event.
    """
    guild = event.get_guild()
    manager = AIManager(
        event.user.id,
        instruction=f"{constants.MAYA_GREETING_INSTR}. The server name is {guild}",
    )
    welcome_message = await manager.send_message(
        text="Welcome me to the discord server"
    )
    channel = GuildData(guild_id=guild.id).retrieve(name="welcome_channel")
    await plugin.bot.rest.create_message(
        channel=channel, content=f"<@{event.user.id}> {welcome_message}"
    )


def load(bot: lightbulb.BotApp):
    """Registers the plugin with the bot instance.

    Args:
        bot: The bot instance to load the plugin into.
    """
    bot.add_plugin(plugin)


def unload(bot: lightbulb.BotApp):
    """Deregisters the plugin from the bot instance.

    Args:
        bot: The bot instance to remove the plugin from.
    """
    bot.remove_plugin(plugin)
