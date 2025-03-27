"""Casino System"""
import hikari

import wolfiebot
from wolfiebot.database.database import UserData
from wolfiebot.logger import Logger

log = Logger(__name__, wolfiebot.LOG_LEVEL)


class InsufficientCreditsError(Exception):
    """Exception raised when a withdrawal attempt exceeds the available balance."""

    def __init__(self, balance: int, amount: int, message: str = "InsufficientCredits"):
        self.amount = amount
        self.balance = balance
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}: amount "{self.amount}" > "{self.balance}"'


class NegativeCreditsError(ValueError):
    """Exception raised when a withdrawal amount is negative."""

    def __init__(self, amount, message="NegativeWithdrawal"):
        self.amount = amount
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}: amount "{self.amount}" is < 0'


class Casino:
    def __init__(self, user_id: hikari.Snowflake | int):
        self.user_data = UserData(user_id=user_id)
        self.user_id = user_id
        self.balance = self.get_balance()

    def deposit(self, amount: int):
        if amount < 0:
            raise NegativeCreditsError(amount=amount)

        new_balance = self.balance + amount
        self.user_data.edit(name="casino_balance", value=new_balance)

    def withdraw(self, amount: int) -> int:
        if amount < 0:
            raise NegativeCreditsError(amount=amount)

        if amount > self.balance:
            raise InsufficientCreditsError(balance=self.balance, amount=amount)

        new_balance = self.balance - amount
        self.user_data.edit(name="casino_balance", value=new_balance)
        return amount

    def get_balance(self) -> int:
        balance = self.user_data.retrieve(name="casino_balance")
        if balance is None:
            self.user_data.edit(name="casino_balance", value=0)
            balance = 0
        return balance
