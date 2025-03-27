"""Leveling System"""
import random
import math

import lightbulb
import hikari

import wolfiebot
from wolfiebot.database.database import UserData
from wolfiebot.core.bank import Bank
from wolfiebot.ai.simple_api import Simple_API

plugin = lightbulb.Plugin("core.levels")
simple_api = Simple_API()

BASE_VALUE = 25
EXPONENT = 1.5


@plugin.listener(hikari.GuildMessageCreateEvent)
async def on_message(event) -> None:
    """
    Handle guild message create event.

    This function is triggered when a message is created in a guild.
    It increments the experience points for the user that messaged and updates their level.

    Args:
        event (hikari.GuildMessageCreateEvent): The guild message create event object.

    Returns:
        None
    """
    user_id = event.author.id
    content = event.message.content
    bot_id = plugin.bot.get_me().id
    guild_id = event.guild_id

    try:
        if (
            content is None
            or content.startswith("!")
            or content.startswith("$")
            or event.is_bot is True
        ):
            return None

    except AttributeError():
        pass

    await add_exp(user_id=user_id, increment=1)
    await update_level(
        user_id=user_id, channel_id=event.get_channel().id, guild_id=guild_id
    )
    exp = await get_exp(user_id)
    level = await get_level(user_id)
    exp_needed = await get_exp_required(level + 1)


async def add_exp(user_id: int, increment: int) -> None:
    """
    Add experience points to a user.

    Increases the experience points of a user by the specified increment.

    Args:
        user_id (int): The ID of the user to add experience points to.
        increment (int): The amount of experience points to add.

    Returns:
        None
    """
    exp = await get_exp(user_id=user_id)
    exp += increment
    UserData(user_id=user_id).edit(name="xp", value=exp)


async def set_exp(user_id: int, exp: int, channel_id: int, guild_id: int) -> None:
    """
    Sets the experience points (exp) for the specified user ID and updates the level.

    Args:
        user_id (int): The ID of the user.
        exp (int): The new experience points to set.
        channel_id (int): The ID of the channel for sending level update messages.

    Returns:
        None
    """
    UserData(user_id=user_id).edit(name="xp", value=exp)
    await update_level(user_id=user_id, channel_id=channel_id, guild_id=guild_id)


async def take_exp(user_id: int, increment: int) -> None:
    """
    Take away experience points from a user.

    Decreases the experience points of a user by the specified increment.
    If the user's experience points become negative, no changes are made.

    Args:
        user_id (int): The ID of the user to take experience points from.
        increment (int): The amount of experience points to take away.

    Returns:
        None
    """
    exp = await get_exp(user_id=user_id)
    if exp < 0:
        return None
    exp -= increment
    UserData(user_id=user_id).edit(name="xp", value=exp)


async def get_exp(user_id: int) -> int:
    """
    Get the experience points of a user.

    Retrieves the experience points of a user from the database.
    If the user's experience points are not found, it returns 0.

    Args:
        user_id (int): The ID of the user to retrieve the experience points for.

    Returns:
        int: The experience points of the user.
    """
    exp = UserData(user_id=user_id).retrieve(name="xp")
    if exp is None:
        exp = 0
    return exp


async def get_level(user_id: int) -> int:
    """
    Get the level of a user.

    Retrieves the level of a user from the database.
    If the user's level is not found, it returns 0.

    Args:
        user_id (int): The ID of the user to retrieve the level for.

    Returns:
        int: The level of the user.
    """
    level = UserData(user_id=user_id).retrieve(name="level")
    if level is None:
        level = 0
    return level


async def update_level(user_id: int, channel_id: int, guild_id: int) -> None:
    """
    Update the user's level.

    This function updates the level of a user based on their experience points.
    If the user's level changes, it sends a notification in the specified event channel.

    Args:
        user_id (int): The ID of the user to update the level for.
        event: The event object related to the update.

    Returns:
        None
    """
    current_exp = await get_exp(user_id)
    current_level = await get_level(user_id)
    level = await calculate_level(exp=current_exp)
    if current_level != level:
        UserData(user_id=user_id).edit(name="level", value=level)
        await notify_level_up(user_id=user_id, channel_id=channel_id, guild_id=guild_id)


async def notify_level_up(user_id: int, channel_id: int, guild_id: int) -> None:
    """
    Notifies the user about a level up and provides rewards.

    Args:
        user_id (int): The ID of the user.
        channel_id (int): The ID of the channel to send the notification.

    Returns:
        None
    """
    level = await get_level(user_id)
    reward = await calculate_reward(level)
    role_id = await calculate_role(level)

    user = plugin.bot.cache.get_user(user_id)
    member = plugin.bot.cache.get_member(guild_id, user_id)
    account = Bank(user_id)
    await account.deposit(amount=reward, statement="reward for leveling")

    session = await simple_api.open_session({user_id: user_id})
    session_id = session.get("name")
    character_id = session.get("sessionCharacters", [])[0].get("character", None)

    response = await simple_api.send_trigger_message(
        session_id=session_id, character_id=character_id, trigger="level_up"
    )
    text_list = response.get("textList")
    combine_text = "".join(text_list)

    embed = hikari.Embed(
        title="Promoted!",
        description=f"You are now level **{level}**",
        color=wolfiebot.DEFAULT_COLOR,
    )
    embed.set_author(name=user.global_name)
    embed.set_thumbnail(user.display_avatar_url)

    if role_id is None:
        embed.add_field(
            name="Rewards: ", value=f"+{wolfiebot.CURRENCY_SYMBOL}{reward:,}"
        )
    else:
        role = plugin.bot.cache.get_role(role_id)
        await member.add_role(role)
        embed.add_field(
            name="Rewards:",
            value=f"**+{wolfiebot.CURRENCY_SYMBOL}{reward:,}** added\n{role.mention} given",
        )

    await plugin.bot.rest.create_message(
        channel=channel_id,
        embed=embed,
        content=f"<@{user_id}> {combine_text}",
    )


async def calculate_role(level: int) -> int:
    """
    Calculates the role ID based on the user's level.

    Args:
        level (int): The level of the user.

    Returns:
        int: The ID of the role corresponding to the level, or None if no role is found.
    """
    roles = {
        10: "996889015502512202",
        30: "997081656445894656",
        50: "997081843063074836",
        80: "997082048810450994",
    }

    return roles.get(level, None)


async def calculate_reward(level: int) -> int:
    """
    Calculates the reward amount based on the given level.

    Args:
        level (int): The level of the user.

    Returns:
        int: The calculated reward amount.
    """
    additional = random.randint(100, 999)
    return (level * 1000) + additional


async def calculate_level(exp: int) -> int:
    """
    Calculates the level based on the given experience points (exp) and user ID.

    Args:
        exp (int): The current experience points of the user.

    Returns:
        int: The calculated level.
    """
    return math.floor((exp / BASE_VALUE) ** (1 / EXPONENT))


async def get_exp_required(level: int) -> int:
    """
    Calculates the required experience points for the given level.

    Args:
        level (int): The level for which to calculate the required experience points.

    Returns:
        int: The calculated required experience points.
    """
    return math.ceil(BASE_VALUE * (level**EXPONENT))


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
