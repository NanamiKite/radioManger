"""Host-level UDP control and owner-scoped QSO subscription."""
import asyncio
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.database.session import get_db, SessionLocal
from app.dependencies import get_current_user, authenticate_token, authenticate_websocket, authenticate_websocket_token
from app.dependencies_admin import get_realtime_user
from app.exceptions import AuthException, RadioManagerException
from app.services.udp_listener_service import udp_listener
from app.services.log_service import LogService
from app.schemas.qso_log import QSOLogCreate

router = APIRouter()


class UDPStartRequest(BaseModel):
    wsjtx_port: Optional[int] = Field(None, ge=1024, le=65535)
    n1mm_port: Optional[int] = Field(None, ge=1024, le=65535)


@router.get("/status")
async def udp_status(current_user=Depends(get_current_user)):
    return {"data": udp_listener.status_for(current_user.id)}


@router.post("/start")
async def udp_start(req: UDPStartRequest, current_user=Depends(get_realtime_user)):
    try:
        await udp_listener.start(current_user.id, req.wsjtx_port, req.n1mm_port)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except OSError as exc:
        raise HTTPException(status_code=409, detail="Cannot bind requested UDP ports") from exc
    return {"data": udp_listener.status_for(current_user.id)}


@router.post("/stop")
async def udp_stop(current_user=Depends(get_realtime_user)):
    await udp_listener.stop(current_user.id)
    return {"data": {"running": False}}


@router.post("/save-to-log")
def save_qso_to_log(qso_data: QSOLogCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    log = LogService.create_log(db, current_user.id, qso_data)
    return {"data": {"id": log.id, "call_sign": log.call_sign}}


def _save_websocket_qso(token: str, data: dict) -> dict:
    qso = QSOLogCreate.model_validate(data)
    with SessionLocal() as db:
        user = authenticate_token(db, token)
        log = LogService.create_log(db, user.id, qso)
        return {"id": log.id, "call_sign": log.call_sign}


@router.websocket("/ws")
async def udp_ws(websocket: WebSocket):
    credentials = await authenticate_websocket(websocket)
    if credentials is None:
        return
    token, user = credentials
    queue = udp_listener.subscribe(user.id)
    received = asyncio.create_task(websocket.receive_text())
    queued = asyncio.create_task(queue.get())
    next_auth = asyncio.get_running_loop().time() + 10
    try:
        while True:
            done, _ = await asyncio.wait({received, queued}, timeout=10, return_when=asyncio.FIRST_COMPLETED)
            if asyncio.get_running_loop().time() >= next_auth:
                await run_in_threadpool(authenticate_websocket_token, token)
                next_auth = asyncio.get_running_loop().time() + 10
            if received in done:
                raw = received.result()
                received = asyncio.create_task(websocket.receive_text())
                try:
                    message = json.loads(raw)
                    if not isinstance(message, dict) or message.get("action") != "save":
                        raise ValueError("Expected action=save with QSO data")
                    result = await run_in_threadpool(_save_websocket_qso, token, message.get("data"))
                    await websocket.send_json({"type": "qso_saved", "data": result})
                except AuthException:
                    raise
                except (ValueError, ValidationError) as exc:
                    await websocket.send_json({"type": "error", "message": str(exc)})
                except RadioManagerException as exc:
                    await websocket.send_json({"type": "error", "message": exc.message})
            if queued in done:
                await asyncio.wait_for(websocket.send_json(queued.result()), timeout=5)
                queued = asyncio.create_task(queue.get())
    except AuthException:
        await websocket.close(code=4401)
    except asyncio.TimeoutError:
        await websocket.close(code=1008, reason="Slow consumer")
    except WebSocketDisconnect:
        pass
    finally:
        udp_listener.unsubscribe(queue)
        received.cancel()
        queued.cancel()
        await asyncio.gather(received, queued, return_exceptions=True)
