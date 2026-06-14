from pydantic import BaseModel
from typing import Optional, List
from datetime import date


class StatsOverview(BaseModel):
    """统计概览"""
    total_qso: int = 0
    total_dxcc: int = 0
    total_waz: int = 0
    qsl_sent: int = 0
    qsl_rcvd: int = 0
    eqsl_sent: int = 0
    eqsl_rcvd: int = 0
    lotw_confirmed: int = 0
    total_distance: int = 0
    average_distance: float = 0
    last_qso_date: Optional[date] = None


class DXCCEntry(BaseModel):
    """DXCC单条统计"""
    entity: str
    code: str
    count: int
    first_contact: Optional[date] = None
    last_contact: Optional[date] = None
    qsl_status: str = "pending"


class DXCCStats(BaseModel):
    """DXCC统计"""
    total_dxcc: int = 0
    confirmed_dxcc: int = 0
    dxcc_list: List[DXCCEntry] = []


class WAZEntry(BaseModel):
    """WAZ单条统计"""
    zone: int
    count: int
    first_contact: Optional[date] = None
    last_contact: Optional[date] = None


class WAZStats(BaseModel):
    """WAZ统计"""
    total_waz: int = 0
    confirmed_waz: int = 0
    waz_list: List[WAZEntry] = []


class BandStatEntry(BaseModel):
    """波段单条统计"""
    band: str
    qso_count: int = 0
    percentage: float = 0


class BandStats(BaseModel):
    """波段统计"""
    band_stats: List[BandStatEntry] = []


class ModeStatEntry(BaseModel):
    """模式单条统计"""
    mode: str
    qso_count: int = 0
    percentage: float = 0


class ModeStats(BaseModel):
    """模式统计"""
    mode_stats: List[ModeStatEntry] = []
