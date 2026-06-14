"""距离计算工具"""

import math
from typing import Optional


class DistanceCalculator:
    """地理距离计算器（使用Haversine公式）"""

    R = 6371.0  # 地球平均半径（公里）

    @staticmethod
    def haversine(
        lat1: float, lon1: float,
        lat2: float, lon2: float
    ) -> float:
        """计算两点间的Haversine距离（公里）"""
        lat1_r = math.radians(lat1)
        lon1_r = math.radians(lon1)
        lat2_r = math.radians(lat2)
        lon2_r = math.radians(lon2)

        dlat = lat2_r - lat1_r
        dlon = lon2_r - lon1_r

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return DistanceCalculator.R * c

    @staticmethod
    def bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """计算方位角（度）"""
        lat1_r = math.radians(lat1)
        lat2_r = math.radians(lat2)
        dlon = math.radians(lon2 - lon1)

        x = math.sin(dlon) * math.cos(lat2_r)
        y = math.cos(lat1_r) * math.sin(lat2_r) - math.sin(lat1_r) * math.cos(lat2_r) * math.cos(dlon)

        bearing = math.degrees(math.atan2(x, y))
        return (bearing + 360) % 360

    @staticmethod
    def grid_distance(grid1: str, grid2: str) -> Optional[float]:
        """通过梅登网格计算距离"""
        from app.utils.grid_utils import GridUtils

        pos1 = GridUtils.to_lat_lon(grid1)
        pos2 = GridUtils.to_lat_lon(grid2)

        if not pos1 or not pos2:
            return None

        return DistanceCalculator.haversine(pos1[0], pos1[1], pos2[0], pos2[1])
