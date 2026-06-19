"""DX Cluster 相关 Pydantic 模型。"""

from pydantic import BaseModel, Field
from typing import Optional, Any


class SpotResponse(BaseModel):
    """单条 Spot 响应。"""
    spotter: str = Field(..., description="通报者呼号（发 spot 的人）")
    freq: float = Field(..., description="频率 (MHz)")
    dx_callsign: str = Field(..., description="被叫台呼号（通联目标）")
    mode: str = Field("", description="模式（FT8/CW/SSB 等）")
    comment: str = Field("", description="spotter 注释")
    time_utc: Optional[str] = Field(None, description="原始 UTC 时间字符串")
    band: str = Field("", description="由频率推算的业余波段")
    received_at: str = Field(..., description="本服务收到该 spot 的 UTC ISO 时间")


class NodeInfoResponse(BaseModel):
    """DX Cluster 节点信息。"""
    host: str
    port: int
    name: str
    country: str
    remark: str = ""


class ClusterStatusResponse(BaseModel):
    """DX Cluster 连接状态。"""
    connected: bool
    connecting: bool = False
    current_node: Optional[NodeInfoResponse] = None
    callsign: Optional[str] = None
    spot_count: int = 0
    uptime_seconds: Optional[float] = None


class SwitchNodeRequest(BaseModel):
    """连接/切换节点请求。"""
    node_host: str = Field(..., description="节点主机地址")
    node_port: int = Field(..., ge=1, le=65535, description="节点端口")


class ConnectResult(BaseModel):
    """连接操作结果。"""
    success: bool
    message: str = ""
    status: Optional[ClusterStatusResponse] = None
