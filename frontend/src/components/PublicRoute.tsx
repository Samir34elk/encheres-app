import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import LoadingScreen from './LoadingScreen'

export default function PublicRoute() {
  const { isAuthenticated, hasCheckedAuth } = useAuthStore()

  if (!hasCheckedAuth) {
    return <LoadingScreen />
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  return <Outlet />
}
