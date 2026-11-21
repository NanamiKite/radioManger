"""Shared DX Cluster connection: public spots, controlled host-level mutations."""
import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.database.session import get_db
from app.dependencies import get_current_user, authenticate_websocket, authenticate_websocket_token
from app.dependencies_admin import get_realtime_user
from app.exceptions import AuthException
from app.models.user import User
from app.schemas.dxcluster import SpotResponse, NodeInfoResponse, ClusterStatusResponse, SwitchNodeRequest, ConnectResult
from app.services.dxcluster_manager import dxcluster_manager, DXClusterManager, NodeInfo
from app.services.location_service import LocationService
from app.services.station_service import StationService

logger = logging.getLogger("radiomanager.dxcluster")
router = APIRouter()


def _resolve_callsign(db: Session, user: User) -> str:
    location = LocationService.get_active_location(db, user.id)
    if location is None:
        raise HTTPException(status_code=409, detail="Create and activate a station location first")
    return StationService.get_station(db, location.station_id, user.id).callsign


def _find_node(host: str, port: int) -> NodeInfo:
    for node in DXClusterManager.get_nodes():
        if node["host"] == host and node["port"] == port:
            return NodeInfo(**node)
    raise HTTPException(status_code=422, detail="DX Cluster endpoint is not configured")


@router.get("/nodes", response_model=list[NodeInfoResponse])
def list_nodes(current_user: User = Depends(get_current_user)):
    return DXClusterManager.get_nodes()


@router.get("/status", response_model=ClusterStatusResponse)
async def get_status(current_user: User = Depends(get_current_user)):
    return dxcluster_manager.status()


@router.get("/spots", response_model=list[SpotResponse])
def get_spots(limit: int = Query(50, ge=1, le=100), current_user: User = Depends(get_current_user)):
    return dxcluster_manager.get_history(limit)


@router.post("/connect", response_model=ConnectResult)
async def connect_node(req: SwitchNodeRequest, db: Session = Depends(get_db), current_user: User = Depends(get_realtime_user)):
    node = _find_node(req.node_host, req.node_port)
    callsign = await run_in_threadpool(_resolve_callsign, db, current_user)
    try:
        state = await dxcluster_manager.connect(node, callsign)
    except ConnectionError as exc:
        raise HTTPException(status_code=502, detail="DX Cluster connection failed") from exc
    return ConnectResult(success=True, message=f"Connected to {node.name}", status=state)


@router.post("/disconnect", response_model=ClusterStatusResponse)
async def disconnect_node(current_user: User = Depends(get_realtime_user)):
    return await dxcluster_manager.disconnect()


@router.websocket("/ws")
async def dxcluster_ws(ws: WebSocket):
    credentials = await authenticate_websocket(ws)
    if credentials is None:
        return
    token, user = credentials
    queue = await dxcluster_manager.subscribe()
    received = asyncio.create_task(ws.receive_text())
    queued = asyncio.create_task(queue.get())
    next_auth = asyncio.get_running_loop().time() + 10
    try:
        for spot in reversed(dxcluster_manager.get_history(limit=100)):
            await asyncio.wait_for(ws.send_json({"type": "spot", "data": spot}), timeout=5)
        while True:
            done, _ = await asyncio.wait({received, queued}, timeout=10, return_when=asyncio.FIRST_COMPLETED)
            if received in done:
                received.result()  # A close frame raises WebSocketDisconnect immediately.
                received = asyncio.create_task(ws.receive_text())
            if asyncio.get_running_loop().time() >= next_auth:
                await run_in_threadpool(authenticate_websocket_token, token)
                next_auth = asyncio.get_running_loop().time() + 10
            if queued in done:
                item = queued.result()
                message = item if isinstance(item, dict) else {"type": "spot", "data": item.to_dict()}
                await asyncio.wait_for(ws.send_json(message), timeout=5)
                queued = asyncio.create_task(queue.get())
    except AuthException:
        await ws.close(code=4401)
    except asyncio.TimeoutError:
        await ws.close(code=1008, reason="Slow consumer")
    except WebSocketDisconnect:
        logger.info("DX WebSocket closed (user=%s)", user.id)
    finally:
        await dxcluster_manager.unsubscribe(queue)
        received.cancel()
        queued.cancel()
        await asyncio.gather(received, queued, return_exceptions=True)
