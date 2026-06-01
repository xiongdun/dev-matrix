import { api } from './index'

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  token: string
  refresh_token: string
  expires_at: number
  user: {
    id: number
    username: string
    nickname: string | null
    email: string | null
    avatar: string | null
    roles: Array<{ id: number; name: string; display_name: string }>
  }
}

export interface UserInfo {
  id: number
  username: string
  nickname: string | null
  email: string | null
  avatar: string | null
  roles: Array<{ id: number; name: string; display_name: string }>
  permissions: string[]
  agents: string[]
}

export const authApi = {
  login(data: LoginRequest) {
    return api.post<LoginResponse>('/auth/login', data)
  },

  logout() {
    return api.post('/auth/logout')
  },

  getMe() {
    return api.get<UserInfo>('/auth/me')
  },

  refreshToken() {
    return api.post<{ token: string; expires_at: number }>('/auth/refresh')
  },

  changePassword(oldPassword: string, newPassword: string) {
    return api.post('/auth/password', { old_password: oldPassword, new_password: newPassword })
  },
}
