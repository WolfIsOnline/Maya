"""Listeners"""

import re

import hikari
import lightbulb

import wolfiebot
from wolfiebot.ai.ai_manager import AIManager
from wolfiebot.ai.voice_manager import VoiceManager
from wolfiebot.database.database import UserData
from wolfiebot.logger import Logger

plugin = lightbulb.Plugin("ai.chat")
log = Logger(__name__, wolfiebot.LOG_LEVEL)


@plugin.listener(hikari.GuildMessageCreateEvent)
async def guild_channel(event) -> None:
    if event.author_id == plugin.bot.get_me().id:
        return

    if plugin.bot.get_me().id in event.message.user_mentions:
        user = plugin.bot.cache.get_member(event.guild_id, event.author.id)
        name = user.nickname
        if name is None:
            name = user
        await chat(event)


@plugin.listener(hikari.DMMessageCreateEvent)
async def direct_message(event) -> None:
    if event.author_id == plugin.bot.get_me().id:
        return

    await chat(event)


async def chat(event) -> None:
    message = _sanatize_message(event.message.content)
    attachments = event.message.attachments
    if message.startswith("!"):
        return

    ai_manager = AIManager(event.author.id)
    async with plugin.bot.rest.trigger_typing(event.channel_id):
        reply = await ai_manager.send_message(text=message, attachment=attachments)
        user = UserData(plugin.bot.get_me().id)
        video = None
        if user.retrieve("voice_state") is True:
            voice = VoiceManager(reply)
            voice.generate_reply()
            voice.save_audio()
            voice.convert_to_video()
            video = hikari.File(voice.OUTPUT_PATH)

    if reply is None or reply == "":
        return

    await plugin.bot.rest.create_message(
        channel=event.channel_id, content=reply, reply=event.message, attachment=video
    )


def _sanatize_message(message: str):
    if message is None or message == "":
        return ""
    return re.sub(r"<.*?>", "", message)


def load(bot: lightbulb.BotApp) -> None:
    """
    Loads the plugin into the specified bot.

    Args:
        bot (lightbulb.BotApp): The bot instance to load the plugin into.
    """
    bot.add_plugin(plugin)


def unload(bot: lightbulb.BotApp) -> None:
    """
    Unloads the plugin from the specified bot.

    Args:
        bot (lightbulb.BotApp): The bot instance to unload the plugin from.
    """
    bot.remove_plugin(plugin)
