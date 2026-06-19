"""DX Cluster 连接管理器（全局单例）。

使用原生 asyncio socket 维护到 DX Cluster 节点的 telnet 连接，
实时接收 spot，存入内存环形缓冲，并广播给所有 WebSocket 订阅者。

设计要点:
    - 单例模式：模块级 `dxcluster_manager` 实例，整个进程共享一个 telnet 连接。
    - 纯内存：spot 存 deque(maxlen=200)，不落库。
    - 异步：基于 asyncio，与 FastAPI 事件循环共存。
    - 不自动重连：连接断开仅标记状态，由前端触发重连（避免无人看时疯狂重连）。

多 worker 约束:
    本管理器是进程内单例。若 uvicorn 以多 worker 启动（config.py 默认 WORKERS=4），
    每个 worker 会建立独立的 telnet 连接。当前部署（start-*.sh / Dockerfile）
    实际单 worker，不受影响。如需多 worker 共享，需引入 Redis pub/sub，
    但 telnet socket 本身无法跨进程序列化，仍需选一个 worker 作单点连接。

参考:
    - DX Spider 协议: https://www.dxcluster.org/adminmanual_en-11.html
    - Python asyncio streams: https://docs.python.org/3/library/asyncio-stream.html
"""

from __future__ import annotations

import asyncio
import logging
from collections import deque
from dataclasses import dataclass, asdict
from typing import Optional, Any

from app.services.dxcluster_parser import parse_spot, SpotData

logger = logging.getLogger("radiomanager.dxcluster")

# 内存中保留的最近 spot 数量
MAX_SPOTS = 100
# telnet 连接/读取超时（秒）
CONNECT_TIMEOUT = 15
READ_TIMEOUT = 600
# telnet 协议的 IAC（Interpret As Command）字节，需过滤
_IAC = 0xFF


@dataclass
class NodeInfo:
    """DX Cluster 节点信息。"""
    host: str
    port: int
    name: str
    country: str
    remark: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# 预设的公共 DX Cluster 节点列表
# 数据来源：常见业余无线电 DX Cluster 节点，端口为标准 telnet 端口。
# 用户可在此列表中选择切换。
PRESET_NODES: list[NodeInfo] = [
    NodeInfo("dxc.ve7cc.net", 7373, "VE7CC", "Canada", "北美西海岸，老牌节点"),
    NodeInfo("dxc.k1ttt.net", 7373, "K1TTT", "USA", "美国东海岸"),
    NodeInfo("dxc.w3lpl.net", 7373, "W3LPL", "USA", "美国东海岸，高可用"),
    NodeInfo("gb7dxf.sadxb.org", 7373, "GB7DXF", "UK", "英国，欧洲枢纽"),
    NodeInfo("oh2aq.df7hu.de", 8000, "OH2AQ", "Finland", "北欧"),
    NodeInfo("pi4rau.nl", 7300, "PI4RAU", "Netherlands", "荷兰"),
    NodeInfo("dxc.mhspet.ru", 7300, "RA3APW", "Russia", "东欧"),
    NodeInfo("dxc.jarl.com", 7373, "JA", "Japan", "日本，亚洲入口"),
]


def _strip_telnet_commands(data: bytes) -> str:
    """过滤 telnet 协议命令字节（IAC 序列），返回纯文本。

    telnet 协议在数据流中夹带以 IAC(0xFF) 开头的协商命令，
    这些不是 spot 内容，必须去掉，否则会干扰解析。
    """
    out = bytearray()
    i = 0
    n = len(data)
    while i < n:
        b = data[i]
        if b == _IAC:
            # IAC 后跟命令字节；部分命令还有子协商参数
            if i + 1 < n:
                cmd = data[i + 1]
                if cmd == 0xFF:  # IAC IAC = 转义的 0xFF 数据字节
                    out.append(0xFF)
                    i += 2
                    continue
                if cmd == 250:  # SB（子协商开始），需找到 SE(240) 结束
                    j = i + 2
                    while j < n - 1 and not (data[j] == _IAC and data[j + 1] == 240):
                        j += 1
                    i = j + 2
                    continue
                # 二字节命令（WILL/WONT/DO/DONT 等）带一个参数字节
                if cmd in (251, 252, 253, 254):
                    i += 3
                    continue
                # 其他单字节命令
                i += 2
                continue
            i += 1
            continue
        out.append(b)
        i += 1
    return out.decode("utf-8", errors="replace")


