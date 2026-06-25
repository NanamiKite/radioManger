"""DX Cluster 路由：节点查询、连接管理、历史 spot、WebSocket 实时推送。"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.dependencies import get_current_user
from app.config import settings
from app.models.user import User
from app.models.station import Station
from app.schemas.dxcluster import (
    SpotResponse,
    NodeInfoResponse,
    ClusterStatusResponse,
    SwitchNodeRequest,
    ConnectResult,
)
from app.services.dxcluster_manager import (
    dxcluster_manager,
    DXClusterManager,
    NodeInfo,
    PRESET_NODES,
)
from app.services.location_service import LocationService
from app.utils.security import SecurityUtils

logger = logging.getLogger("radiomanager.dxcluster")
router = APIRouter()


def _resolve_callsign(db: Session, user: User) -> str:
    """从用户激活位置推断台站呼号，用作 cluster 登录名。

    优先级：激活位置所属台站的 callsign。
    Raises:
        HTTPException 409: 没有激活位置 / 台站，无法登录 cluster。
    """
    active_loc = LocationService.get_active_location(db, user.id)
    if not active_loc or not active_loc.station_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No active station with callsign. Please create and activate a station first.",
        )
    station = db.query(Station).filter(Station.id == active_loc.station_id).first()
    if not station or not station.callsign:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Active station has no callsign.",
        )
    return station.callsign


def _find_node(host: str, port: int) -> NodeInfo:
    """根据 host+port 查找预设节点；未命中则构造临时节点对象。"""
    for n in PRESET_NODES:
        if n.host == host and n.port == port:
            return n
    return NodeInfo(host=host, port=port, name=f"{host}:{port}", country="Unknown", remark="自定义节点")


# ----------------------------------------------------------------------
# REST 端点
# ----------------------------------------------------------------------
@router.get("/nodes", response_model=list[NodeInfoResponse])
async def list_nodes(current_user: User = Depends(get_current_user)):
    """返回预设 DX Cluster 节点列表。"""
    return DXClusterManager.get_nodes()


@router.get("/status", response_model=ClusterStatusResponse)
async def get_status(current_user: User = Depends(get_current_user)):
    """返回当前 cluster 连接状态。"""
    return dxcluster_manager.status()


@router.get("/spots", response_model=list[SpotResponse])
async def get_spots(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
):
    """返回最近 N 条历史 spot（新→旧）。"""
    return dxcluster_manager.get_history(limit=limit)


@router.post("/connect", response_model=ConnectResult)
async def connect_node(
    req: SwitchNodeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """连接/切换到指定节点。用当前用户激活台站呼号登录。"""
    callsign = _resolve_callsign(db, current_user)
    node = _find_node(req.node_host, req.node_port)
    try:
        st = await dxcluster_manager.connect(node, callsign)
        return ConnectResult(success=True, message=f"Connected to {node.name}", status=st)
    except Exception as e:
        logger.error("Connect failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(e),
        )


@router.post("/disconnect", response_model=ClusterStatusResponse)
async def disconnect_node(current_user: User = Depends(get_current_user)):
    """断开当前 cluster 连接。"""
    return await dxcluster_manager.disconnect()


# ----------------------------------------------------------------------
# WebSocket：实时推送 spot
# ----------------------------------------------------------------------
async def _authenticate_ws(ws: WebSocket) -> User:
    """从 query param ?token=xxx 鉴权 WebSocket 连接。

    浏览器原生 WebSocket 不支持自定义 header，故用 query param 传 token。

    ⚠️ 安全提示: JWT 放在 URL query 中会被记录在 access log、浏览器历史、代理日志中。
    长期方案应改为 WebSocket 建立后首条消息发送 token，或使用短期专用 token。
    """
    token = ws.query_params.get("token")
    if not token:
        await ws.close(code=4401)
        raise HTTPException(status_code=401, detail="Missing token")

    from app.database.session import SessionLocal
    db = SessionLocal()
    payload = SecurityUtils.decode_token(token)
    user_id = payload.get("sub")
    jti = payload.get("jti")
    if not user_id:
        await ws.close(code=4401)
        raise HTTPException(status_code=401, detail="Invalid token")

    # 检查 token 黑名单（所有模式）
    if jti:
        from app.services.token_blacklist_service import token_blacklist
        if token_blacklist.is_blacklisted(jti):
            await ws.close(code=4401)
            raise HTTPException(status_code=401, detail="Token revoked")

    from app.models.user import User as UserModel
    user = db.query(UserModel).filter(UserModel.id == int(user_id)).first()
    if not user or user.is_deleted or not user.is_active:
        await ws.close(code=4401)
        raise HTTPException(status_code=401, detail="User not found or disabled")

    # 预加载字段后关闭 session
    _ = user.username
    _ = user.id
    db.close()
    return user


@router.websocket("/ws")
async def dxcluster_ws(ws: WebSocket):
    """DX Cluster 实时 spot WebSocket。

    鉴权后:
      1. 推送当前历史 spot（一次性）
      2. 持续推送后续实时 spot
      3. 连接断开时推送 {"type":"disconnect"} 提示前端
    """
    try:
        user = await _authenticate_ws(ws)
    except HTTPException:
        return  # _authenticate_ws 已 close

    await ws.accept()
    logger.info("DX cluster WS client connected (user=%s)", user.username)

    # 推送历史 spot
    history = dxcluster_manager.get_history(limit=100)
    logger.info("WS pushing %d history spots to client", len(history))
    for spot_dict in history:
        try:
            await ws.send_json({"type": "spot", "data": spot_dict})
        except Exception:
            break

    # 订阅实时流
    queue = await dxcluster_manager.subscribe()
    logger.info("WS client subscribed to real-time stream (subscribers=%d)", dxcluster_manager.subscriber_count)
    try:
        while True:
            item = await queue.get()
            if isinstance(item, dict) and item.get("type") == "disconnect":
                logger.info("WS sending disconnect notification to client")
                await ws.send_json({"type": "disconnect", "message": "cluster disconnected"})
                continue
            # SpotData 实例
            await ws.send_json({"type": "spot", "data": item.to_dict()})
    except WebSocketDisconnect:
        logger.info("DX cluster WS client disconnected (user=%s)", user.username)
    except Exception as e:
        logger.error("DX cluster WS error: %s", e)
    finally:
        await dxcluster_manager.unsubscribe(queue)
        try:
            await ws.close()
        except Exception:
            pass
