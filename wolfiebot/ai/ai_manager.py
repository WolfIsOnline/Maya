"""Handles the AI assistant"""

import asyncio
import json
from typing import List, Dict, Optional

import hikari
import openai
from openai.types.beta import threads

import wolfiebot
from wolfiebot.logger import Logger
from wolfiebot.database.database import UserData

log = Logger(__name__, wolfiebot.LOG_LEVEL)


class AIManager:
    """Manages AI assistant"""

    REPLY_CHECK_INTERVAL = 0.5

    def __init__(self, user_id: hikari.Snowflake | int, instruction: str = None):
        """Initializes the AIManager.

        Args:
            user_id: The Discord user ID for the user.

        Initializes the OpenAI client, gets the user's data and conversation
        thread ID. If no thread ID exists, creates a new thread. Also initializes
        a table of internal helper functions.
        """
        self.client = openai.OpenAI(api_key=wolfiebot.OPENAI_API_KEY)
        self.user_data = UserData(user_id=user_id)
        self.thread_id = self.user_data.retrieve(name="thread_id")
        self.user_id = user_id
        self.instruction = instruction
        self.function_table = {
            "_write_to_brain": self._write_to_brain,
            "_retrieve_from_brain": self._retrieve_from_brain,
            "_delete_from_brain": self._delete_from_brain,
            "_view_image": self._view_image,
        }

        if self.thread_id is None:
            self.thread_id = self._create_thread()

    def create_image(self, text: str):
        log.debug("creating an image")
        image = self.client.images.generate(
            model="dall-e-3", prompt=text, n=1, size="1024x1024", quality="standard"
        )
        log.debug("image created")
        return image.data[0].url

    async def send_message(self, text: str, attachment: Optional[str] = None) -> None:
        """
        Sends a message to the AI and retrieves the AI's reply.

        Args:
            text (str): The message text to send to the AI.

        Returns:
            str: The AI's reply message.
        """
        try:
            if not attachment:
                message = await self._add_message(message=text)

            else:
                message = await self._add_message(
                    message=f"{text}: {attachment[0].url}"
                )
            await self._run_reply()
            reply_json = await self._get_reply(message)
            reply = self._parse_reply(reply_json)
            return reply[0] if reply else None

        except openai.BadRequestError as e:
            log.warning(f"BadRequestError: {e.message}")
            return

        except openai.RateLimitError as e:
            log.warning(f"RateLimitError: {e.message}")
            return

        except openai.OpenAIError as e:
            log.error("OpenAIError")
            return

    async def _add_message(self, message: str) -> threads.ThreadMessage:
        """Creates a message in the conversation thread.

        Args:
            message (str): The content of the message to add to the thread.

        Returns:
            Message: The created message object.
        """
        message = self.client.beta.threads.messages.create(
            thread_id=self.thread_id, role="user", content=message
        )
        return message

    async def _get_reply(self, message: str) -> Dict:
        """Retrieves the AI's reply to the given message.

        Args:
            message: The message object that was sent to the AI.

        Returns:
            The JSON response from the OpenAI API containing the AI's reply.
        """
        reply = self.client.beta.threads.messages.list(
            thread_id=self.thread_id, order="asc", after=message.id
        )
        return self._load_json(reply)

    async def _run_reply(self) -> threads.run.Run:
        """
        Initiates a run, checks its status, handles tool calls if required,
        submits tool outputs, and logs activities.
        Continues until the run is completed or no longer active.

        Returns:
            run: the run object
        """
        run = self.client.beta.threads.runs.create(
            thread_id=self.thread_id,
            assistant_id=wolfiebot.ASSISTANT_ID,
            instructions=self.instruction,
        )

        while run.status in ("queued", "in_progress"):
            run = self.client.beta.threads.runs.retrieve(
                thread_id=self.thread_id, run_id=run.id
            )

            if run.status == "requires_action":
                tool_calls = run.required_action.submit_tool_outputs.model_dump()
                tool_output = []

                for call in tool_calls["tool_calls"]:
                    function_name = call["function"]["name"]
                    arguments = json.loads(call["function"]["arguments"])

                    table = self.function_table.get(function_name)
                    if table:
                        result = table(**arguments)

                        # pylint: disable=no-value-for-parameter
                        output = json.dumps() if not isinstance(result, str) else result
                        tool_output.append(
                            {"tool_call_id": call["id"], "output": output}
                        )
                        log.debug(f"function_called: {function_name}")
                        log.debug(f"function_arguments: {arguments}")
                    else:
                        log.warning(f"function_called: {function_name} not found")

                    run = self.client.beta.threads.runs.submit_tool_outputs(
                        thread_id=self.thread_id,
                        run_id=run.id,
                        tool_outputs=tool_output,
                    )
            log.debug("_run_reply().run.status: %s", run.status)
            await asyncio.sleep(AIManager.REPLY_CHECK_INTERVAL)
        return run

    def _create_thread(self) -> str:
        """Creates a new conversation thread and stores the thread ID.

        Returns:
            thread.id: the id of the users thread
        """
        thread = self.client.beta.threads.create()
        self.user_data.edit("thread_id", thread.id)
        return thread.id

    def _parse_reply(self, data) -> List[str]:
        """Parses the reply data from the AI to extract text values.

        Iterates through the nested data structure looking for "text" keys
        that contain a "value" key. Appends any found text values to a list
        and returns the list.

        Args:
            data: The reply data from OpenAI.

        Returns:
            A list of text values extracted from the reply.
        """
        values = []
        for data_item in data["data"]:
            if "content" in data_item:
                for content_item in data_item["content"]:
                    if "text" in content_item and "value" in content_item["text"]:
                        values.append(content_item["text"]["value"])
        return values

    def _load_json(self, data: list):
        """Loads JSON data from the model dump.

        Args:
            data: The model dump data.

        Returns:
            The loaded JSON object.
        """
        return json.loads(data.model_dump_json())

    def _write_to_brain(self, data_name: str, data_value: str) -> str:
        self.user_data.ai_edit(data_name, data_value)
        return f"{data_name} : {data_value}"

    def _retrieve_from_brain(self) -> str:
        data = self.user_data.ai_retrieve()
        return f"here is the information in your brain: {data}"

    def _delete_from_brain(self, data_name: str) -> str:
        self.user_data.ai_delete(data_name)
        return f"{data_name} has been removed"

    def _view_image(self, instruction: str, image_url: str):
        log.debug("_view_image(): instruction=%s", instruction)
        response = self.client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": instruction},
                        {"type": "image_url", "image_url": {"url": image_url}},
                    ],
                }
            ],
            max_tokens=300,
        )
        response = response.choices[0].message.content
        log.debug("view_image(): response: %s", response)
        return response