class DXClusterManager:
    """DX Cluster 连接与 spot 分发的全局单例管理器。"""

    def __init__(self) -> None:
        self._reader: Optional[asyncio.StreamReader] = None
        self._writer: Optional[asyncio.StreamWriter] = None
        self._listen_task: Optional[asyncio.Task] = None

        self._spots: deque[SpotData] = deque(maxlen=MAX_SPOTS)
        self._subscribers: set[asyncio.Queue] = set()

        self._connected: bool = False
        self._connecting: bool = False
        self._current_node: Optional[NodeInfo] = None
        self._callsign: Optional[str] = None
        self._connected_at: Optional[float] = None
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # 状态查询
    # ------------------------------------------------------------------
    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def connecting(self) -> bool:
        return self._connecting

    def status(self) -> dict[str, Any]:
        """返回当前连接状态摘要。"""
        uptime = None
        if self._connected and self._connected_at:
            uptime = round(asyncio.get_event_loop().time() - self._connected_at, 1)
        return {
            "connected": self._connected,
            "connecting": self._connecting,
            "current_node": self._current_node.to_dict() if self._current_node else None,
            "callsign": self._callsign,
            "spot_count": len(self._spots),
            "uptime_seconds": uptime,
        }

    def get_history(self, limit: int = 50) -> list[dict]:
        """返回最近 N 条 spot（新→旧）。"""
        items = list(self._spots)
        items.reverse()
        print(f"Returning {min(limit, len(items))} spots from history (total stored: {len(items)})")
        return [s.to_dict() for s in items[:limit]]

    @staticmethod
    def get_nodes() -> list[dict]:
        """返回预设节点列表。"""
        return [n.to_dict() for n in PRESET_NODES]

    # ------------------------------------------------------------------
    # 订阅 / 取消订阅（WebSocket 客户端用）
    # ------------------------------------------------------------------
    async def subscribe(self) -> asyncio.Queue:
        """订阅实时 spot。返回一个 Queue，新 spot 会 put 进去。"""
        q: asyncio.Queue = asyncio.Queue(maxsize=MAX_SPOTS)
        self._subscribers.add(q)
        return q

    async def unsubscribe(self, q: asyncio.Queue) -> None:
        """取消订阅。"""
        self._subscribers.discard(q)

    async def _broadcast(self, spot: SpotData) -> None:
        """将 spot 广播给所有订阅者。慢消费者会被丢弃最旧消息（非阻塞）。"""
        for q in list(self._subscribers):
            try:
                q.put_nowait(spot)
            except asyncio.QueueFull:
                # 订阅者消费太慢，丢最旧的一条腾位置
                try:
                    q.get_nowait()
                    q.put_nowait(spot)
                except Exception:
                    pass

    # ------------------------------------------------------------------
    # 连接管理
    # ------------------------------------------------------------------
    async def connect(self, node: NodeInfo, callsign: str) -> dict[str, Any]:
        """连接到指定节点并以 callsign 登录。

        Returns:
            状态字典（用于 API 直接返回）
        Raises:
            RuntimeError: 已在连接中 / 登录失败 / 连接超时
        """
        async with self._lock:
            if self._connecting:
                raise RuntimeError("Another connection attempt is in progress")
            if self._connected:
                await self._do_disconnect()

            self._connecting = True
            self._current_node = node
            self._callsign = callsign.upper()
            try:
                logger.info("Connecting to DX cluster %s:%d as %s", node.host, node.port, self._callsign)
                self._reader, self._writer = await asyncio.wait_for(
                    asyncio.open_connection(node.host, node.port),
                    timeout=CONNECT_TIMEOUT,
                )
                await self._do_login()
                self._connected = True
                self._connected_at = asyncio.get_event_loop().time()
                self._listen_task = asyncio.create_task(self._listen_loop())
                logger.info("Connected to %s as %s", node.name, self._callsign)
            except Exception as e:
                self._connected = False
                self._connecting = False
                await self._cleanup_socket()
                logger.error("Failed to connect to %s: %s", node.name, e)
                raise RuntimeError(f"Connection failed: {e}") from e
            finally:
                self._connecting = False

            return self.status()

    async def _do_login(self) -> None:
        """处理 cluster 登录握手：逐行读取，找到 login/callsign 提示后发送呼号。

        逐行读取而非 readuntil，避免跨行消费字节流导致后续 readline 行不对齐。
        超时或找不到提示也直接发呼号（多数节点兼容）。
        """
        assert self._reader is not None and self._writer is not None
        login_timeout = 15  # 等待 login 提示的超时（秒）
        try:
            deadline = asyncio.get_event_loop().time() + login_timeout
            line_count = 0
            while True:
                remaining = deadline - asyncio.get_event_loop().time()
                if remaining <= 0:
                    logger.info("Login prompt timeout after reading %d lines", line_count)
                    break
                raw = await asyncio.wait_for(self._reader.readline(), timeout=max(remaining, 0.1))
                if not raw:
                    logger.info("EOF while waiting for login prompt after %d lines", line_count)
                    break
                line = _strip_telnet_commands(raw).strip()
                line_count += 1
                if not line:
                    continue
                logger.debug("Login banner line %d: %s", line_count, line[:120])
                # 找到 login / callsign 提示即停止
                if line.lower().startswith(("login:", "callsign:", "enter call", "your call")):
                    logger.info("Login prompt found: %s", line[:80])
                    break
        except (asyncio.TimeoutError, asyncio.IncompleteReadError):
            pass
        except Exception as exc:
            logger.warning("Login handshake exception: %s", exc)

        # 发送呼号 + 换行完成登录
        logger.info("Sending callsign: %s", self._callsign)
        self._writer.write(f"{self._callsign}\n".encode("ascii", errors="replace"))
        await self._writer.drain()

    async def _listen_loop(self) -> None:
        """后台任务：持续读取 cluster 输出，解析 spot，存入内存并广播。

        连接断开时退出循环并清理状态（不自动重连）。
        """
        assert self._reader is not None
        logger.info("DX cluster listen loop started")
        line_num = 0
        spot_num = 0
        try:
            while self._connected:
                try:
                    raw = await asyncio.wait_for(self._reader.readline(), timeout=READ_TIMEOUT)
                except asyncio.TimeoutError:
                    # 长时间无数据，检查连接是否还活着
                    logger.warning("DX cluster read timeout after %d lines, %d spots", line_num, spot_num)
                    break
                if not raw:
                    # EOF，对端关闭
                    logger.warning("DX cluster connection closed by remote (EOF) after %d lines, %d spots", line_num, spot_num)
                    break

                try:
                    line = _strip_telnet_commands(raw).strip()
                    line_num += 1
                    if not line:
                        continue
                    if line_num <= 5:
                        logger.info("Listen line %d: %s", line_num, line[:120])

                    spot = parse_spot(line)
                    if spot:
                        spot_num += 1
                        if spot_num <= 3:
                            logger.info("Parsed spot #%d: %s by %s on %.1f (%s)",
                                        spot_num, spot.dx_callsign, spot.spotter, spot.freq, spot.band)
                        self._spots.append(spot)
                        await self._broadcast(spot)
                except Exception as e:
                    logger.debug("Failed to process line %d: %s", line_num, e)
                    continue
        except Exception as e:
            logger.error("DX cluster listen loop error: %s", e)
        finally:
            self._connected = False
            self._connected_at = None
            logger.info("DX cluster listen loop ended")
            # 通知订阅者连接已断（通过特殊消息）
            await self._notify_disconnect()

    async def _notify_disconnect(self) -> None:
        """通知所有订阅者连接已断开。"""
        for q in list(self._subscribers):
            try:
                q.put_nowait({"type": "disconnect"})
            except asyncio.QueueFull:
                pass

    async def _cleanup_socket(self) -> None:
        """关闭并清理 socket。"""
        if self._writer is not None:
            try:
                self._writer.close()
                await self._writer.wait_closed()
            except Exception:
                pass
        self._reader = None
        self._writer = None

    async def _do_disconnect(self) -> None:
        """内部断开（不加锁）。"""
        self._connected = False
        if self._listen_task and not self._listen_task.done():
            self._listen_task.cancel()
            try:
                await self._listen_task
            except (asyncio.CancelledError, Exception):
                pass
        self._listen_task = None
        await self._cleanup_socket()
        self._connected_at = None

    async def disconnect(self) -> dict[str, Any]:
        """断开当前连接。"""
        async with self._lock:
            await self._do_disconnect()
            self._current_node = None
            self._callsign = None
            return self.status()


# 模块级单例，全进程共享
dxcluster_manager = DXClusterManager()
