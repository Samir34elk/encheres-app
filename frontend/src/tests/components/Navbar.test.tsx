import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Navbar from '@/components/Navbar'
import { useAuthStore } from '@/stores/authStore'

// Mock the auth store
vi.mock('@/stores/authStore')

const renderNavbar = () => {
  return render(
    <BrowserRouter>
      <Navbar />
    </BrowserRouter>
  )
}

describe('Navbar', () => {
  it('should render navigation links', () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      checkAuth: vi.fn(),
    })

    renderNavbar()

    // Should have app name/logo
    expect(screen.getByText(/enchères/i)).toBeInTheDocument()
  })

  it('should show login/register when not authenticated', () => {
    vi.mocked(useAuthStore).mockReturnValue({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      checkAuth: vi.fn(),
    })

    renderNavbar()

    // Should have login and register links
    const links = screen.getAllByRole('link')
    const linkTexts = links.map(link => link.textContent?.toLowerCase())

    // At least one link should contain login or register
    const hasAuthLinks = linkTexts.some(text =>
      text?.includes('connexion') || text?.includes('login') ||
      text?.includes('inscription') || text?.includes('register')
    )

    expect(hasAuthLinks).toBe(true)
  })

  it('should show user menu when authenticated', () => {
    const mockUser = {
      id: 1,
      email: 'test@example.com',
      username: 'testuser',
      is_admin: false,
      theme: 'light',
      language: 'fr',
    }

    vi.mocked(useAuthStore).mockReturnValue({
      user: mockUser,
      isAuthenticated: true,
      isLoading: false,
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      checkAuth: vi.fn(),
    })

    renderNavbar()

    // Should show username or email
    expect(
      screen.getByText(mockUser.username) || screen.getByText(mockUser.email)
    ).toBeInTheDocument()
  })
})
