import { Navigate, Outlet } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'

export default function AdminRoute() {
  const { user, isAuthenticated } = useAuthStore()

  if (!isAuthenticated || !user?.is_admin) {
    return <Navigate to="/" replace />
  }

  return <Outlet />
}
