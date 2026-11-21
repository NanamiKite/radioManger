"""One host-level UDP listener; QSO messages belong to its initiating user."""

import asyncio
import logging
import struct
from contextlib import AsyncExitStack
from datetime import datetime, timezone, timedelta
from typing import Optional
from xml.etree import ElementTree

from app.config import settings
from app.exceptions import PermissionException
from app.services.dxcluster_parser import freq_to_band
from decimal import Decimal

logger = logging.getLogger("radiomanager.udp")


class UDPListenerService:
    def __init__(self):
        self._owner_id: Optional[int] = None
        self._transports = []
        self._closed = []
        self._lock = asyncio.Lock()
        self._wsjtx_port = settings.UDP_WSJTX_PORT
        self._n1mm_port = settings.UDP_N1MM_PORT
        self._qso_count = 0
        self._last_qso = None
        self._subscribers: dict[asyncio.Queue, int] = {}

    @property
    def is_running(self) -> bool:
        return bool(self._transports)

    def status_for(self, user_id: int) -> dict:
        receiving = self.is_running and user_id == self._owner_id
        return {
            "running": self.is_running,
            "receiving": receiving,
            "wsjtx_port": self._wsjtx_port,
            "n1mm_port": self._n1mm_port,
            "qso_count": self._qso_count if receiving else 0,
            "last_qso": self._last_qso if receiving else None,
            "ws_clients": sum(owner == user_id for owner in self._subscribers.values()),
        }

    async def start(self, user_id: int, wsjtx_port: Optional[int] = None, n1mm_port: Optional[int] = None):
        ports = (wsjtx_port if wsjtx_port is not None else settings.UDP_WSJTX_PORT,
                 n1mm_port if n1mm_port is not None else settings.UDP_N1MM_PORT)
        if any(not 1024 <= port <= 65535 for port in ports) or ports[0] == ports[1]:
            raise ValueError("UDP ports must be distinct and between 1024 and 65535")
        async with self._lock:
            if self.is_running and self._owner_id != user_id:
                raise PermissionException("UDP listener belongs to another user")
            if self.is_running and ports == (self._wsjtx_port, self._n1mm_port):
                return
            await self._stop()
            loop = asyncio.get_running_loop()
            async def close_transport(transport, done):
                transport.close()
                await done
            transports, closed = [], []
            # Close the first socket too if binding the second socket fails.
            async with AsyncExitStack() as cleanup:
                for protocol_type, source, port in ((WSJTXProtocol, "wsjtx", ports[0]), (N1MMProtocol, "n1mm", ports[1])):
                    done = loop.create_future()
                    transport, _ = await loop.create_datagram_endpoint(
                        lambda protocol_type=protocol_type, source=source, done=done: protocol_type(
                            lambda data: self._process_qso(source, data), done),
                        local_addr=(settings.UDP_BIND_HOST, port),
                    )
                    cleanup.push_async_callback(close_transport, transport, done)
                    transports.append(transport)
                    closed.append(done)
                self._transports, self._closed = transports, closed
                self._wsjtx_port, self._n1mm_port = ports
                self._owner_id = user_id
                self._qso_count, self._last_qso = 0, None
                cleanup.pop_all()
            logger.info("UDP listening on %s:%s/%s", settings.UDP_BIND_HOST, *ports)

    async def _stop(self):
        transports, closed = self._transports, self._closed
        self._transports, self._closed = [], []
        for transport in transports:
            transport.close()
        if closed:
            await asyncio.gather(*closed)
        self._owner_id = None
        self._last_qso, self._qso_count = None, 0

    async def stop(self, user_id: Optional[int] = None):
        async with self._lock:
            if user_id is not None and self.is_running and user_id != self._owner_id:
                raise PermissionException("UDP listener belongs to another user")
            await self._stop()

    def subscribe(self, user_id: int) -> asyncio.Queue:
        queue = asyncio.Queue(maxsize=100)
        self._subscribers[queue] = user_id
        return queue

    def unsubscribe(self, queue: asyncio.Queue):
        self._subscribers.pop(queue, None)

    def _process_qso(self, source: str, data: dict):
        if not self.is_running:
            return
        try:
            qso = self._map_fields(source, data)
        except (ValueError, TypeError, OverflowError) as exc:
            logger.debug("Invalid UDP QSO: %s", exc)
            return
        if not qso.get("call_sign"):
            return
        from app.schemas.qso_log import QSOLogCreate
        try:
            qso = QSOLogCreate.model_validate(qso).model_dump(mode="json", exclude_none=True)
        except ValueError as exc:
            logger.debug("Invalid UDP fields: %s", exc)
            return
        self._qso_count += 1
        self._last_qso = {
            "source": source, "call_sign": qso["call_sign"], "band": qso.get("band"),
            "mode": qso.get("mode"), "time": datetime.now(timezone.utc).isoformat(),
        }
        message = {"type": "qso_received", "source": source, "data": qso, "count": self._qso_count}
        for queue, owner in self._subscribers.items():
            if owner != self._owner_id:
                continue
            if queue.full():
                queue.get_nowait()
            queue.put_nowait(message)

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
            "band": freq_to_band(Decimal(str(freq_mhz))) if freq_mhz else None,
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
            dt = datetime.strptime(str(ts), "%Y-%m-%d %H:%M:%S")
            qso_date = dt.date().isoformat()
            time_on = dt.time().isoformat()

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
            "band": freq_to_band(Decimal(str(freq_mhz))) if freq_mhz else None,
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
    """WSJT-X QSO Logged type 5, QDataStream schema 2/3 (big endian)."""

    MAGIC = 0xADBCCBDA
    QSO_LOGGED = 5

    def __init__(self, on_qso, closed=None):
        self.on_qso = on_qso
        self.closed = closed

    def connection_lost(self, exc):
        if self.closed is not None and not self.closed.done():
            self.closed.set_result(None)

    @staticmethod
    def _utf8(data: bytes, offset: int):
        length = struct.unpack_from(">I", data, offset)[0]
        offset += 4
        if length == 0xFFFFFFFF:
            return "", offset
        end = offset + length
        if end > len(data):
            raise ValueError("Truncated QDataStream string")
        return data[offset:end].decode("utf-8"), end

    @staticmethod
    def _datetime(data: bytes, offset: int):
        julian, milliseconds, spec = struct.unpack_from(">qIB", data, offset)
        offset += 13
        if spec not in (1, 2) or milliseconds >= 86400000:
            raise ValueError("Expected UTC or fixed-offset QDateTime")
        instant = datetime.fromordinal(julian - 1721425).replace(tzinfo=timezone.utc) + timedelta(milliseconds=milliseconds)
        if spec == 2:
            seconds = struct.unpack_from(">i", data, offset)[0]
            offset += 4
            instant -= timedelta(seconds=seconds)
        return int(instant.timestamp() * 1000), offset

    def datagram_received(self, data: bytes, addr):
        if addr[0] not in settings.UDP_ALLOWED_SOURCES or len(data) > 16384:
            return
        try:
            magic, schema, kind = struct.unpack_from(">III", data)
            if magic != self.MAGIC or schema not in (2, 3) or kind != self.QSO_LOGGED:
                return
            _, offset = self._utf8(data, 12)
            end, offset = self._datetime(data, offset)
            payload = {"timeOff": end}
            for name in ("dxCall", "dxGrid"):
                payload[name], offset = self._utf8(data, offset)
            payload["txFrequency"] = struct.unpack_from(">Q", data, offset)[0]
            offset += 8
            for name in ("mode", "reportSent", "reportReceived", "txPower", "comments", "name"):
                payload[name], offset = self._utf8(data, offset)
            payload["timeOn"], offset = self._datetime(data, offset)
            for name in ("operatorCall", "myCall", "myGrid"):
                payload[name], offset = self._utf8(data, offset)
            self.on_qso(payload)
        except (ValueError, UnicodeDecodeError, struct.error, OverflowError) as exc:
            logger.debug("WSJT-X parse error: %s", exc)


class N1MMProtocol(asyncio.DatagramProtocol):
    """N1MM XML 协议解析"""

    def __init__(self, on_qso, closed=None):
        self.on_qso = on_qso
        self.closed = closed

    def connection_lost(self, exc):
        if self.closed is not None and not self.closed.done():
            self.closed.set_result(None)

    def datagram_received(self, data: bytes, addr):
        if addr[0] not in settings.UDP_ALLOWED_SOURCES or len(data) > 16384:
            return
        try:
            xml_str = data.decode("utf-8")
            if "<!" in xml_str:
                return
            if "<contactinfo>" not in xml_str:
                return
            root = ElementTree.fromstring(xml_str)
            if root.tag != "contactinfo":
                return
            fields = {}
            for child in root:
                fields[child.tag.lower()] = child.text or ""
            self.on_qso(fields)
        except (ElementTree.ParseError, UnicodeDecodeError) as exc:
            logger.debug("N1MM parse error: %s", exc)


# 全局单例
udp_listener = UDPListenerService()
