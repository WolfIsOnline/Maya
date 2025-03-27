"""Entrance"""

import hikari
import lightbulb
import uvloop

from dotenv import load_dotenv, find_dotenv

import wolfiebot
from wolfiebot.database.database import UserData
from wolfiebot.logger import Logger
from wolfiebot.constants import CMD_ERR_NOT_OWNER

log = Logger(__name__, wolfiebot.LOG_LEVEL)

load_dotenv(find_dotenv())
DISCORD_API_KEY = wolfiebot.DISCORD_API_KEY

bot = lightbulb.BotApp(
    token=DISCORD_API_KEY,
    prefix="!",
    intents=hikari.Intents.ALL,
    default_enabled_guilds=[851644348281258035],
    help_class=None,
    logs=None,
)


def load_extensions():
    """Load all bot extensions"""
    extensions = {
        "core": ["quotes", "rooms", "logs", "welcome", "autorole", "levels", "stats"],
        "commands": ["user", "dev", "admin", "economy", "owner", "quotes"],
        "games": ["slots", "casino"],
        "ai": ["chat"],
    }

    for path, extension_list in extensions.items():
        for extension in extension_list:
            try:
                bot.load_extensions(f"wolfiebot.{path}.{extension}")
            # pylint: disable=broad-exception-caught
            except Exception as e:
                log.critical("Failed to load extensions: %s", e)


@bot.listen(hikari.StartedEvent)
# pylint: disable=unused-argument
async def start(event) -> None:
    """Set bot status"""
    status = UserData(bot.get_me().id).retrieve("status")
    await bot.update_presence(
        status=hikari.Status.ONLINE,
        activity=hikari.Activity(
            name=status,
            type=hikari.ActivityType.PLAYING,
        ),
    )


@bot.listen(lightbulb.CommandErrorEvent)
async def on_command_error(event: lightbulb.CommandErrorEvent) -> None:
    """Error handling"""
    exc = event.exception

    if isinstance(exc, lightbulb.NotOwner):
        await event.context.respond(CMD_ERR_NOT_OWNER)

    if isinstance(exc, lightbulb.CommandIsOnCooldown):
        seconds = exc.retry_after
        time = await format_time(seconds)
        await event.context.respond(f"On cooldown, try again in {time}")


async def format_time(seconds):
    """Formats a time duration in seconds into a human-readable string.

    Args:
        seconds: The time duration in seconds.

    Returns:
        A string representing the formatted time duration.
    """
    minutes = int(seconds // 60)
    hours = int(minutes // 60)
    days = int(hours // 24)
    years = int(days // 365)

    time_units = [
        (years, "year"),
        (days % 365, "day"),
        (hours % 24, "hour"),
        (minutes % 60, "minute"),
        (int(seconds) % 60, "second"),
    ]

    result = []
    for value, unit in time_units:
        if value != 0:
            result.append(f"{value} {unit if value == 1 else unit+'s'}")

    return ", ".join(result)


def main():
    """run bot"""
    uvloop.install()
    load_extensions()
    bot.run()


if __name__ == "__main__":
    main()
