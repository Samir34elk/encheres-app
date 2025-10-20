import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,  // Enable sending cookies with requests
})

// Add auth token to requests (fallback to localStorage for backward compatibility)
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle token expiration
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const headers = (error.config?.headers || {}) as Record<string, string>
    const skipRedirect =
      headers['X-Skip-Auth-Redirect'] === 'true' || headers['x-skip-auth-redirect'] === 'true'

    if (error.response?.status === 401 && !skipRedirect) {
      // Clear localStorage tokens (if any)
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      // Cookies will be cleared by backend on logout
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
