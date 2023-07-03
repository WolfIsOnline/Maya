"""
Economy Commands
"""

import logging
import hikari
import lightbulb
import wolfiebot

# pylint: disable=no-name-in-module, import-error, unused-import
from wolfiebot.core.bank import Bank

log = logging.getLogger(__name__)
bank = Bank()
plugin = lightbulb.Plugin("commands.economy")

@plugin.command
@lightbulb.command("balance", "Display your balance")
@lightbulb.implements(lightbulb.SlashCommand, lightbulb.PrefixCommand)
async def balance(ctx: lightbulb.Context):
    """
    Command to display the user's balance.

    Parameters:
    - ctx (lightbulb.Context): The command context.

    This command retrieves the user's balance from the bank
    and sends a response with an embedded message displaying the available balance.
    The balance is formatted with the currency symbol and comma separators.
    The embedded message includes the user's display name and avatar.
    """
    user_balance = bank.get_balance(ctx.author.id)
    embed = hikari.Embed(
        title = "Nocturnia Bank",
        description=f"Available Balance: **{wolfiebot.CURRENCY_SYMBOL}{user_balance:,}**",
        color=wolfiebot.DEFAULT_COLOR
    )
    embed.set_author(name=f"{ctx.author}", icon=ctx.author.display_avatar_url)
    await ctx.respond(embed)

@plugin.command
@lightbulb.add_cooldown(length=14400, uses=1, bucket=lightbulb.UserBucket)
@lightbulb.command("payday", f"Get paid {wolfiebot.PAYDAY:,}")
@lightbulb.implements(lightbulb.SlashCommand, lightbulb.PrefixCommand)
async def payday(ctx: lightbulb.Context):
    """
    Command to receive a payday deposit.

    Parameters:
    - ctx (lightbulb.Context): The command context.

    This command deposits the predefined payday amount into the user's account
    in the bank. It applies a cooldown period to limit the frequency of payday
    claims. After the deposit, a response is sent notifying the user about the
    deposited amount using the `notify` function.
    """
    bank.deposit(ctx.author.id, wolfiebot.PAYDAY, "payday")
    await ctx.respond(
        notify(
            f"{wolfiebot.CURRENCY_SYMBOL}{wolfiebot.PAYDAY:,} has been deposited into your account"
        )
    )

@plugin.command
@lightbulb.option("user", "Select the member", type=hikari.User, required=True)
@lightbulb.option("amount", "Amount of money", type=int, required=True)
@lightbulb.command("transfer", "Transfer money to a member", aliases="tr")
@lightbulb.implements(lightbulb.SlashCommand, lightbulb.PrefixCommand)
async def transfer(ctx: lightbulb.Context):
    """
    Command to transfer money to another member.

    Parameters:
    - ctx (lightbulb.Context): The command context.

    This command allows the user to transfer a specified amount of money to
    another member. The target member is specified using the `user` option, and
    the transfer amount is specified using the `amount` option. The `transfer`
    function in the `bank` module is called to process the transfer. If the
    transfer is successful, a response is sent notifying the user about the
    transferred amount using the `notify` function. If the transfer fails due to
    insufficient funds, a decline message is displayed.
    """
    amount = ctx.options.amount
    transfer_amount = bank.transfer(
        ctx.author.id,
        ctx.options.user.id,
        amount,
        f"Transfer to {ctx.options.user}",
        f"Transfer from {ctx.author}"
    )
    if transfer_amount <= -1:
        description = "Transfer declined (Insufficent Funds)"
    else:
        description = f"{wolfiebot.CURRENCY_SYMBOL}{amount:,} transfered to {ctx.options.user}"
    await ctx.respond(notify(description))

def notify(message):
    """
    Creates an embedded message with the specified title and color.

    Parameters:
    - message (str): The message content.

    Returns:
    - hikari.Embed: The embedded message with the specified title, an empty description,
      and the default color.
    """
    embed = hikari.Embed(title=message, description="", color=wolfiebot.DEFAULT_COLOR)
    embed.set_author(
        name="Nocturnia Bank",
        icon=plugin.bot.get_me().display_avatar_url
    )
    return embed

def load(bot: lightbulb.BotApp):
    """
    Loads the plugin into the specified bot.

    Args:
        bot (lightbulb.BotApp): The bot instance to load the plugin into.

    Returns:
        None
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
