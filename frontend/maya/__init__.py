import os

from dotenv import load_dotenv

load_dotenv()
BACKEND_URL = os.environ.get("BACKEND_URL")
OWNER_ID = os.environ.get("OWNER_ID")
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
DEBUG_GUILD = os.environ.get("DEBUG_GUILD")
