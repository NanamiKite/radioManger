import api from './index'
import type { User } from '@/types'

export const authApi = {
  register(data: any): Promise<User> {
    return api.post('/auth/register', data)
  },

  login(data: {
    username: string
    password: string
    remember_me?: boolean
  }): Promise<{
    access_token: string
    refresh_token: string
    token_type: string
    expires_in: number
    user: User
  }> {
    return api.post('/auth/login', data)
  },

  getMe(): Promise<User> {
    return api.get('/auth/me')
  },

  logout(): Promise<any> {
    return api.post('/auth/logout')
  },

  /** 申请注销账号（服务器模式） */
  deleteAccount(password: string): Promise<any> {
    return api.post('/auth/delete-account', { password })
  },

  /** 撤销注销申请（服务器模式） */
  cancelDeleteAccount(): Promise<any> {
    return api.post('/auth/cancel-delete')
  },

  /** 确认注销账号（服务器模式，需验证码） */
  confirmDeleteAccount(code: string): Promise<any> {
    return api.post('/auth/confirm-delete', { code })
  },
}
