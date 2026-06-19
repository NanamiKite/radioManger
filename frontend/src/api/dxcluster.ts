import api from './index'

/** DX Cluster 节点信息 */
export interface DxNode {
  host: string
  port: number
  name: string
  country: string
  remark: string
}

/** 单条 Spot */
export interface Spot {
  spotter: string
  freq: number
  dx_callsign: string
  mode: string
  comment: string
  time_utc: string | null
  band: string
  received_at: string
}

/** 连接状态 */
export interface ClusterStatus {
  connected: boolean
  connecting: boolean
  current_node: DxNode | null
  callsign: string | null
  spot_count: number
  uptime_seconds: number | null
}

export const dxclusterApi = {
  getNodes(): Promise<DxNode[]> {
    return api.get('/dxcluster/nodes')
  },

  getStatus(): Promise<ClusterStatus> {
    return api.get('/dxcluster/status')
  },

  getSpots(limit = 50): Promise<Spot[]> {
    return api.get('/dxcluster/spots', { params: { limit } })
  },

  connect(nodeHost: string, nodePort: number): Promise<{ success: boolean; message: string; status: ClusterStatus }> {
    return api.post('/dxcluster/connect', { node_host: nodeHost, node_port: nodePort })
  },

  disconnect(): Promise<ClusterStatus> {
    return api.post('/dxcluster/disconnect')
  },
}
