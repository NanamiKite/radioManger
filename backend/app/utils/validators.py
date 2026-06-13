import re
from decimal import Decimal

class RadioValidators:
    """业余无线电验证工具"""
    
    @staticmethod
    def validate_callsign(callsign: str) -> bool:
        """验证呼号格式"""
        # 支持格式: B7/BG6VBM, JA1ABC, 4I1EBD, E2A等
        pattern = r'^[A-Z0-9]{1,3}/[A-Z0-9]{3,10}$|^[A-Z0-9]{2,6}$|^[A-Z0-9]{1,3}/[A-Z0-9]{1,3}/[A-Z0-9]{1,6}$'
        return bool(re.match(pattern, callsign.upper()))
    
    @staticmethod
    def validate_grid_square(grid: str) -> bool:
        """验证梅登网格"""
        # 4位格式: OL63, PL09
        # 6位格式: OL63fc, PL09ae
        pattern = r'^[A-R]{2}[0-9]{2}([a-x]{2})?$'
        return bool(re.match(pattern, grid.lower()))
    
    @staticmethod
    def validate_frequency(freq: float, band: str) -> bool:
        """验证频率和波段是否匹配"""
        band_ranges = {
            "160m": (1.8, 2.0),
            "80m": (3.5, 4.0),
            "60m": (5.25, 5.45),
            "40m": (7.0, 7.3),
            "30m": (10.1, 10.15),
            "20m": (14.0, 14.35),
            "17m": (18.068, 18.168),
            "15m": (21.0, 21.45),
            "12m": (24.89, 24.99),
            "10m": (28.0, 29.7),
            "6m": (50.0, 54.0),
            "2m": (144.0, 148.0),
            "70cm": (420.0, 450.0),
        }
        
        if band not in band_ranges:
            return False
        
        min_freq, max_freq = band_ranges[band]
        return min_freq <= freq <= max_freq
    
    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
        """计算两点间距离(公里)"""
        import math
        
        R = 6371  # 地球半径(公里)
        
        lat1_rad = math.radians(lat1)
        lon1_rad = math.radians(lon1)
        lat2_rad = math.radians(lat2)
        lon2_rad = math.radians(lon2)
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))
        
        return round(R * c)
