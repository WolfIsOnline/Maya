"""
WolfieBot
"""

import os
from dotenv import load_dotenv, find_dotenv

from wolfiebot.logger import Level

# load .env file
load_dotenv(find_dotenv())
MONGODB_CONNECTION = os.environ.get("MONGODB_CONNECTION")
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY")
DISCORD_API_KEY = os.environ.get("DISCORD_API_KEY")
WEBHOOK_ID = os.environ.get("WEBHOOK_ID")
WEBHOOK_TOKEN = os.environ.get("WEBHOOK_TOKEN")
INWORLD_KEY = os.environ.get("INWORLD_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
ASSISTANT_ID = os.environ.get("ASSISTANT_ID")

AI_NAME = "Maya"
PAYDAY = 1000
MIN_SLOT_AMOUNT = 2
DEFAULT_COLOR = 0x02E7E7
CASINO_NAME = "Nocturnia"
CASINO_COLOR = 0xBF40BF
CASINO_SYMBOL = "₵"
CURRENCY_NAME = "Eurodollar"
CURRENCY_ABBR = "ecu"
CURRENCY_SYMBOL = "§"
LOG_LEVEL = Level.DEBUG

__version__ = "2.3.0-alpha"
__authors__ = "WolfIsOnline"
__description__ = f"{AI_NAME} is an AI conversational bot with its own personality."
