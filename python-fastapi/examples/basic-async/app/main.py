from __future__ import annotations

import logging
import sys

import fastapi
import gel

from app import auth, users, events, ui


formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)

logger = logging.getLogger("fast_jelly")
logger.setLevel(logging.DEBUG)
logger.addHandler(stream_handler)

auth_core_logger = logging.getLogger("gel.auth")
auth_core_logger.setLevel(logging.DEBUG)
auth_core_logger.addHandler(stream_handler)


async def startup():
    fast_api.state.client = await gel.create_async_client().ensure_connected()


async def shutdown():
    await fast_api.state.client.aclose()


fast_api = fastapi.FastAPI(
    title="Jellyrole",
    on_startup=[startup],
    on_shutdown=[shutdown],
)
fast_api.include_router(ui.router)
fast_api.include_router(auth.router, prefix="/auth")

api_router = fastapi.APIRouter()
api_router.include_router(users.router)
api_router.include_router(events.router)

fast_api.include_router(api_router, prefix="/api")
