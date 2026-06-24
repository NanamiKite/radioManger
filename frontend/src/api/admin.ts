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

export const adminApi = {
  // 用户管理
  getUsers(params: { page?: number; page_size?: number; keyword?: string; role?: string; is_active?: boolean }) {
    return api.get('/admin/users', { params })
  },
  getUser(userId: number) {
    return api.get(`/admin/users/${userId}`)
  },
  toggleUser(userId: number) {
    return api.post(`/admin/users/${userId}/toggle`)
  },
  resetPassword(userId: number, newPassword: string) {
    return api.post(`/admin/users/${userId}/reset-password`, { new_password: newPassword })
  },
  deleteUser(userId: number) {
    return api.delete(`/admin/users/${userId}`)
  },
  getUserStats(userId: number) {
    return api.get(`/admin/users/${userId}/stats`)
  },

  // 审计日志
  getAuditLogs(params: { page?: number; page_size?: number; user_id?: number; action?: string }) {
    return api.get('/admin/audit-logs', { params })
  },

  // 系统配置
  getConfigs() {
    return api.get('/admin/system/config')
  },
  updateConfig(key: string, value: string) {
    return api.patch('/admin/system/config', { key, value })
  },

  // 系统状态
  getStatus() {
    return api.get('/admin/system/status')
  },
}
