"""数据格式化工具"""

from datetime import datetime, date
from typing import Optional


class Formatters:
    """通用格式化工具"""

    @staticmethod
    def format_datetime(dt: Optional[datetime], fmt: str = "%Y-%m-%d %H:%M:%S") -> Optional[str]:
        """格式化日期时间"""
        if dt is None:
            return None
        return dt.strftime(fmt)

    @staticmethod
    def format_date(d: Optional[date], fmt: str = "%Y-%m-%d") -> Optional[str]:
        """格式化日期"""
        if d is None:
            return None
        return d.strftime(fmt)

    @staticmethod
    def format_frequency(freq_mhz: Optional[float]) -> Optional[str]:
        """格式化频率 (MHz -> kHz/MHz 展示)"""
        if freq_mhz is None:
            return None
        if freq_mhz < 30:
            return f"{freq_mhz:.4f} MHz"
        return f"{freq_mhz:.2f} MHz"

    @staticmethod
    def format_distance(km: Optional[int]) -> str:
        """格式化距离"""
        if km is None:
            return "N/A"
        if km < 1:
            return f"{int(km * 1000)} m"
        if km < 1000:
            return f"{km} km"
        return f"{km / 1000:.1f}K km"

    @staticmethod
    def callsign_display(callsign: str) -> str:
        """标准化呼号显示"""
        return callsign.upper().strip()

    @staticmethod
    def band_from_frequency(freq_mhz: float) -> Optional[str]:
        """从频率自动推断波段"""
        band_map = [
            (1.8, 2.0, "160m"),
            (3.5, 4.0, "80m"),
            (5.25, 5.45, "60m"),
            (7.0, 7.3, "40m"),
            (10.1, 10.15, "30m"),
            (14.0, 14.35, "20m"),
            (18.068, 18.168, "17m"),
            (21.0, 21.45, "15m"),
            (24.89, 24.99, "12m"),
            (28.0, 29.7, "10m"),
            (50.0, 54.0, "6m"),
            (144.0, 148.0, "2m"),
            (420.0, 450.0, "70cm"),
        ]
        for lo, hi, band in band_map:
            if lo <= freq_mhz <= hi:
                return band
        return None
