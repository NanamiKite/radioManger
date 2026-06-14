import api from './index'
import type { User } from '@/types'

// export const authApi = {
//   register(data: {
//     username: string
//     email: string
//     password: string
//     confirm_password: string
//     full_name?: string
//   }): Promise<User> {
//     return api.post('/auth/register', data)
//   },

//   login(data: {
//     username: string
//     password: string
//     remember_me?: boolean
//   }): Promise<{
//     access_token: string
//     refresh_token: string
//     token_type: string
//     expires_in: number
//     user: User
//   }> {
//     return api.post('/auth/login', data)
//   },

//   getMe(): Promise<User> {
//     return api.get('/auth/me')
//   },

//   logout(): Promise<any> {
//     return api.post('/auth/logout')
//   }
// }


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
  }
}
