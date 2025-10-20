import { Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { useAuthStore } from './stores/authStore'
import { useThemeStore } from './stores/themeStore'
import { useEffect } from 'react'

// Pages
import HomePage from './pages/HomePage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import SalesPage from './pages/SalesPage'
import SaleDetailPage from './pages/SaleDetailPage'
import LotsPage from './pages/LotsPage'
import LotDetailPage from './pages/LotDetailPage'
import FavoritesPage from './pages/FavoritesPage'
import AlertsPage from './pages/AlertsPage'
import AdminPage from './pages/AdminPage'
import NotFoundPage from './pages/NotFoundPage'

// Components
import Layout from './components/Layout'
import PrivateRoute from './components/PrivateRoute'
import AdminRoute from './components/AdminRoute'
import LoadingScreen from './components/LoadingScreen'

function App() {
  const { theme } = useThemeStore()
  const { checkAuth, isAuthenticated, hasCheckedAuth } = useAuthStore()

  useEffect(() => {
    if (!hasCheckedAuth) {
      checkAuth()
    }
  }, [checkAuth, hasCheckedAuth])

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [theme])

  if (!hasCheckedAuth) {
    return <LoadingScreen />
  }

  return (
    <>
      <Routes>
        {isAuthenticated ? (
          <Route path="/" element={<Layout />}>
            <Route index element={<HomePage />} />
            <Route path="login" element={<Navigate to="/" replace />} />
            <Route path="register" element={<Navigate to="/" replace />} />
            <Route path="sales" element={<SalesPage />} />
            <Route path="sales/:saleNumber" element={<SaleDetailPage />} />
            <Route path="lots" element={<LotsPage />} />
            <Route path="lots/:id" element={<LotDetailPage />} />

            {/* Protected routes */}
            <Route element={<PrivateRoute />}>
              <Route path="dashboard" element={<DashboardPage />} />
              <Route path="favorites" element={<FavoritesPage />} />
              <Route path="alerts" element={<AlertsPage />} />
            </Route>

            {/* Admin routes */}
            <Route element={<AdminRoute />}>
              <Route path="admin" element={<AdminPage />} />
            </Route>

            <Route path="*" element={<NotFoundPage />} />
          </Route>
        ) : (
          <Route path="/" element={<Layout />}>
            <Route index element={<HomePage />} />
            <Route path="login" element={<LoginPage />} />
            <Route path="register" element={<RegisterPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        )}
      </Routes>
      <Toaster position="top-right" />
    </>
  )
}

export default App
