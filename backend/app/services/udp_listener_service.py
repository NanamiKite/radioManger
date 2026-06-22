"""
UDP 监听服务 - 接收 WSJT-X/JTDX/MSHV/N1MM 的 QSO 日志广播
通过 WebSocket 实时推送给前端

协议:
- WSJT-X/JTDX/MSHV: QDataStream header + JSON (默认端口 2237)
- N1MM Logger+: XML over UDP (默认端口 12060)
"""

import asyncio
import json
import logging
import struct
from datetime import datetime, timezone, date, time
from decimal import Decimal
from typing import Optional, Set
from xml.etree import ElementTree

from app.config import settings

logger = logging.getLogger("radiomanager.udp")


class UDPListenerService:
    """UDP 监听服务（单例）"""

    _instance: Optional["UDPListenerService"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._running = False
        self._wsjtx_task: Optional[asyncio.Task] = None
        self._n1mm_task: Optional[asyncio.Task] = None
        self._wsjtx_port = settings.UDP_WSJTX_PORT
        self._n1mm_port = settings.UDP_N1MM_PORT
        self._qso_count = 0
        self._ws_clients: Set = set()  # WebSocket 连接集合
        self._last_qso = None

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def status(self) -> dict:
        return {
            "running": self._running,
            "wsjtx_port": self._wsjtx_port,
            "n1mm_port": self._n1mm_port,
            "qso_count": self._qso_count,
            "last_qso": self._last_qso,
            "ws_clients": len(self._ws_clients),
        }

    async def start(self, wsjtx_port: Optional[int] = None, n1mm_port: Optional[int] = None):
        if self._running:
            return
        self._wsjtx_port = wsjtx_port or settings.UDP_WSJTX_PORT
        self._n1mm_port = n1mm_port or settings.UDP_N1MM_PORT
        self._running = True
        self._qso_count = 0

        # 短暂延迟确保旧 socket 释放（TIME_WAIT）
        await asyncio.sleep(0.2)

        self._wsjtx_task = asyncio.create_task(self._listen_wsjtx())
        self._n1mm_task = asyncio.create_task(self._listen_n1mm())
        logger.info(f"UDP listener started: WSJT-X={self._wsjtx_port}, N1MM={self._n1mm_port}")

    async def stop(self):
        self._running = False
        if self._wsjtx_task:
            self._wsjtx_task.cancel()
            self._wsjtx_task = None
        if self._n1mm_task:
            self._n1mm_task.cancel()
            self._n1mm_task = None
        logger.info("UDP listener stopped")

    def register_ws(self, ws):
        self._ws_clients.add(ws)

    def unregister_ws(self, ws):
        self._ws_clients.discard(ws)

    async def _broadcast(self, data: dict):
        """广播 QSO 数据到所有 WebSocket 客户端"""
        dead = set()
        for ws in self._ws_clients:
            try:
                await ws.send_json(data)
            except Exception:
                dead.add(ws)
        self._ws_clients -= dead

    # ── WSJT-X / JTDX / MSHV 监听 ──
    async def _listen_wsjtx(self):
        try:
            loop = asyncio.get_event_loop()
            transport, protocol = await loop.create_datagram_endpoint(
                lambda: WSJTXProtocol(self._on_wsjtx_qso),
                local_addr=("0.0.0.0", self._wsjtx_port),
            )
            logger.info(f"WSJT-X UDP listening on :{self._wsjtx_port}")
            while self._running:
                await asyncio.sleep(1)
            transport.close()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"WSJT-X listener error: {e}")
            self._running = False

    def _on_wsjtx_qso(self, data: dict):
        """WSJT-X QSO Logged 回调"""
        asyncio.get_event_loop().create_task(self._process_qso("wsjtx", data))

    # ── N1MM 监听 ──
    async def _listen_n1mm(self):
        try:
            loop = asyncio.get_event_loop()
            transport, protocol = await loop.create_datagram_endpoint(
                lambda: N1MMProtocol(self._on_n1mm_qso),
                local_addr=("0.0.0.0", self._n1mm_port),
            )
            logger.info(f"N1MM UDP listening on :{self._n1mm_port}")
            while self._running:
                await asyncio.sleep(1)
            transport.close()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"N1MM listener error: {e}")
            self._running = False

    def _on_n1mm_qso(self, data: dict):
        """N1MM contactinfo 回调"""
        asyncio.get_event_loop().create_task(self._process_qso("n1mm", data))

    # ── 统一处理 ──
    async def _process_qso(self, source: str, data: dict):
        """解析 QSO 数据并通过 WebSocket 广播"""
        try:
            qso = self._map_fields(source, data)
            self._qso_count += 1
            self._last_qso = {
                "source": source,
                "call_sign": qso.get("call_sign"),
                "band": qso.get("band"),
                "mode": qso.get("mode"),
                "time": datetime.now(timezone.utc).isoformat(),
            }
            # 广播给前端
            await self._broadcast({
                "type": "qso_received",
                "source": source,
                "data": qso,
                "count": self._qso_count,
            })
            logger.info(f"[{source.upper()}] QSO received: {qso.get('call_sign')} {qso.get('band')} {qso.get('mode')}")
        except Exception as e:
            logger.error(f"Process QSO error: {e}")

    def _map_fields(self, source: str, data: dict) -> dict:
        """将不同来源的字段映射为统一的 QSO 日志格式"""
        if source == "wsjtx":
            return self._map_wsjtx(data)
        elif source == "n1mm":
            return self._map_n1mm(data)
        return data

    def _map_wsjtx(self, d: dict) -> dict:
        """WSJT-X QSO Logged 字段映射"""
        # 频率: Hz → MHz
        freq_mhz = None
        txfreq = d.get("txFrequency")
        if txfreq:
            freq_mhz = round(int(txfreq) / 1_000_000, 6)

        # 时间: QDateTime ms → date + time
        qso_date = None
        time_on = None
        time_on_ms = d.get("timeOn")
        if time_on_ms:
            dt = datetime.fromtimestamp(int(time_on_ms) / 1000, tz=timezone.utc)
            qso_date = dt.date().isoformat()
            time_on = dt.time().isoformat()

        # 功率: "100W" → 100
        tx_pwr = None
        raw_pwr = d.get("txPower", "")
        if raw_pwr:
            digits = "".join(c for c in str(raw_pwr) if c.isdigit())
            if digits:
                tx_pwr = int(digits)

        return {
            "call_sign": (d.get("dxCall") or "").upper(),
            "qso_date": qso_date,
            "time_on": time_on,
            "freq": freq_mhz,
            "mode": d.get("mode"),
            "rst_sent": d.get("reportSent"),
            "rst_rcvd": d.get("reportReceived"),
            "grid_square": (d.get("dxGrid") or "").upper() or None,
            "my_gridsquare": (d.get("myGrid") or "").upper() or None,
            "tx_pwr": tx_pwr,
            "comment": d.get("comments"),
            "operator": d.get("operatorCall"),
        }

    def _map_n1mm(self, d: dict) -> dict:
        """N1MM contactinfo 字段映射"""
        # 频率: 10Hz 单位 → MHz
        freq_mhz = None
        rxfreq = d.get("rxfreq")
        if rxfreq:
            freq_mhz = round(int(rxfreq) / 100_000, 6)

        # 时间
        qso_date = None
        time_on = None
        ts = d.get("timestamp")
        if ts:
            try:
                dt = datetime.strptime(str(ts), "%Y-%m-%d %H:%M:%S")
                qso_date = dt.date().isoformat()
                time_on = dt.time().isoformat()
            except ValueError:
                pass

        # 功率
        tx_pwr = None
        raw_pwr = d.get("power", "")
        if raw_pwr:
            digits = "".join(c for c in str(raw_pwr) if c.isdigit())
            if digits:
                tx_pwr = int(digits)

        return {
            "call_sign": (d.get("call") or "").upper(),
            "qso_date": qso_date,
            "time_on": time_on,
            "freq": freq_mhz,
            "mode": d.get("mode"),
            "rst_sent": d.get("snt"),
            "rst_rcvd": d.get("rcv"),
            "grid_square": (d.get("gridsquare") or "").upper() or None,
            "tx_pwr": tx_pwr,
            "comment": d.get("comment"),
            "operator": d.get("name"),
        }


