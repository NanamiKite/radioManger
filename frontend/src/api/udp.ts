import api from './index'

export interface UDPStatus {
  running: boolean
  wsjtx_port: number
  n1mm_port: number
  qso_count: number
  last_qso: {
    source: string
    call_sign: string
    band: string
    mode: string
    time: string
  } | null
  ws_clients: number
}

export const udpApi = {
  getStatus(): Promise<{ data: UDPStatus }> {
    return api.get('/udp/status')
  },

  start(wsjtx_port?: number, n1mm_port?: number): Promise<{ data: UDPStatus }> {
    return api.post('/udp/start', { wsjtx_port, n1mm_port })
  },

  stop(): Promise<{ data: { running: boolean } }> {
    return api.post('/udp/stop')
  },

  /** 创建 WebSocket 连接（用于实时接收 QSO） */
  createWebSocket(token: string): WebSocket {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    return new WebSocket(`${protocol}//${host}/api/v1/udp/ws?token=${token}`)
  }
}
