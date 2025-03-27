"""
Auto Roles. Automatically assign roles upon joining the server
"""

import hikari
import lightbulb

from wolfiebot.database.database import GuildData

plugin = lightbulb.Plugin("core.autorole")


@plugin.listener(hikari.MemberCreateEvent)
async def user_join(event):
    """
    Handle user join event.

    Assigns autoroles to a newly joined member, if any are configured for the guild.

    Args:
        event (hikari.MemberCreateEvent): The member create event object.

    Returns:
        None
    """
    user = event.member
    guild_id = event.guild_id
    roles = GuildData(guild_id=guild_id).retrieve("autoroles")
    if roles is not None:
        for _role in roles:
            role = plugin.bot.cache.get_role(_role)
            await user.add_role(role)


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
