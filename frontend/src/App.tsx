import { Routes, Route } from 'react-router-dom'
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
import PublicRoute from './components/PublicRoute'
import LoadingScreen from './components/LoadingScreen'

function App() {
  const { theme } = useThemeStore()
  const { checkAuth, hasCheckedAuth } = useAuthStore()

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
        <Route path="/" element={<Layout />}>
          <Route index element={<HomePage />} />

          <Route element={<PublicRoute />}>
            <Route path="login" element={<LoginPage />} />
            <Route path="register" element={<RegisterPage />} />
          </Route>

          <Route element={<PrivateRoute />}>
            <Route path="sales" element={<SalesPage />} />
            <Route path="sales/:saleNumber" element={<SaleDetailPage />} />
            <Route path="lots" element={<LotsPage />} />
            <Route path="lots/:id" element={<LotDetailPage />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="favorites" element={<FavoritesPage />} />
            <Route path="alerts" element={<AlertsPage />} />
          </Route>

          <Route element={<AdminRoute />}>
            <Route path="admin" element={<AdminPage />} />
          </Route>

          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Routes>
      <Toaster position="top-right" />
    </>
  )
}

export default App