# ── 协议处理器 ──

class WSJTXProtocol(asyncio.DatagramProtocol):
    """WSJT-X QDataStream 协议解析"""

    # QDataStream header: magic 0xADBCCBDA + schema + type
    MAGIC = 0xADBCCBDA
    QSO_LOGGED = 3

    def __init__(self, on_qso):
        self.on_qso = on_qso

    def connection_made(self, transport):
        pass

    def datagram_received(self, data: bytes, addr):
        try:
            if len(data) < 16:
                return
            # 解析 QDataStream 头
            magic = struct.unpack(">I", data[0:4])[0]
            if magic != self.MAGIC:
                return
            msg_type = struct.unpack(">I", data[8:12])[0]
            if msg_type != self.QSO_LOGGED:
                return
            # JSON payload 从第 12 字节开始
            json_bytes = data[12:]
            # QDataStream 字符串: 4字节长度 + UTF-8
            if len(json_bytes) < 4:
                return
            str_len = struct.unpack(">I", json_bytes[0:4])[0]
            json_str = json_bytes[4:4 + str_len].decode("utf-8")
            payload = json.loads(json_str)
            self.on_qso(payload)
        except Exception as e:
            logger.debug(f"WSJT-X parse error: {e}")


class N1MMProtocol(asyncio.DatagramProtocol):
    """N1MM XML 协议解析"""

    def __init__(self, on_qso):
        self.on_qso = on_qso

    def connection_made(self, transport):
        pass

    def datagram_received(self, data: bytes, addr):
        try:
            xml_str = data.decode("utf-8", errors="ignore")
            if "<contactinfo>" not in xml_str:
                return
            root = ElementTree.fromstring(xml_str)
            if root.tag != "contactinfo":
                return
            fields = {}
            for child in root:
                fields[child.tag.lower()] = child.text or ""
            self.on_qso(fields)
        except Exception as e:
            logger.debug(f"N1MM parse error: {e}")


# 全局单例
udp_listener = UDPListenerService()
