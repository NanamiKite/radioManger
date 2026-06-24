import api from './index'

export interface AdminUser {
  id: number
  username: string
  email: string
  full_name?: string
  role: string
  is_active: boolean
  created_at?: string
}

export interface AuditLog {
  id: number
  user_id: number
  username: string
  action: string
  target_type?: string
  target_id?: number
  detail?: string
  ip_address?: string
  created_at?: string
}

export interface SystemConfig {
  id: number
  key: string
  value?: string
  value_type: string
  description?: string
  updated_at?: string
}

export interface SystemStatus {
  database_mode: string
  total_users: number
  active_users: number
  total_qso: number
  total_stations: number
  online_sessions: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export const adminApi = {
  // 用户管理
  getUsers(params: { page?: number; page_size?: number; keyword?: string; role?: string; is_active?: boolean }): Promise<PaginatedResponse<AdminUser>> {
    return api.get('/admin/users', { params })
  },
  getUser(userId: number): Promise<AdminUser> {
    return api.get(`/admin/users/${userId}`)
  },
  toggleUser(userId: number): Promise<AdminUser> {
    return api.post(`/admin/users/${userId}/toggle`)
  },
  resetPassword(userId: number, newPassword: string): Promise<any> {
    return api.post(`/admin/users/${userId}/reset-password`, { new_password: newPassword })
  },
  deleteUser(userId: number): Promise<any> {
    return api.delete(`/admin/users/${userId}`)
  },
  getUserStats(userId: number): Promise<{ qso_count: number; station_count: number }> {
    return api.get(`/admin/users/${userId}/stats`)
  },

  // 审计日志
  getAuditLogs(params: { page?: number; page_size?: number; user_id?: number; action?: string }): Promise<PaginatedResponse<AuditLog>> {
    return api.get('/admin/audit-logs', { params })
  },

  // 系统配置
  getConfigs(): Promise<SystemConfig[]> {
    return api.get('/admin/system/config')
  },
  updateConfig(key: string, value: string): Promise<any> {
    return api.patch('/admin/system/config', { key, value })
  },

  // 系统状态
  getStatus(): Promise<SystemStatus> {
    return api.get('/admin/system/status')
  },
}
