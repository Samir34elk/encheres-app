import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import LoadingScreen from './LoadingScreen'

export default function PrivateRoute() {
  const { isAuthenticated, hasCheckedAuth } = useAuthStore()
  const location = useLocation()

  if (!hasCheckedAuth) {
    return <LoadingScreen />
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return <Outlet />
}
