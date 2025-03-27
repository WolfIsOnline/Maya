"""
Inworld Simple API Wrapper
"""
import requests

import wolfiebot

WORKSPACE_ID = "default-firdbgosgclm_v_vu5dcnw"
BASE_URL = "https://studio.inworld.ai"


class OpenSessionData:
    """
    Data class for storing information required to open a session.

    Attributes:
        user_id (int): The ID of the user.
        name (str): The name of the user.
        gender (str): The gender of the user.
        age (int): The age of the user.
    """

    user_id: int
    name: str
    gender: str
    age: int


class Simple_API:
    """
    A class for interacting with a simple API.

    This class provides functions for opening sessions and sending messages via the API.
    """

    async def open_session(self, data: OpenSessionData):
        """
        Opens a new session with the API.

        Args:
            data (OpenSessionData): An instance of OpenSessionData containing user information.

        Returns:
            dict: A JSON response from the API with session information.
        """
        url = f"{BASE_URL}/v1/workspaces/{WORKSPACE_ID}/characters/wolfie:openSession"
        headers = {
            "Content-Type": "application/json",
            "authorization": f"Basic {wolfiebot.INWORLD_KEY}",
        }
        data = {
            "name": f"workspaces/{WORKSPACE_ID}/characters/wolfie",
            "user": {
                "endUserId": data.get("user_id"),
                "givenName": data.get("name"),
                "gender": data.get("gender"),
                "role": "member",
                "age": data.get("age"),
            },
        }
        session = requests.post(url=url, json=data, headers=headers, timeout=10)
        return session.json()

    async def send_message(self, message: str, session_id: str, character_id: str):
        """
        Sends a message using an existing session and character.

        Args:
            message (str): The message to be sent.
            session_id (str): The session ID.
            character_id (str): The character ID.

        Returns:
            dict: A JSON response from the API confirming the sent message.
        """
        url = f"{BASE_URL}/v1/workspaces/{WORKSPACE_ID}/sessions/{session_id}/sessionCharacters/{character_id}:sendText"
        headers = {
            "Content-Type": "application/json",
            "authorization": f"Basic {wolfiebot.INWORLD_KEY}",
            "Grpc-Metadata-session-id": f"{session_id}",
        }
        message = {"text": message}
        response = requests.post(url=url, json=message, headers=headers, timeout=10)
        return response.json()

    async def send_simple_message(self, username: str, user_id: str, message: str):
        """
        Sends a simple message using a character and user information.

        Args:
            username (str): The username of the recipient.
            user_id (str): The ID of the recipient user.
            message (str): The message to be sent.

        Returns:
            dict: A JSON response from the API confirming the sent message.
        """
        url = f"{BASE_URL}/v1/workspaces/default-firdbgosgclm_v_vu5dcnw/characters/wolfie:simpleSendText"
        headers = {
            "Content-Type": "application/json",
            "authorization": f"Basic {wolfiebot.INWORLD_KEY}",
        }
        data = {
            "character": "workspaces/default-firdbgosgclm_v_vu5dcnw/characters/wolfie",
            "text": message,
            "endUserFullname": username,
            "endUserId": user_id,
        }
        response = requests.post(url=url, json=data, headers=headers, timeout=10)

        return response.json()

    async def send_trigger_message(
        self, session_id: str, character_id: str, trigger: str
    ):
        """
        Sends a trigger message using an existing session and character.

        Args:
            session_id (str): The session ID.
            character_id (str): The character ID.
            trigger (str): The trigger to be sent.

        Returns:
            dict: A JSON response from the API confirming the sent trigger.
        """
        url = f"{BASE_URL}/v1/workspaces/{WORKSPACE_ID}/sessions/{session_id}/sessionCharacters/{character_id}:sendTrigger"
        headers = {
            "Content-Type": "application/json",
            "authorization": f"Basic {wolfiebot.INWORLD_KEY}",
            "Grpc-Metadata-session-id": f"{session_id}",
        }
        data = {
            "triggerEvent": {"trigger": f"workspaces/{WORKSPACE_ID}/triggers/{trigger}"}
        }

        response = requests.post(url=url, json=data, headers=headers, timeout=10)
        return response.json()
