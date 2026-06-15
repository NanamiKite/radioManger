"""QRZ.com XML API 客户端"""

import logging
from typing import Optional, Dict
from datetime import date
import requests

from app.config import settings

logger = logging.getLogger("radiomanager.qrz")

BASE_URL = "https://xmldata.qrz.com/xml/current/"


def _extract_tag(xml: str, tag: str) -> Optional[str]:
    """从XML字符串中提取标签内容（无视命名空间）"""
    import re
    m = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", xml, re.DOTALL)
    return m.group(1).strip() if m else None


class QRZClient:
    """QRZ.com XML API 客户端"""

    def __init__(self):
        self.session_key: Optional[str] = None

    def _ensure_session(self) -> str:
        if self.session_key:
            return self.session_key

        if not settings.QRZ_USERNAME or not settings.QRZ_PASSWORD:
            raise ConnectionError("QRZ API credentials not configured")

        r = requests.get(
            BASE_URL,
            params={
                "username": settings.QRZ_USERNAME,
                "password": settings.QRZ_PASSWORD,
                "agent": "radiomanager.1.0",
            },
            timeout=15,
        )

        key = _extract_tag(r.text, "Key")
        err = _extract_tag(r.text, "Error")

        if err:
            raise ConnectionError(f"QRZ login failed: {err}")

        if not key:
            raise ConnectionError("QRZ login failed: no session key returned")

        self.session_key = key
        return key

    def lookup(self, callsign: str) -> Optional[Dict]:
        try:
            session = self._ensure_session()
            r = requests.get(
                BASE_URL,
                params={"s": session, "callsign": callsign},
                timeout=15,
            )
            return self._parse_response(r.text, callsign)
        except Exception as e:
            logger.warning(f"QRZ lookup failed for {callsign}: {e}")
            return None

    def _parse_response(self, xml_text: str, callsign: str) -> Optional[Dict]:
        err = _extract_tag(xml_text, "Error")
        if err:
            logger.debug(f"QRZ error for {callsign}: {err}")
            return None

        # 直接用字符串提取
        obj = xml_text.split("<Callsign>")
        if len(obj) < 2:
            return None
        block = obj[1].split("</Callsign>")[0]

        def t(tag: str) -> Optional[str]:
            return _extract_tag(block, tag)

        def tf(tag: str) -> Optional[float]:
            v = t(tag)
            if v:
                try:
                    return float(v)
                except ValueError:
                    return None
            return None

        def td(tag: str) -> Optional[date]:
            v = t(tag)
            if not v or len(v) != 10:
                return None
            try:
                return date(int(v[0:4]), int(v[5:7]), int(v[8:10]))
            except ValueError:
                return None

        first = t("fname") or ""
        last = t("name") or ""
        full_name = f"{first} {last}".strip() or None

        addr1 = t("addr1")
        addr2 = t("addr2")
        state = t("state")
        zip_code = t("zip")
        full_addr_parts = [p for p in [addr1, addr2, state, zip_code] if p]
        address = ", ".join(full_addr_parts) if full_addr_parts else None

        return {
            "call_sign": callsign.upper(),
            "first_name": first or None,
            "last_name": last or None,
            "full_name": full_name,
            "country": t("country"),
            "grid_square": t("grid"),
            "latitude": tf("lat"),
            "longitude": tf("lon"),
            "class_type": t("class"),
            "license_date": td("efdate") or td("licdate"),
            "license_exp": td("expdate") or td("effdate"),
            "previous_call": t("aliases"),
            "qrz_url": f"https://www.qrz.com/db/{callsign.upper()}",
            "url": t("url"),
            "phone": t("phone"),
            "address": address,
            "zip_code": zip_code,
            "cq_zone": t("cqzone"),
            "itu_zone": t("ituzone"),
            "email": t("email"),
            "image": t("image"),
        }

    def close(self):
        pass
