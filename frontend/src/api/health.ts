import axios from 'axios'

/** 轻量级 /health 请求工具，绕过 /api/v1 拦截器 */
const healthAxios = axios.create({ baseURL: '/', timeout: 5000 })

export interface HealthResponse {
  status: string
  version?: string
  database: string
  subsystems: Record<string, string>
  db_path?: string
  db_dir?: string
}

export async function fetchHealth(): Promise<HealthResponse> {
  const res = await healthAxios.get<HealthResponse>('/health')
  return res.data
}
