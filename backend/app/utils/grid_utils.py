"""梅登网格坐标工具"""

import math
import re
from typing import Tuple, Optional


class GridUtils:
    """梅登网格(Maidenhead Grid)坐标工具"""

    @staticmethod
    def validate(grid: str) -> bool:
        """验证网格格式（4位或6位）"""
        pattern = r'^[A-R]{2}[0-9]{2}([a-x]{2})?$'
        return bool(re.match(pattern, grid, re.IGNORECASE))

    @staticmethod
    def to_lat_lon(grid: str) -> Optional[Tuple[float, float]]:
        """将梅登网格转为经纬度（返回网格中心点）"""
        if not GridUtils.validate(grid):
            return None

        grid = grid.upper()

        lon = (ord(grid[0]) - ord('A')) * 20 - 180
        lat = (ord(grid[1]) - ord('A')) * 10 - 90

        lon += (int(grid[2]) * 2)
        lat += (int(grid[3]) * 1)

        # 4位网格返回中心
        if len(grid) == 4:
            return (lat + 0.5, lon + 1.0)

        # 6位网格
        lon += (ord(grid[4]) - ord('A')) * (2 / 24)
        lat += (ord(grid[5]) - ord('A')) * (1 / 24)

        return (lat + (1 / 48), lon + (1 / 24))

    @staticmethod
    def from_lat_lon(lat: float, lon: float, length: int = 6) -> str:
        """将经纬度转为梅登网格（4位或6位）"""
        lon += 180
        lat += 90

        field_lon = chr(int(lon / 20) + ord('A'))
        field_lat = chr(int(lat / 10) + ord('A'))

        square_lon = int(lon % 20 / 2)
        square_lat = int(lat % 10 / 1)

        result = f"{field_lon}{field_lat}{square_lon}{square_lat}"

        if length >= 6:
            subsquare_lon = int((lon % 2) / (2 / 24))
            subsquare_lat = int((lat % 1) / (1 / 24))
            result += f"{chr(subsquare_lon + ord('a'))}{chr(subsquare_lat + ord('a'))}"

        return result

    @staticmethod
    def distance_between(grid1: str, grid2: str) -> Optional[float]:
        """计算两个梅登网格之间的距离（公里）"""
        pos1 = GridUtils.to_lat_lon(grid1)
        pos2 = GridUtils.to_lat_lon(grid2)

        if not pos1 or not pos2:
            return None

        lat1, lon1 = math.radians(pos1[0]), math.radians(pos1[1])
        lat2, lon2 = math.radians(pos2[0]), math.radians(pos2[1])

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))

        return 6371 * c
