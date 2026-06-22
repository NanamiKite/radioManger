"""UDP 监听控制 API + WebSocket 实时推送"""

import json
import logging
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database.session import get_db
from app.dependencies import get_current_user
from app.services.udp_listener_service import udp_listener
from app.services.log_service import LogService
from app.schemas.qso_log import QSOLogCreate
from app.utils.security import SecurityUtils

logger = logging.getLogger("radiomanager.udp")
router = APIRouter()


class UDPStartRequest(BaseModel):
    wsjtx_port: Optional[int] = None
    n1mm_port: Optional[int] = None


@router.get("/status")
async def udp_status(current_user=Depends(get_current_user)):
    """获取 UDP 监听状态"""
    return {"data": udp_listener.status}


@router.post("/start")
async def udp_start(
    req: UDPStartRequest,
    current_user=Depends(get_current_user),
):
    """启动 UDP 监听"""
    if udp_listener.is_running:
        return {"data": udp_listener.status}
    await udp_listener.start(
        wsjtx_port=req.wsjtx_port,
        n1mm_port=req.n1mm_port,
    )
    return {"data": udp_listener.status}


@router.post("/stop")
async def udp_stop(current_user=Depends(get_current_user)):
    """停止 UDP 监听"""
    await udp_listener.stop()
    return {"data": {"running": False}}


@router.post("/save-to-log/{user_id}")
async def save_qso_to_log(
    user_id: int,
    qso_data: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """将接收到的 QSO 数据保存为日志（由前端调用或自动保存）"""
    try:
        create_data = QSOLogCreate(**qso_data)
        log = LogService.create_log(db, current_user.id, create_data)
        return {"data": {"id": log.id, "call_sign": log.call_sign}}
    except Exception as e:
        return {"error": str(e)}


@router.websocket("/ws")
async def udp_ws(websocket: WebSocket):
    """WebSocket 实时推送接收到的 QSO

    连接时需要在 query 参数中传递 token:
    ws://host/api/v1/udp/ws?token={jwt_token}
    """
    # 验证 token
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001, reason="Missing token")
        return
    try:
        payload = SecurityUtils.decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=4001, reason="Invalid token")
            return
    except Exception:
        await websocket.close(code=4001, reason="Invalid token")
        return

    await websocket.accept()
    udp_listener.register_ws(websocket)
    logger.info(f"UDP WebSocket client connected (user {user_id})")

    try:
        while True:
            # 保持连接，接收前端消息（如确认保存）
            msg = await websocket.receive_text()
            try:
                data = json.loads(msg)
                if data.get("action") == "save":
                    # 前端确认保存 QSO 到数据库
                    qso_data = data.get("data", {})
                    if qso_data:
                        from app.database.base import SessionLocal
                        db = SessionLocal()
                        try:
                            create_data = QSOLogCreate(**qso_data)
                            log = LogService.create_log(db, int(user_id), create_data)
                            await websocket.send_json({
                                "type": "qso_saved",
                                "data": {"id": log.id, "call_sign": log.call_sign},
                            })
                        except Exception as e:
                            await websocket.send_json({"type": "error", "message": str(e)})
                        finally:
                            db.close()
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        pass
    finally:
        udp_listener.unregister_ws(websocket)
        logger.info(f"UDP WebSocket client disconnected (user {user_id})")
