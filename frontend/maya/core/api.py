from typing import Optional

import requests

from frontend.discord.core.logs import log
from frontend.discord import BACKEND_URL

TIMEOUT = 10


class API:
    """Handles all calls to the backend API"""

    def get_guild_data(self, guild_id: int, endpoint: str, data: Optional[str] = None):
        """Calls get requests to the Backend API.

        Args:
            guild_id (int): id of the guild you are getting from
            endpoint (str): endpoint path
            data (Optional[str], optional): data being retrieved. Defaults to None.

        Returns:
            dict: the data requested from the api. Returns none if nothing is found
        """
        try:
            response = requests.get(
                f"{BACKEND_URL}/guilds/{guild_id}/{endpoint}", timeout=TIMEOUT
            )
            if response.status_code == 200:
                response_data = response.json()
                if data is None:
                    return response_data
                return response_data.get(data)
            return None
        except requests.RequestException as e:
            log.error("API request failed: %s", e)
            raise

    def set_guild_data(self, guild_id: int, endpoint: str, value):
        """Calls post requests to the Backend API.
        Args:
            guild_id (int): id of the guild you are getting from
            endpoint (str): endpoint path
            value (_type_): value to be set

        Raises:
            requests.RequestException: raises any errors and prints response

        Returns:
            status code: the response code
        """
        try:
            response = requests.post(
                f"{BACKEND_URL}/guilds/{guild_id}/{endpoint}",
                timeout=TIMEOUT,
                json=value,
            )
            if response.status_code in (200, 201):
                return response.status_code
            log.error(
                "API request failed with status %s: %s",
                response.status_code,
                response.text,
            )
            raise requests.RequestException(
                f"Failed to set guild data: {response.status_code} {response.text}"
            )
        except requests.RequestException as e:
            log.error("API request failed: %s", e)
            raise
