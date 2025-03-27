"""Slot game"""
import random
import asyncio
from dataclasses import dataclass, field
from typing import List, Tuple

import hikari
import lightbulb

import wolfiebot
from wolfiebot import constants
from wolfiebot.core.casino import Casino, InsufficientCreditsError, NegativeCreditsError
from wolfiebot.logger import Logger


log = Logger(__name__, wolfiebot.LOG_LEVEL)
plugin = lightbulb.Plugin("games.slots")


class MinimumAmountError(ValueError):
    """Exception for amounts below the minimum required."""

    def __init__(self, min_amount: int):
        """Initializes the exception with the minimum required amount.

        Args:
            min_amount (int): The minimum required amount.
        """
        super().__init__(
            f"Minimum amount error: amount is less than minimum '{min_amount}'"
        )


@dataclass
class Symbol:
    """Represents a symbol in the slot game with its properties.

    Attributes:
        name (str): The name of the symbol.
        sid (int): The symbol identifier.
        weight (int): The weight of the symbol for random selection.
        animated (bool): Flag indicating if the symbol is animated.
        multipliers (Tuple[int, ...]): Multipliers associated with the symbol.
    """

    name: str = ""
    sid: int = 0
    weight: int = 1
    animated: bool = False
    multipliers: Tuple[int, ...] = field(default_factory=tuple)

    def __post_init__(self):
        self.markdown = self._get_markdown()

    def _get_markdown(self) -> str:
        """Generates markdown representation of the symbol."""
        return (
            f"<a:{self.sid}:{self.sid}>"
            if self.animated
            else f"<:{self.sid}:{self.sid}>"
        )


class Bet:
    """Manages the state and logic for a bet in the slot game."""

    SLOTS = 3
    CREATED = 0
    PLAYING = 1
    LOSS = 2
    WIN = 3

    def __init__(self, amount: int, account: Casino):
        """Initializes the bet with a specified amount and account.

        Args:
            amount (int): The amount of the bet.
            account (Casino): The casino account associated with the bet.
        """
        self.amount = amount
        self.account = account
        self.condition = self.CREATED
        self.choices = None
        self.payout = None
        self.diamond = Symbol(
            name="diamond",
            sid=constants.SLOTS_SYM_DIAMOND_ID,
            weight=constants.SLOTS_SYM_DIAMOND_WEIGHT,
            animated=False,
            multipliers=(1600,),
        )
        self.cherry = Symbol(
            name="cherry",
            sid=constants.SLOTS_SYM_CHERRY_ID,
            weight=constants.SLOTS_SYM_CHERRY_WEIGHT,
            animated=False,
            multipliers=(2, 5, 10),
        )
        self.bbar = Symbol(
            name="bar",
            sid=constants.SLOTS_SYM_BAR_ID,
            weight=constants.SLOTS_SYM_BAR_WEIGHT,
            animated=False,
            multipliers=(10,),
        )
        self.seven = Symbol(
            name="seven",
            sid=constants.SLOTS_SYM_SEVEN_ID,
            weight=constants.SLOTS_SYM_SEVEN_WEIGHT,
            animated=False,
            multipliers=(100,),
        )
        self.blank = Symbol(
            name="blank",
            sid=constants.SLOTS_SYM_BLANK_ID,
            weight=constants.SLOTS_SYM_BLANK_WEIGHT,
            animated=False,
        )

    def run(self):
        """Runs the slot game, updates the bet state, and calculates the payout."""
        if self.amount < wolfiebot.MIN_SLOT_AMOUNT:
            raise MinimumAmountError(min_amount=wolfiebot.MIN_SLOT_AMOUNT)

        try:
            self.account.withdraw(amount=self.amount)

        except InsufficientCreditsError as exc:
            raise exc
        except NegativeCreditsError as exc:
            raise exc

        self.condition = self.PLAYING

        choices = []
        for _ in range(self.SLOTS):
            choices.append(self._get_choice())

        payout = self._get_payout(choices)
        self.payout = payout
        if payout == 0:
            self.condition = self.LOSS
        else:
            self.condition = self.WIN
            self.account.deposit(amount=payout)

        self.choices = choices

    def _get_payout(self, choices: List[Symbol]) -> int:
        """Calculates the payout based on the selected symbols.

        Args:
            choices(List[Symbol]): The symbols selected in the slot game.

        Returns:
            int: The calculated payout amount.
        """
        if not choices:
            return 0

        payout_rules = {
            constants.SLOTS_SYM_CHERRY_ID: (
                [1, 2, 3],
                [
                    self.cherry.multipliers[0],
                    self.cherry.multipliers[1],
                    self.cherry.multipliers[2],
                ],
            ),
            constants.SLOTS_SYM_BAR_ID: ([3], [self.bbar.multipliers[0]]),
            constants.SLOTS_SYM_SEVEN_ID: ([3], [self.seven.multipliers[0]]),
            constants.SLOTS_SYM_DIAMOND_ID: ([3], [self.diamond.multipliers[0]]),
        }

        symbol_counts = {sid: 0 for sid in payout_rules}

        for choice in choices:
            if choice.sid in symbol_counts:
                symbol_counts[choice.sid] += 1

        for sid, (counts, multipliers) in payout_rules.items():
            for count, multiplier in zip(counts, multipliers):
                if symbol_counts[sid] == count:
                    return self.amount * multiplier

        return 0

    def _get_choice(self):
        symbols = [self.diamond, self.cherry, self.bbar, self.seven, self.blank]
        weights = [symbol.weight for symbol in symbols]
        choice = random.choices(symbols, weights=weights)[0]
        return choice


