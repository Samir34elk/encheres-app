import { describe, it, expect, beforeEach, vi } from 'vitest'
import { useAuthStore } from '@/stores/authStore'
import api from '@/services/api'

// Mock the API
vi.mock('@/services/api')

describe('AuthStore', () => {
  beforeEach(() => {
    // Reset store state before each test
    useAuthStore.setState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
    })
    vi.clearAllMocks()
  })

  it('should have initial state', () => {
    const state = useAuthStore.getState()
    expect(state.user).toBeNull()
    expect(state.isAuthenticated).toBe(false)
    expect(state.isLoading).toBe(false)
  })

  it('should login successfully', async () => {
    const mockUser = {
      id: 1,
      email: 'test@example.com',
      username: 'testuser',
      is_admin: false,
      theme: 'light',
      language: 'fr',
    }

    vi.mocked(api.post).mockResolvedValueOnce({
      data: {
        access_token: 'fake-token',
        refresh_token: 'fake-refresh-token',
        token_type: 'bearer',
      },
    } as any)

    vi.mocked(api.get).mockResolvedValueOnce({
      data: mockUser,
    } as any)

    const { login } = useAuthStore.getState()
    await login('test@example.com', 'password')

    const state = useAuthStore.getState()
    expect(state.user).toEqual(mockUser)
    expect(state.isAuthenticated).toBe(true)
  })

  it('should handle login failure', async () => {
    vi.mocked(api.post).mockRejectedValueOnce(new Error('Invalid credentials'))

    const { login } = useAuthStore.getState()

    await expect(login('test@example.com', 'wrongpassword')).rejects.toThrow()

    const state = useAuthStore.getState()
    expect(state.user).toBeNull()
    expect(state.isAuthenticated).toBe(false)
  })

  it('should logout successfully', async () => {
    // Set authenticated state
    useAuthStore.setState({
      user: { id: 1, email: 'test@example.com' } as any,
      isAuthenticated: true,
    })

    vi.mocked(api.post).mockResolvedValueOnce({ data: { message: 'Logged out' } } as any)

    const { logout } = useAuthStore.getState()

    // Mock window.location.href
    delete (window as any).location
    window.location = { href: '' } as any

    await logout()

    const state = useAuthStore.getState()
    expect(state.user).toBeNull()
    expect(state.isAuthenticated).toBe(false)
  })

  it('should check auth successfully', async () => {
    const mockUser = {
      id: 1,
      email: 'test@example.com',
      username: 'testuser',
      is_admin: false,
      theme: 'light',
      language: 'fr',
    }

    vi.mocked(api.get).mockResolvedValueOnce({
      data: mockUser,
    } as any)

    const { checkAuth } = useAuthStore.getState()
    await checkAuth()

    const state = useAuthStore.getState()
    expect(state.user).toEqual(mockUser)
    expect(state.isAuthenticated).toBe(true)
  })

  it('should handle check auth failure', async () => {
    vi.mocked(api.get).mockRejectedValueOnce(new Error('Unauthorized'))

    const { checkAuth } = useAuthStore.getState()
    await checkAuth()

    const state = useAuthStore.getState()
    expect(state.user).toBeNull()
    expect(state.isAuthenticated).toBe(false)
  })
})
