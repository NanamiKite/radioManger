"""QRZ.com API客户端"""

import logging
from typing import Optional, Dict
from datetime import date
import xml.etree.ElementTree as ET

import httpx

from app.config import settings

logger = logging.getLogger("radiomanager.qrz")


class QRZClient:
    """QRZ.com XML API 客户端"""

    SESSION_URL = "https://xmldata.qrz.com/xml/current/"
    CALLSIGN_URL = "https://xmldata.qrz.com/xml/current/"

    def __init__(self):
        self.session_key: Optional[str] = None
        self._client = httpx.Client(timeout=15.0)

    def _ensure_session(self) -> str:
        """获取或刷新QRZ会话"""
        if self.session_key:
            return self.session_key

        if not settings.QRZ_USERNAME or not settings.QRZ_PASSWORD:
            raise ConnectionError("QRZ API credentials not configured")

        response = self._client.get(
            self.SESSION_URL,
            params={
                "username": settings.QRZ_USERNAME,
                "password": settings.QRZ_PASSWORD,
                "agent": "radiomanager.1.0",
            },
        )
        root = ET.fromstring(response.text)

        err = root.find(".//Error")
        if err is not None:
            raise ConnectionError(f"QRZ login failed: {err.text}")

        key = root.find(".//Key")
        if key is None:
            raise ConnectionError("QRZ login failed: no session key returned")

        self.session_key = key.text
        return self.session_key

    def lookup(self, callsign: str) -> Optional[Dict]:
        """查询单个呼号"""
        try:
            session = self._ensure_session()
            response = self._client.get(
                self.CALLSIGN_URL,
                params={"s": session, "callsign": callsign},
            )
            return self._parse_callsign_response(response.text, callsign)
        except Exception as e:
            logger.warning(f"QRZ lookup failed for {callsign}: {e}")
            return None

    def _parse_callsign_response(self, xml_text: str, callsign: str) -> Optional[Dict]:
        """解析QRZ XML响应"""
        root = ET.fromstring(xml_text)
        err = root.find(".//Error")
        if err is not None:
            logger.debug(f"QRZ error for {callsign}: {err.text}")
            return None

        callsign_elem = root.find(".//Callsign")
        if callsign_elem is None:
            return None

        result = {
            "call_sign": callsign.upper(),
            "first_name": self._elem_text(callsign_elem, "fname"),
            "last_name": self._elem_text(callsign_elem, "name"),
            "full_name": None,
            "country": self._elem_text(callsign_elem, "country"),
            "grid_square": self._elem_text(callsign_elem, "grid"),
            "latitude": self._elem_float(callsign_elem, "lat"),
            "longitude": self._elem_float(callsign_elem, "lon"),
            "class_type": self._elem_text(callsign_elem, "class"),
            "license_date": self._parse_date(self._elem_text(callsign_elem, "licdate")),
            "license_exp": self._parse_date(self._elem_text(callsign_elem, "effdate")),
            "previous_call": self._elem_text(callsign_elem, "prev_call"),
            "qrz_url": f"https://www.qrz.com/db/{callsign.upper()}",
        }

        # 组装全名
        first = result["first_name"] or ""
        last = result["last_name"] or ""
        result["full_name"] = f"{first} {last}".strip() or None

        return result

    @staticmethod
    def _elem_text(element, tag: str) -> Optional[str]:
        """获取子元素文本"""
        sub = element.find(tag)
        return sub.text if sub is not None and sub.text else None

    @staticmethod
    def _elem_float(element, tag: str) -> Optional[float]:
        """获取子元素浮点值"""
        text = QRZClient._elem_text(element, tag)
        if text:
            try:
                return float(text)
            except ValueError:
                return None
        return None

    @staticmethod
    def _parse_date(text: Optional[str]) -> Optional[date]:
        """解析QRZ日期格式 (YYYYMMDD)"""
        if not text or len(text) != 8:
            return None
        try:
            return date(
                year=int(text[0:4]),
                month=int(text[4:6]),
                day=int(text[6:8]),
            )
        except ValueError:
            return None

    def close(self):
        """关闭HTTP客户端"""
        self._client.close()
