import json
from typing import Optional, Dict

from fastapi import APIRouter, status, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from maya.database import Database


class LogsChannelID(BaseModel):
    """Pydantic model for storing the Discord logs channel ID."""

    logs_channel_id: int


class ColorChannel(BaseModel):
    """Pydantic model for storing color data"""

    color_channel_id: Optional[int] = None
    color_message_id: Optional[int] = None
    color_roles: Optional[Dict[str, int]] = None


class GuildID(BaseModel):
    """Pydantic model for storing the guild id"""

    guild_id: int


guild_router = APIRouter()


@guild_router.get("/")
async def get_guilds() -> JSONResponse:
    """Retrieve all guild IDs from the database.

    Raises:
        HTTPException: If a database error occurs during the query.

    Returns:
        JSONResponse: 200 OK with a list of guild IDs if found,
                      404 Not Found if no guilds exist.
    """
    database = Database()
    try:
        with database.open_pool() as cursor:
            cursor.execute("SELECT guild_id FROM Guilds")
            result = cursor.fetchall()
            if result:
                return JSONResponse(
                    status_code=status.HTTP_200_OK, content={"guild_ids": result}
                )
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"message": "No guilds found"},
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}") from e


@guild_router.post("/")
async def add_guild(guild_id: GuildID) -> JSONResponse:
    """Adds guild ID to the database.

    Raises:
        HTTPException: If a database error occurs during the query.

    Returns:
        JSONResponse: 201 CREATED if added
    """
    database = Database()
    try:
        with database.open_pool() as cursor:
            cursor.execute(
                "INSERT INTO Guilds (guild_id) VALUES (%s)", (guild_id.guild_id,)
            )
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content=f"{guild_id.guild_id} added",
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}") from e


@guild_router.get("/{guild_id}/logs-channel")
async def get_logs_channel(guild_id: int) -> JSONResponse:
    """Retrieves log channel id from the database.

    Raises:
        HTTPException: If a database error occurs during the query.

    Returns:
        JSONResponse: 200 OK if found
                      404 NOT_FOUND if it cannnot be located
    """
    database = Database()
    try:
        with database.open_pool() as cursor:
            cursor.execute(
                "SELECT logs_channel_id FROM Guilds WHERE guild_id = %s", (guild_id,)
            )
            result = cursor.fetchone()
            if result and result[0] is not None:
                return JSONResponse(
                    status_code=status.HTTP_200_OK,
                    content={"logs_channel_id": result[0]},
                )
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"message": "Logs channel not found"},
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}") from e


@guild_router.post("/{guild_id}/logs-channel")
async def set_logs_channel(guild_id: int, channel_id: LogsChannelID) -> JSONResponse:
    """Sets log channel id in the database.

    Raises:
        HTTPException: If a database error occurs during the query.

    Returns:
        JSONResponse: 200 OK if it was updated
    """
    database = Database()
    try:
        with database.open_pool() as cursor:
            cursor.execute(
                "UPDATE Guilds SET logs_channel_id = %s WHERE guild_id = %s",
                (channel_id.logs_channel_id, guild_id),
            )
            if cursor.rowcount == 0:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"message": f"Guild {guild_id} not found"},
                )
            return JSONResponse(
                status_code=status.HTTP_200_OK, content="Logs channel updated"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}") from e


@guild_router.get("/{guild_id}/color-channel")
async def get_color_channel(guild_id: int) -> JSONResponse:
    """Gets color channel information from database.

    Raises:
        HTTPException: If a database error occurs during the query.

    Returns:
        JSONResponse: 200 OK if found
                      404 NOT_FOUND if it cannnot be located
    """
    database = Database()
    try:
        with database.open_pool() as cursor:
            cursor.execute(
                """
                SELECT color_channel_id, color_message_id, color_roles
                FROM Guilds
                WHERE guild_id = %s
                """,
                (guild_id,),
            )
            result = cursor.fetchone()
            if result:
                color_channel_id, color_message_id, color_roles = result
                if color_channel_id or color_message_id or color_roles:
                    response_data = {}
                    if color_channel_id is not None:
                        response_data["color_channel_id"] = color_channel_id
                    if color_message_id is not None:
                        response_data["color_message_id"] = color_message_id
                    if color_roles is not None:
                        response_data["color_roles"] = color_roles
                    return JSONResponse(
                        status_code=status.HTTP_200_OK, content=response_data
                    )
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"message": "Color data not found"},
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}") from e


@guild_router.post("/{guild_id}/color-channel")
async def set_color_channel(guild_id: int, color_channel: ColorChannel) -> JSONResponse:
    """Sets color channel data in database.

    Raises:
        HTTPException: If a database error occurs during the query.

    Returns:
        JSONResponse: 200 OK if it was updated
                      400 BAD_REQUEST if no POST data was provided
                      404 NOT_FOUND if the guild cannot be found
    """
    database = Database()
    try:
        with database.open_pool() as cursor:
            updates = []
            params = []

            if color_channel.color_channel_id is not None:
                updates.append("color_channel_id = %s")
                params.append(color_channel.color_channel_id)

            if color_channel.color_message_id is not None:
                updates.append("color_message_id = %s")
                params.append(color_channel.color_message_id)

            if color_channel.color_roles is not None:
                updates.append("color_roles = %s")
                # Serialize the dictionary to a JSON string
                params.append(json.dumps(color_channel.color_roles))

            if not updates:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"message": "No color channel data provided to update"},
                )

            params.append(guild_id)
            query = f"""
                UPDATE Guilds
                SET {', '.join(updates)}
                WHERE guild_id = %s
            """
            cursor.execute(query, params)

            if cursor.rowcount == 0:
                return JSONResponse(
                    status_code=status.HTTP_404_NOT_FOUND,
                    content={"message": f"Guild {guild_id} not found"},
                )

            return JSONResponse(
                status_code=status.HTTP_200_OK, content="Color channel updated"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}") from e
