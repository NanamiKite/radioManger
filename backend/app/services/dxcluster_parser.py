"""
DX Cluster Spot 解析器
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional
from decimal import Decimal
from app.utils.dxcc import DXCC_PREFIXES


@dataclass
class SpotData:
    """解析后pot结构"""
    spotter: str
    freq: str                 # 原始频率字符串（UI展示）
    freq_mhz: Decimal        # 归一化后的 MHz（计算波段使用）
    dx_callsign: str
    mode: str
    comment: str
    time_utc: Optional[str]
    band: str
    received_at: str
    dxcc_entity: str

    def to_dict(self) -> dict:
        """给 API / JSON 输出用（保证兼容前端）"""
        data = asdict(self)
        # 保持前端字段不变
        data["freq"] = self.freq
        # 提供计算值（字符串避免 JSON float 问题）
        data["freq_mhz"] = str(self.freq_mhz)
        return data


# Spot 正则（兼容整数/小数）
_SPOT_RE = re.compile(
    r"^DX\s+de\s+"
    r"(?P<spotter>[A-Z0-9/]+):\s*"
    r"(?P<freq>\d+(?:\.\d+)?)\s+"   # 修复：14074 / 14.074 / 14.074123
    r"(?P<dx>[A-Z0-9/]+)\s+"
    r"(?P<comment>.*?)"
    r"(?:\s+(?P<time>\d{4}Z))?\s*$",
    re.IGNORECASE,
)


# 波段表（MHz）
_BAND_RANGES = [
    (0.1357, 0.1378, "2200m"),
    (0.472, 0.479, "630m"),
    (1.800, 2.000, "160m"),
    (3.500, 4.000, "80m"),
    (5.060, 5.450, "60m"),
    (7.000, 7.300, "40m"),
    (10.100, 10.150, "30m"),
    (14.000, 14.350, "20m"),
    (18.068, 18.168, "17m"),
    (21.000, 21.450, "15m"),
    (24.890, 24.990, "12m"),
    (28.000, 29.700, "10m"),
    (50.000, 54.000, "6m"),
    (70.000, 70.500, "4m"),
    (144.000, 148.000, "2m"),
    (430.000, 440.000, "70cm"),
    (1240.000, 1300.000, "23cm"),
    (2300.000, 2450.000, "13cm"),
    (5760.000, 5850.000, "5cm"),
    (10_000.000, 10_500.000, "3cm"),
    (24_000.000, 24_250.000, "1.2cm"),
    (47_000.000, 47_200.000, "6mm"),
    (76_000.000, 81_000.000, "4mm"),
    (122_250.000, 123_000.000, "2.5mm"),
    (134_000.000, 141_000.000, "2mm"),
    (241_000.000, 250_000.000, "1mm"),
]


def _match_band_raw(freq_mhz: Decimal) -> Optional[str]:
    """波段匹配（Decimal安全）"""
    for low, high, name in _BAND_RANGES:
        low_d = Decimal(str(low))
        high_d = Decimal(str(high))
        if low_d <= freq_mhz <= high_d:
            return name
    return None


def normalize_freq(freq: Decimal) -> Decimal:
    """
    统一频率到 MHz（兼容 kHz / MHz 混乱）
    """
    # ✔ 明显 kHz
    if freq > Decimal("1500"):
        return freq / Decimal("1000")

    # ✔ 双重校验（避免 14074 被当 MHz）
    if (
        _match_band_raw(freq) is None
        and _match_band_raw(freq / Decimal("1000")) is not None
    ):
        return freq / Decimal("1000")

    return freq


def freq_to_band(freq_mhz: Decimal) -> str:
    return _match_band_raw(freq_mhz) or "Other"


# band识别
_KNOWN_MODES = {
    "FT8", "FT4", "JT65", "JT9", "MSK144", "JS8",
    "CW", "SSB", "USB", "LSB", "FM", "AM",
    "RTTY", "PSK31", "PSK63", "MFSK",
    "OLIVIA", "CONTESTIA", "SSTV", "ATV",
    "PACTOR", "PACKET", "HELL",
}

def match_dxcc_entity(dx_callsign: str) -> str:
    """根据呼号前缀从高精度到低精度查找 DXCC 实体名称"""
    if not dx_callsign:
        return "Unknown"
    
    clean_call = dx_callsign.strip().upper()
    for pattern, entity in DXCC_PREFIXES:
        if re.match(pattern, clean_call):
            return entity
            
    return "Unknown"

def _extract_mode(comment: str) -> str:
    upper = comment.upper()
    words = re.findall(r"[A-Z0-9]+", upper)
    for w in words:
        if w in _KNOWN_MODES:
            return w
    return ""


def is_spot_line(line: str) -> bool:
    return bool(
        line.strip().upper().startswith("DX DE ")
        and _SPOT_RE.match(line.strip())
    )


# 主解析函数
def parse_spot(line: str) -> Optional[SpotData]:
    if not line:
        return None

    cleaned = line.strip()
    match = _SPOT_RE.match(cleaned)
    if not match:
        return None

    spotter = match.group("spotter").upper()
    freq_str = match.group("freq")   # 保留原始字符串（UI用）
    freq_raw = Decimal(freq_str)     # 精确计算
    freq_mhz = normalize_freq(freq_raw)

    dx_callsign = match.group("dx").upper()
    dxcc_entity = match_dxcc_entity(dx_callsign)
    comment = match.group("comment").strip()
    time_utc = match.group("time")

    mode = _extract_mode(comment)
    band = freq_to_band(freq_mhz)

    received_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return SpotData(
        spotter=spotter,
        freq=freq_str,        # 前端展示
        freq_mhz=freq_mhz,    # 内部计算
        dx_callsign=dx_callsign,
        mode=mode,
        comment=comment,
        time_utc=time_utc,
        band=band,
        received_at=received_at,
        dxcc_entity=dxcc_entity,
    )


# 批量解析
def parse_cluster_output(text: str) -> list[SpotData]:
    spots = []
    for line in text.splitlines():
        spot = parse_spot(line)
        if spot:
            spots.append(spot)
    return spots