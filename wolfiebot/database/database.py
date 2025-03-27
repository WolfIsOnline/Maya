"""Database Manager"""
import threading
from typing import Any, Optional

import hikari
from pymongo import MongoClient

import wolfiebot
from wolfiebot.logger import Logger

log = Logger(__name__, wolfiebot.LOG_LEVEL)


class _MongoDBClient:
    """Singleton for managing a MongoDB client connection.

    Ensures only one instance of the MongoDB client is created in the application.
    Thread safety during instance creation is ensured with threading.Lock.

    Attributes:
        _instance: The singleton instance of the MongoDB client.
        _lock: Lock object for thread-safe instance creation.

    Methods:
        __new__(cls): Creates or retrieves the singleton instance.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Implements singleton pattern for MongoDB client instantiation.

        Returns the existing instance if available, or creates a new one.

        Returns:
            The singleton instance of _MongoDBClient.
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(_MongoDBClient, cls).__new__(cls)
                cls._instance.client = MongoClient(wolfiebot.MONGODB_CONNECTION)
                log.info("database connection established")
            else:
                log.debug("database already connected")
        return cls._instance


class UserData:
    """Manages user data"""

    def __init__(self, user_id: hikari.Snowflake | int) -> None:
        """Initializes UserData instance.

        Args:
          user_id: Discord user ID.
        """
        # pylint: disable=no-member
        self.client = _MongoDBClient().client
        self.document = self.client["wolfie"]["users"]
        self.user_id = user_id

    def edit(self, name: str, value: Any) -> None:
        """Updates or creates a field with the given value in the user document.

        Args:
            name (str): The field name to be updated or created.
            value (Any): The value to set for the field.
        """
        self.document.find_one_and_update(
            {"_id": self.user_id}, {"$set": {name: value}}, upsert=True
        )

    def append(self, name: str, value: Any) -> None:
        """Appends a value to a list field in the user document.

        Args:
            name: The field name to append to.
            value: The value to append to the list.
        """
        self.document.find_one_and_update(
            {"_id": self.user_id}, {"$push": {name: value}}, upsert=True
        )

    def delete(self, name: str) -> None:
        """Removes a specified field from the user's document in the database.

        Args:
            name (str): Field name to be removed.
        """
        self.document.update_one({"_id": self.user_id}, {"$unset": {name: {}}})

    def delete_element(self, name, value):
        """Removes an element from a list field in the user document.

        Args:
            name: The field name containing the list.
            value: The element to remove from the list.
        """
        self.document.find_one_and_update(
            {"_id": self.user_id}, {"$pull": {name: value}}, upsert=True
        )

    def delete_element_by_index(self, name: str, index: int):
        """
        Removes an element from a user's data array by index.

        Args:
            name (str): The name of the data array.
            index (int): The index of the element to remove.
        """
        # this is a work around for removing an array by the index
        # this can cause some future issues but for now it works
        self.document.find_one_and_update(
            {"_id": self.user_id}, {"$unset": {f"{name}.{index}": 1}}, upsert=True
        )
        self.document.find_one_and_update(
            {"_id": self.user_id}, {"$pull": {f"{name}": None}}, upsert=True
        )

    def retrieve(self, name: Optional[str] = None) -> Any:
        """Fetches a specified field's value from the user's document.

        Retrieves the value of the field specified by 'name'. If 'name' is not provided,
        or if the specified field is not found, returns None.

        Args:
            name (str, optional): The name of the field to retrieve. Defaults to None.

        Returns:
            The value of the specified field, or None if not found.
        """
        raw_data = self.document.find({"_id": self.user_id}, {})
        for data in raw_data:
            if name is not None:
                is_present = name in data
                if is_present is False:
                    return None
                return data[name]
        return None

    def ai_edit(self, name: str, value: Any) -> None:
        self.document.find_one_and_update(
            {"_id": self.user_id}, {"$set": {"ai_brain." + name: value}}, upsert=True
        )

    def ai_retrieve(self):
        raw_data = self.document.find({"_id": self.user_id}, {"ai_brain"})
        data = []
        for info in raw_data:
            data.append(info)
        return data[0]

    def ai_delete(self, name: str) -> None:
        self.document.find_one_and_update(
            {"_id": self.user_id}, {"$unset": {f"ai_brain.{name}": ""}}
        )


class GuildData:
    """Manages guild data"""

    def __init__(self, guild_id):
        # pylint: disable=no-member
        self.client = _MongoDBClient().client
        self.document = self.client["wolfie"]["guilds"]
        self.guild_id = guild_id

    def edit(self, name, value):
        self.document.find_one_and_update(
            {"_id": self.guild_id}, {"$set": {name: value}}, upsert=True
        )

    def append(self, name, value):
        self.document.find_one_and_update(
            {"_id": self.guild_id}, {"$push": {name: value}}, upsert=True
        )

    def delete(self, name):
        self.document.update_one({"_id": self.guild_id}, {"$unset": {name: {}}})

    def delete_element(self, name, value):
        self.document.find_one_and_update(
            {"_id": self.guild_id}, {"$pull": {name: value}}, upsert=True
        )

    def delete_element_by_index(self, name: str, index: int):
        """
        Removes an element from a user's data array by index.

        Args:
            name (str): The name of the data array.
            index (int): The index of the element to remove.
        """
        # this is a work around for removing an array by the index
        # this can cause some future issues but for now it works
        self.document.find_one_and_update(
            {"_id": self.guild_id}, {"$unset": {f"{name}.{index}": 1}}, upsert=True
        )
        self.document.find_one_and_update(
            {"_id": self.guild_id}, {"$pull": {f"{name}": None}}, upsert=True
        )

    def retrieve(self, name=None):
        raw_data = self.document.find({"_id": self.guild_id}, {})
        for data in raw_data:
            if name is not None:
                is_present = name in data
                if is_present is False:
                    return None
                return data[name]
        return raw_data
