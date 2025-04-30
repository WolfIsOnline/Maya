import uvicorn

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

from maya.logs import log
from maya.database import Database
from maya.routers.guild import guild_router

from maya import VERSION_SHORT, MAYA_HOST, MAYA_PORT, MAYA_RELOAD


async def life(_maya: FastAPI):
    """Manage Maya's life"""
    log.info("Maya v%s backend started", _maya.version)
    database = Database()
    database.init()
    yield
    log.info("Maya API shutting down")


maya = FastAPI(lifespan=life)
maya.include_router(guild_router, prefix=f"/v{VERSION_SHORT}/guilds")


@maya.get(f"/v{VERSION_SHORT}/status")
async def get_status():
    """Check API status"""
    response = status.HTTP_200_OK
    return JSONResponse(status_code=response, content=response)


def main():
    uvicorn.run("maya.main:maya", host=MAYA_HOST, port=MAYA_PORT, reload=MAYA_RELOAD)
