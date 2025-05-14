from contextlib import contextmanager

from fastapi import HTTPException, status

from mysql.connector.pooling import MySQLConnectionPool
from mysql.connector import IntegrityError, Error, Connect

from pydantic import ValidationError

from dotenv import load_dotenv

from maya import MARIADB_HOST, MARIADB_USER, MARIADB_PASSWORD, MARIADB_DB, MARIADB_PORT

from maya.logs import log


load_dotenv()


class SQL:
    """Handles MYSQL pool connections"""

    def __init__(self):
        self.pool = None
        self.db_config = {
            "host": MARIADB_HOST,
            "user": MARIADB_USER,
            "password": MARIADB_PASSWORD,
            "database": MARIADB_DB,
            "port": MARIADB_PORT,
        }

    # this is pointless right now
    # since Connect() class handles connection
    def init(self):
        """Connect to a MYSQL Pool"""
        try:
            self.pool = MySQLConnectionPool(
                pool_name="maya",
                pool_size=5,
                autocommit=True,
                **self.db_config,
            )
            log.info("Database connected to %s on %s", MARIADB_DB, MARIADB_HOST)

            self._init_schema()

        except Error as e:
            log.error("Could not connect to database: %s", e)

    @contextmanager
    def open_pool(self):
        """Context manager to open a MySQL connection and yield a cursor.

        Raises:
            HTTPException: If database configuration is invalid (400 - ValidationError).
            HTTPException: If a constraint violation occurs (409 - IntegrityError).
            HTTPException: If a generic database error occurs (500 - Error).

        Yields:
            Cursor: A MySQL cursor object for executing database operations.
        """

        connection = None
        try:
            connection = Connect(
                autocommit=True, **self.db_config, pool_name="maya", pool_size=5
            )
            log.debug("Connected to pool %s", connection.connection_id)
            cursor = connection.cursor()
            yield cursor
        except ValidationError as ve:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"ValidationError: {ve}",
            ) from ve
        except IntegrityError as ie:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail=f"IntegrityError: {ie}"
            ) from ie
        except Error as e:
            log.warning("Database error: %s", e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Internal error: {e}",
            ) from e

        finally:
            if connection:
                connection.close()

    def _init_schema(self):
        """Initialize the database schema"""
        try:
            with self.open_pool() as cursor:
                cursor.execute(
                    """
                        CREATE TABLE IF NOT EXISTS Guilds (
                            guild_id BIGINT PRIMARY KEY,
                            logs_channel_id BIGINT DEFAULT NULL,
                            color_channel_id BIGINT DEFAULT NULL,
                            color_message_id BIGINT DEFAULT NULL,
                            color_roles JSON DEFAULT NULL
                        )
                    """
                )
                log.debug("Guilds table ensured with all columns")

                cursor.execute(
                    """
                        CREATE TABLE IF NOT EXISTS Users (
                            user_id BIGINT PRIMARY KEY
                        )
                    """
                )
                log.debug("Users table ensured")

        except Exception as e:
            log.error("Failed to initialize database schema: %s", str(e))
            raise RuntimeError(
                f"Database schema initialization failed: {str(e)}"
            ) from e