@plugin.command
@lightbulb.option("amount", constants.SLOTS_CMD_AMOUNT_DESC, type=int, required=True)
@lightbulb.command("slots", constants.SLOTS_CMD_DESC)
@lightbulb.implements(lightbulb.SlashCommand, lightbulb.PrefixCommand)
async def slots_cmd(ctx: lightbulb.Context) -> None:
    """Executes the slot command, managing the flow of the slot game.

    Args:
        ctx (lightbulb.Context): The context of the command.
    """
    account = Casino(user_id=ctx.author.id)
    bet = Bet(amount=ctx.options.amount, account=account)

    await show_initial_animation(ctx)

    if not await process_bet(ctx, bet):
        return

    await reveal_slot_results(ctx, bet)
    await show_final_result(ctx, bet, account)


async def show_initial_animation(ctx: lightbulb.Context) -> None:
    """Displays the initial animation for the slot game.

    Args:
        ctx (lightbulb.Context): The context of the command.
    """
    anim = Symbol(sid=constants.SLOTS_SYM_ANIMATION_ID, animated=True)
    await ctx.respond(f"{anim.markdown}|{anim.markdown}|{anim.markdown}")


async def process_bet(ctx: lightbulb.Context, bet: Bet) -> bool:
    """Processes the bet and handles any exceptions.

    Args:
        ctx (lightbulb.Context): The context of the command.
        bet (Bet): The bet object.

    Returns:
        bool: True if the bet processing was successful, False otherwise.
    """
    try:
        bet.run()
        return True
    except (MinimumAmountError, InsufficientCreditsError, NegativeCreditsError) as exc:
        await handle_bet_exception(ctx, exc)
        return False


async def handle_bet_exception(ctx: lightbulb.Context, exc: Exception) -> None:
    """Handles exceptions raised during bet processing.

    Args:
        ctx (lightbulb.Context): The context of the command.
        exc (Exception): The exception that was raised.
    """
    log.error(exc.message)
    if isinstance(exc, MinimumAmountError):
        await ctx.respond(constants.CASINO_MIN_GAMBLE)
    elif isinstance(exc, InsufficientCreditsError):
        await ctx.respond(constants.INSUFFICIENT_CREDITS_ERROR)
    elif isinstance(exc, NegativeCreditsError):
        await ctx.respond(constants.NEGATIVE_AMOUNT_ERROR)


async def reveal_slot_results(ctx: lightbulb.Context, bet: Bet) -> None:
    """Reveals the slot game results.

    Args:
        ctx (lightbulb.Context): The context of the command.
        bet (Bet): The bet object.
    """
    anim = Symbol(sid=constants.SLOTS_SYM_ANIMATION_ID, animated=True)
    for i in range(Bet.SLOTS):
        response_elements = [
            bet.choices[j].markdown if j <= i else anim.markdown
            for j in range(Bet.SLOTS)
        ]
        response = "|".join(response_elements)
        await ctx.edit_last_response(response)
        await asyncio.sleep(0.3)


async def show_final_result(ctx: lightbulb.Context, bet: Bet, account: Casino) -> None:
    """Shows the final result of the slot game.

    Args:
        ctx (lightbulb.Context): The context of the command.
        bet (Bet): The bet object.
        account (Casino): The casino account associated with the user.
    """
    if bet.condition == bet.WIN:
        message, sign, color, amount = "YOU WON!", "+", 0x2ECC71, bet.payout
    else:
        message, sign, color, amount = "You lost!", "-", 0xFF0000, bet.amount

    embed = hikari.Embed(title="Nocturnia Casino", color=color)
    embed.add_field(
        "Result:",
        f"{bet.choices[0].markdown}|{bet.choices[1].markdown}|{bet.choices[2].markdown}",
    )
    embed.add_field("Credits:", f"**₵{account.get_balance():,}**")
    await ctx.edit_last_response(f"{message} **{sign}₵{amount:,}**", embed=embed)


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
