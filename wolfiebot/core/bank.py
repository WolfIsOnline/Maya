"""Banking System"""
import uuid
import datetime

import wolfiebot
from wolfiebot.database.database import UserData
from wolfiebot.logger import Logger


log = Logger(__name__, wolfiebot.LOG_LEVEL)


class InsufficientFundsError(Exception):
    """Exception raised when a withdrawal attempt exceeds the available balance."""

    def __init__(self, amount: int, balance: int, message: str = "InsufficientFunds"):
        self.amount = amount
        self.balance = balance
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}: amount "{self.amount}" > "{self.balance}"'


class NegativeFundsWithdrawalError(ValueError):
    """Exception raised when a withdrawal amount is negative."""

    def __init__(self, amount, message="NegativeWithdrawal"):
        self.amount = amount
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f'{self.message}: amount "{self.amount}" is < 0'


class Bank:
    """
    A class representing a bank.

    Provides methods for depositing, withdrawing, transferring funds,
    and checking balance
    """

    def __init__(self, user_id):
        self.user_data = UserData(user_id=user_id)
        self.user_id = user_id
        self.balance = self.get_balance()

    async def deposit(self, amount: int, statement: str) -> None:
        """Deposit funds into the user's account and record the transaction.

        Args:
            amount (int): The amount to deposit.
            statement (str): A statement describing the deposit transaction.

        """
        if amount < 0:
            raise NegativeFundsWithdrawalError

        new_balance = self.balance + amount
        transaction_id = uuid.uuid4().hex
        data = {
            "id": transaction_id,
            "amount": amount,
            "date": datetime.datetime.now(),
            "type": "deposit",
            "statement": statement,
        }
        self.user_data.append(name="transactions", value=data)
        self.user_data.edit(name="balance", value=new_balance)

    async def withdraw(self, amount: int, statement: str) -> int:
        """Withdraw funds from the user's account if sufficient balance is available.

        Raises InsufficientFundsError if withdrawal amount exceeds available balance.
        Records the transaction by updating the user's balance and transaction history.

        Args:
          amount (int): The amount to withdraw.
          statement (str): A statement describing the withdrawal.

        Returns:
          int: amount withdrawn
        """
        if amount > self.balance:
            raise InsufficientFundsError(amount=amount, balance=self.balance)

        new_balance = self.balance - amount

        transaction_id = uuid.uuid4().hex
        data = {
            "id": transaction_id,
            "amount": amount,
            "date": datetime.datetime.now(),
            "type": "withdraw",
            "statement": statement,
        }
        self.user_data.append(name="transactions", value=data)
        self.user_data.edit(name="balance", value=new_balance)
        return amount

    async def transfer(
        self, receiver_id, amount: int, sender_statment: str, receiver_statment: str
    ) -> int | str:
        """
        Transfer funds from one user's account to another and record the transactions.

        Args:
            receiver_id (Any): The ID of the receiver.
            amount (int): The amount to transfer.
            sender_statement (str): A statement from the sender's perspective.
            receiver_statement (str): A statement from the receiver's perspective.

        Returns:
            int: The transferred amount if the transfer is successful, otherwise -1.
        """
        receiver_account = Bank(receiver_id)

        try:
            confirmed_amount = await self.withdraw(
                amount=amount, statement=sender_statment
            )
        except InsufficientFundsError as exc:
            log.error(exc)
            raise exc

        await receiver_account.deposit(
            amount=confirmed_amount, statement=receiver_statment
        )
        return confirmed_amount

    def get_balance(self) -> int:
        """
        Get the balance of the user.

        Args:
            user_id (Any): The ID of the user.

        Returns:
            int: The balance of the user.
        """
        balance = self.user_data.retrieve("balance")
        if balance is None:
            self.user_data.edit(name="balance", value=0)
            balance = 0
        return balance
