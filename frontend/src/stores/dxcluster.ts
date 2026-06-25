import { defineStore } from 'pinia'
import { ref, computed, onScopeDispose } from 'vue'
import { dxclusterApi, type DxNode, type Spot, type ClusterStatus } from '@/api/dxcluster'
import { useAuthStore } from '@/stores/auth'

const MAX_SPOTS = 200

export const useDxClusterStore = defineStore('dxcluster', () => {
  const spots = ref<Spot[]>([])
  const status = ref<ClusterStatus | null>(null)
  const nodes = ref<DxNode[]>([])
  const selectedNode = ref<DxNode | null>(null)
  const wsConnected = ref(false)
  const error = ref<string | null>(null)

  let ws: WebSocket | null = null

  const isConnected = computed(() => status.value?.connected ?? false)
  const isConnecting = computed(() => status.value?.connecting ?? false)

  /** 拉取节点列表 + 当前状态 */
  const fetchInit = async () => {
    try {
      const [n, s] = await Promise.all([dxclusterApi.getNodes(), dxclusterApi.getStatus()])
      nodes.value = n
      status.value = s
      // 默认选中第一个节点（或当前已连接节点）
      if (s.current_node) {
        selectedNode.value = s.current_node
      } else if (n.length > 0) {
        selectedNode.value = n[0]
      }
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch DX cluster info'
    }
  }

  /** 建立 WebSocket 连接，接收实时 spot */
  let _reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let _reconnectAttempts = 0
  const MAX_RECONNECT = 5

  const connectWS = () => {
    if (ws && ws.readyState <= WebSocket.OPEN) return
    const authStore = useAuthStore()
    if (!authStore.token) return

    // 构造 WS URL（同源，走 vite 代理 / 生产 nginx）
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const url = `${proto}://${window.location.host}/api/v1/dxcluster/ws?token=${encodeURIComponent(authStore.token)}`
    ws = new WebSocket(url)

    ws.onopen = () => {
      wsConnected.value = true
      error.value = null
      _reconnectAttempts = 0
    }
    ws.onclose = () => {
      wsConnected.value = false
      // 指数退避重连
      if (_reconnectAttempts < MAX_RECONNECT) {
        const delay = Math.min(1000 * Math.pow(2, _reconnectAttempts), 16000)
        _reconnectTimer = setTimeout(() => {
          _reconnectAttempts++
          connectWS()
        }, delay)
      }
    }
    ws.onerror = () => { error.value = 'WebSocket error' }

    ws.onmessage = (ev) => {
      try {
        const msg = JSON.parse(ev.data)
        if (msg.type === 'spot' && msg.data) {
          // 新 spot 顶部插入，超限丢弃最旧
          spots.value.unshift(msg.data)
          if (spots.value.length > MAX_SPOTS) spots.value.pop()
        } else if (msg.type === 'disconnect') {
          // cluster 侧断开，刷新状态
          fetchStatus()
        }
      } catch { /* ignore malformed */ }
    }
  }

  const disconnectWS = () => {
    if (_reconnectTimer) { clearTimeout(_reconnectTimer); _reconnectTimer = null }
    _reconnectAttempts = MAX_RECONNECT // 阻止自动重连
    if (ws) {
      ws.onclose = null
      ws.close()
      ws = null
    }
    wsConnected.value = false
  }

  const fetchStatus = async () => {
    try { status.value = await dxclusterApi.getStatus() }
    catch (e: unknown) { error.value = e instanceof Error ? e.message : 'Failed to fetch status' }
  }

  /** 连接到选定节点 */
  const connect = async () => {
    if (!selectedNode.value) return
    error.value = null
    try {
      const res = await dxclusterApi.connect(selectedNode.value.host, selectedNode.value.port)
      // 后端在连接失败时仍返回 HTTP 200 但 success=false，需要额外判断
      if (!res.success) {
        status.value = res.status
        error.value = res.message
        throw new Error(res.message || 'Connection failed')
      }
      status.value = res.status
      // 连接成功后清空旧 spot，建 WS 接收新流
      spots.value = []
      connectWS()
      return res
    } catch (e: any) {
      error.value = e?.response?.data?.detail || e?.message
      throw e
    }
  }


  /** 断开 cluster 连接 */
  const disconnect = async () => {
    try {
      disconnectWS()
      status.value = await dxclusterApi.disconnect()
      spots.value = []
    } catch (e: any) { error.value = e?.message }
  }

  // 组件卸载时自动清理 WebSocket 和重连定时器
  onScopeDispose(() => { disconnectWS() })

  return {
    spots, status, nodes, selectedNode, wsConnected, error,
    isConnected, isConnecting,
    fetchInit, fetchStatus, connectWS, disconnectWS, connect, disconnect,
  }
})
