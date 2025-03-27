import hikari
import lightbulb

import wolfiebot

from wolfiebot import constants
from wolfiebot.core.casino import (
    Casino,
    InsufficientCreditsError,
    NegativeCreditsError,
)
from wolfiebot.core.bank import Bank, InsufficientFundsError
from wolfiebot.logger import Logger

plugin = lightbulb.Plugin("games.casino")

log = Logger(__name__, wolfiebot.LOG_LEVEL)


# Admin Group
@plugin.command
@lightbulb.command("casino", "Casino commands")
@lightbulb.implements(lightbulb.PrefixCommandGroup, lightbulb.SlashCommandGroup)
async def casino():
    pass


@casino.child
@lightbulb.command("balance", "Check balance")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def balance(ctx: lightbulb.Context):
    author_id = ctx.author.id
    casino_balance = Casino(user_id=author_id).balance
    description = f"Credits: **{wolfiebot.CASINO_SYMBOL}{casino_balance:,}**"
    embed = hikari.Embed(
        title="Nocturnia Casino", description=description, color=wolfiebot.CASINO_COLOR
    )
    embed.set_author(name=f"{ctx.author} | Member", icon=ctx.author.display_avatar_url)
    await ctx.respond(embed)


@casino.child
@lightbulb.option("amount", "Amount to deposit", type=int, required=True)
@lightbulb.command("deposit", "Deposit money into casino")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def deposit(ctx: lightbulb.Context):
    author_id = ctx.author.id
    account = Bank(author_id)
    casino_account = Casino(user_id=author_id)
    amount = ctx.options.amount
    try:
        withdrawl = await account.withdraw(amount=amount, statement="casino")

    except InsufficientFundsError as exc:
        await ctx.respond(notify(constants.INSUFFICIENT_FUNDS_ERROR))
        raise exc

    try:
        casino_account.deposit(amount=withdrawl)
    except NegativeCreditsError as exc:
        await ctx.respond(notify(constants.NEGATIVE_AMOUNT_ERROR))
        raise exc

    casino_balance = casino_account.balance
    description = f"**{withdrawl:,}** credits have been added to your account"
    embed = hikari.Embed(
        title="Nocturnia Casino", description=description, color=wolfiebot.CASINO_COLOR
    )
    embed.add_field("Credits:", f"**{wolfiebot.CASINO_SYMBOL}{casino_balance:,}**")
    await ctx.respond(embed)


@casino.child
@lightbulb.option("amount", "Amount to payout", type=int, required=True)
@lightbulb.command("payout", "Payout casino money to your bank account")
@lightbulb.implements(lightbulb.PrefixSubCommand, lightbulb.SlashSubCommand)
async def payout(ctx: lightbulb.Context):
    author_id = ctx.author.id
    casino_account = Casino(user_id=author_id)
    amount = ctx.options.amount

    try:
        casino_account.withdraw(amount)
    except InsufficientCreditsError as exc:
        await ctx.respond(notify(constants.INSUFFICIENT_CREDITS_ERROR))
        raise exc

    except NegativeCreditsError as exc:
        await ctx.respond(notify(constants.NEGATIVE_AMOUNT_ERROR))
        raise exc

    account = Bank(user_id=author_id)
    await account.deposit(amount=amount, statement="Nocturnia Casino payout")
    await ctx.respond(
        f"**{wolfiebot.CURRENCY_SYMBOL}{amount:,}** has been transfered to your bank"
    )


def notify(message):
    bot = plugin.bot.get_me()
    embed = hikari.Embed(
        title=message,
        description="",
        color=wolfiebot.CASINO_COLOR,
    )
    embed.set_author(name="Nocturnia Casino", icon=bot.display_avatar_url)
    return embed


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
