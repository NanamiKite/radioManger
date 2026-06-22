from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.logs import router as logs_router
from app.api.v1.stations import router as stations_router
from app.api.v1.locations import router as locations_router
from app.api.v1.stats import router as stats_router
from app.api.v1.callsigns import router as callsigns_router
from app.api.v1.sync import router as sync_router
from app.api.v1.shortcuts import router as shortcuts_router
from app.api.v1.dxcluster import router as dxcluster_router
from app.api.v1.map import router as map_router
from app.api.v1.udp import router as udp_router

__all__ = [
    "auth_router",
    "users_router",
    "logs_router",
    "stations_router",
    "locations_router",
    "stats_router",
    "callsigns_router",
    "sync_router",
    "shortcuts_router",
    "dxcluster_router",
    "map_router",
    "udp_router",
]
