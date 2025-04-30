import os

from dotenv import load_dotenv

load_dotenv()


def _get_env_bool(name: str, default: bool = False) -> bool:
    env = os.getenv(name)
    if env is None or env == "":
        return default
    return env.lower() in ("true", "1")


MAYA_RELOAD = _get_env_bool(name="MAYA_RELOAD")

VERSION_SHORT = "1"
VERION_LONG = "1.0.0"

MARIADB_HOST = os.getenv("MARIADB_HOST")
MARIADB_USER = os.getenv("MARIADB_USER")
MARIADB_PASSWORD = os.getenv("MARIADB_PASSWORD")
MARIADB_DB = os.getenv("MARIADB_DB")

MAYA_HOST = os.getenv("MAYA_HOST")
MAYA_PORT = int(os.getenv("MAYA_PORT"))
