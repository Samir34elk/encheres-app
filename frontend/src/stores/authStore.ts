import { create } from 'zustand'
import api from '../services/api'

interface User {
  id: number
  email: string
  username: string
  full_name?: string
  is_admin: boolean
  theme: string
  language: string
}

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, username: string, password: string) => Promise<void>
  logout: () => Promise<void>
  checkAuth: () => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,

  login: async (email, password) => {
    const formData = new FormData()
    formData.append('username', email)
    formData.append('password', password)

    const { data } = await api.post('/auth/login', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })

    // Tokens are now in httpOnly cookies set by backend
    // Keep localStorage for backward compatibility (optional)
    // The cookies will take precedence on the backend side

    const userResponse = await api.get('/auth/me')
    set({ user: userResponse.data, isAuthenticated: true })
  },

  register: async (email, username, password) => {
    await api.post('/auth/register', { email, username, password })
  },

  logout: async () => {
    try {
      // Call backend to clear httpOnly cookies
      await api.post('/auth/logout')
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      // Clear localStorage (if any)
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      set({ user: null, isAuthenticated: false })
      window.location.href = '/login'
    }
  },

  checkAuth: async () => {
    // With httpOnly cookies, we always try to check auth
    // The cookies will be sent automatically with the request
    try {
      const { data } = await api.get('/auth/me')
      set({ user: data, isAuthenticated: true })
    } catch (error) {
      // If auth fails, clear everything
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      set({ isAuthenticated: false, user: null })
    }
  },
}))
