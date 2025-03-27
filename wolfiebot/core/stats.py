"""Stat tracking"""

import datetime

import hikari
import lightbulb

import wolfiebot
from wolfiebot.database.database import UserData, GuildData
from wolfiebot.logger import Logger

plugin = lightbulb.Plugin("core.stats")
log = Logger(__name__, wolfiebot.LOG_LEVEL)


class UserStats:
    """Manages statistics for a user, including message counts and voice chat (VC) time.

    Args:
        user_id (hikari.Snowflake | int): The unique identifier for the user.
    """

    def __init__(self, user_id: hikari.Snowflake | int):
        self.user_data = UserData(user_id=user_id)

    def get_messages(self) -> int:
        """Retrieves the total number of messages sent by the user.

        Returns:
            int: The total number of messages sent by the user. Returns 0 if no messages are found.
        """
        messages = self.user_data.retrieve(name="messages")
        if messages is None:
            messages = 0
        return messages

    def update_messages(self, new_value: int):
        """Updates the total number of messages sent by the user.

        Args:
            new_value (int): The new total number of messages to be set for the user.
        """
        self.user_data.edit(name="messages", value=new_value)

    def update_vc_time(self, new_value: int):
        """Updates the total time spent by the user in voice chat (VC).

        Args:
            new_value (int): The new total time (in seconds) to be set for the user's VC time.
        """
        self.user_data.edit(name="vc_time", value=new_value)

    def get_vc_time(self) -> int:
        """Retrieves the total time spent by the user in voice chat (VC).

        Returns:
            int: The total time (in seconds) spent by the user in VC.
        """
        vc_time = self.user_data.retrieve(name="vc_time")
        if vc_time is None:
            vc_time = 0
        return vc_time


class GuildStats:
    """Manages statistics for a guild, such as message counts.

    Args:
        guild_id (hikari.Snowflake | int): The unique identifier for the guild.
    """

    def __init__(self, guild_id: hikari.Snowflake | int):
        self.guild_data = GuildData(guild_id=guild_id)

    def get_messages(self) -> int:
        """Retrieves the total number of messages sent in the guild.

        Returns:
            int: The total number of messages sent in the guild.
        """
        messages = self.guild_data.retrieve(name="messages")
        if messages is None:
            messages = 0
        return messages

    def update_messages(self, new_value: int):
        """Updates the total number of messages sent in the guild.

        Args:
            new_value (int): The new total number of messages to be set for the guild.
        """
        self.guild_data.edit(name="messages", value=new_value)


class Timer:
    """Implements a timer using the Singleton pattern, ensuring only one instance per timer_id."""

    _instances = {}

    def __new__(cls, timer_id: int):
        if timer_id not in cls._instances:
            cls._instances[timer_id] = super(Timer, cls).__new__(cls)
        return cls._instances[timer_id]

    def __init__(self, timer_id: int):
        if not hasattr(self, "initialized"):
            self.time = 0
            self._start_time = None
            self.id = timer_id
            self.is_running = False
            self.initialized = True

    def start(self):
        """Starts the timer, setting the start time to the current time."""
        if not self.is_running:
            self._start_time = datetime.datetime.now()
            self.is_running = True

    def stop(self):
        """Stops the timer, calculates the elapsed time, and resets the timer's state."""
        if self.is_running:
            elapsed_time = datetime.datetime.now() - self._start_time
            self.time = round(elapsed_time.total_seconds())
            self.is_running = False


@plugin.listener(hikari.VoiceStateUpdateEvent)
async def on_voice(event):
    """Handles voice state updates for users in voice channels.

    The elapsed time is logged when the user leaves the channel.

    Args:
        event (hikari.VoiceStateUpdateEvent): The event triggered by a voice state update.
    """
    user_id = event.state.user_id
    if user_id == plugin.bot.get_me().id:
        return None

    user_timer = Timer(timer_id=user_id)

    if event.state.channel_id is not None:
        if not user_timer.is_running:
            user_timer.start()
    else:
        if user_timer.is_running:
            user_timer.stop()
            log.debug("user spent: %s", user_timer.time)


@plugin.listener(hikari.GuildMessageCreateEvent)
async def on_message(event):
    """Handles new messages created in a guild, updating user and guild message stats.

    Args:
        event (hikari.GuildMessageCreateEvent)
    """
    if event.is_bot is True or event.message.content.startswith("!"):
        return

    user_stats = UserStats(user_id=event.author.id)
    guild_stats = GuildStats(guild_id=event.guild.id)

    user_messages = user_stats.get_messages()
    guild_messages = guild_stats.get_messages()

    user_stats.update_messages(new_value=user_messages + 1)
    guild_stats.update_messages(new_value=guild_messages + 1)


def load(bot: lightbulb.BotApp) -> None:
    """Loads the plugin into the bot.

    Args:
        bot (lightbulb.BotApp): The bot instance.

    Returns:
        None
    """
    bot.add_plugin(plugin)


def unload(bot: lightbulb.BotApp) -> None:
    """Unloads the plugin from the bot.

    Args:
        bot (lightbulb.BotApp): The bot instance.

    Returns:
        None
    """
    bot.remove_plugin(plugin)
