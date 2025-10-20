import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import LoadingScreen from './LoadingScreen'

export default function PublicRoute() {
  const { isAuthenticated, hasCheckedAuth } = useAuthStore()
  const location = useLocation()

  if (!hasCheckedAuth) {
    return <LoadingScreen />
  }

  if (isAuthenticated) {
    const redirectTo = (location.state as { from?: string } | null)?.from || '/'
    return <Navigate to={redirectTo} replace />
  }

  return <Outlet />
}
