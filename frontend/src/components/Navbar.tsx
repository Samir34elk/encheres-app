import { useEffect, useState } from 'react'
import { Link, NavLink, useLocation } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { useThemeStore } from '../stores/themeStore'
import { useTranslation } from 'react-i18next'
import { Moon, Sun, LogOut, Bell, Layers, Gavel, Menu, X } from 'lucide-react'

export default function Navbar() {
  const { user, isAuthenticated, logout } = useAuthStore()
  const { theme, toggleTheme } = useThemeStore()
  const { t } = useTranslation()
  const location = useLocation()
  const [isMenuOpen, setIsMenuOpen] = useState(false)

  const publicLinks = [
    { to: '/sales', label: 'Prochaines ventes', icon: Gavel },
    { to: '/lots', label: 'Tous les lots', icon: Layers }
  ]

  const privateLinks = [{ to: '/alerts', label: 'Mes alertes', icon: Bell }]

  const navigationLinks = isAuthenticated ? [...publicLinks, ...privateLinks] : publicLinks

  useEffect(() => {
    setIsMenuOpen(false)
  }, [location.pathname])

  return (
    <nav className="sticky top-0 z-40 border-b border-gray-200/70 dark:border-gray-800/80 bg-white/90 dark:bg-gray-900/80 backdrop-blur">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between gap-4">
          <Link to="/" className="flex items-center gap-2 text-lg sm:text-xl font-semibold text-gray-900 dark:text-white">
            <span className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-primary-600 text-white font-bold">
              SE
            </span>
            <div className="flex flex-col leading-tight">
              <span>Suivi Enchères</span>
              <span className="text-xs font-normal text-gray-500 dark:text-gray-400">
                Gardez une longueur d&apos;avance
              </span>
            </div>
          </Link>

          <div className="flex items-center gap-2 sm:gap-3">
            <div className="hidden md:flex items-center gap-2 lg:gap-3">
              {navigationLinks.map(({ to, label, icon: Icon }) => (
                <NavLink
                  key={to}
                  to={to}
                  className={({ isActive }) =>
                    [
                      'inline-flex items-center gap-2 rounded-full px-3 py-2 text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-primary-50 text-primary-700 border border-primary-100 dark:bg-primary-900/30 dark:text-primary-200 dark:border-primary-800/70'
                        : 'text-gray-600 hover:text-primary-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:text-primary-200 dark:hover:bg-gray-800'
                    ].join(' ')
                  }
                >
                  <Icon className="h-4 w-4" />
                  <span>{label}</span>
                </NavLink>
              ))}

              {isAuthenticated && user?.is_admin && (
                <NavLink
                  to="/admin"
                  className={({ isActive }) =>
                    [
                      'inline-flex items-center gap-2 rounded-full px-3 py-2 text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-amber-100 text-amber-700 border border-amber-200 dark:bg-amber-500/10 dark:text-amber-200 dark:border-amber-500/40'
                        : 'text-amber-700 hover:text-amber-800 hover:bg-amber-50 dark:text-amber-300 dark:hover:text-amber-200 dark:hover:bg-amber-500/10'
                    ].join(' ')
                  }
                >
                  Espace admin
                </NavLink>
              )}
            </div>

            {isAuthenticated ? (
              <div className="hidden md:flex items-center gap-2">
                <Link
                  to="/favorites"
                  className="inline-flex items-center rounded-full border border-primary-100 bg-primary-50 px-3 py-2 text-sm font-medium text-primary-700 hover:bg-primary-100 dark:border-primary-500/30 dark:bg-primary-500/10 dark:text-primary-200 dark:hover:bg-primary-500/20"
                >
                  {t('favorites')}
                </Link>
                <div className="flex flex-col items-end leading-tight">
                  <span className="text-sm font-semibold text-gray-900 dark:text-white">
                    {user?.username || user?.email}
                  </span>
                  <span className="text-xs text-gray-500 dark:text-gray-400">Connecté</span>
                </div>
                <button
                  onClick={logout}
                  className="inline-flex items-center justify-center rounded-full border border-red-100 bg-red-50 p-2 text-red-600 transition-colors hover:bg-red-100 dark:border-red-500/30 dark:bg-red-500/10 dark:text-red-300 dark:hover:bg-red-500/20"
                  title={t('logout')}
                >
                  <LogOut size={18} />
                </button>
              </div>
            ) : (
              <div className="hidden md:flex items-center gap-2">
                <Link
                  to="/login"
                  className="inline-flex items-center rounded-full px-3 py-2 text-sm font-medium text-gray-600 transition-colors hover:text-primary-600 hover:bg-gray-100 dark:text-gray-300 dark:hover:text-primary-200 dark:hover:bg-gray-800"
                >
                  {t('login')}
                </Link>
                <Link
                  to="/register"
                  className="inline-flex items-center rounded-full bg-primary-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 dark:focus:ring-offset-gray-900"
                >
                  Créer un compte
                </Link>
              </div>
            )}

            <button
              onClick={toggleTheme}
              className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-gray-200 bg-white text-gray-600 transition-colors hover:text-primary-600 hover:border-primary-200 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:text-primary-200"
              title="Changer de thème"
            >
              {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
            </button>

            <button
              onClick={() => setIsMenuOpen((prev) => !prev)}
              className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-gray-200 bg-white text-gray-600 transition-colors hover:text-primary-600 hover:border-primary-200 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:text-primary-200 md:hidden"
              aria-label="Menu"
              aria-expanded={isMenuOpen}
            >
              {isMenuOpen ? <X size={22} /> : <Menu size={22} />}
            </button>
          </div>
        </div>
      </div>

      {isMenuOpen && (
        <div className="md:hidden border-t border-gray-200 bg-white/95 backdrop-blur dark:border-gray-800 dark:bg-gray-900/95">
          <div className="px-4 pb-4 pt-3 space-y-3">
            {navigationLinks.map(({ to, label }) => (
              <NavLink
                key={to}
                to={to}
                className={({ isActive }) =>
                  [
                    'flex items-center justify-between rounded-2xl px-4 py-3 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary-600 text-white shadow-sm dark:bg-primary-500'
                      : 'bg-gray-100 text-gray-700 hover:bg-primary-50 hover:text-primary-600 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700'
                  ].join(' ')
                }
              >
                {label}
              </NavLink>
            ))}

            {isAuthenticated && user?.is_admin && (
              <NavLink
                to="/admin"
                className={({ isActive }) =>
                  [
                    'flex items-center justify-between rounded-2xl px-4 py-3 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-amber-500 text-white shadow-sm'
                      : 'bg-amber-50 text-amber-700 hover:bg-amber-100 dark:bg-amber-500/10 dark:text-amber-200 dark:hover:bg-amber-500/20'
                  ].join(' ')
                }
              >
                Espace admin
              </NavLink>
            )}

            {isAuthenticated ? (
              <>
                <div className="rounded-2xl bg-gray-100 px-4 py-3 dark:bg-gray-800">
                  <span className="block text-sm font-semibold text-gray-900 dark:text-white">
                    {user?.username || user?.email}
                  </span>
                  <span className="text-xs text-gray-500 dark:text-gray-400">Connecté</span>
                </div>
                <NavLink
                  to="/favorites"
                  className={({ isActive }) =>
                    [
                      'flex items-center justify-between rounded-2xl px-4 py-3 text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-primary-600 text-white shadow-sm dark:bg-primary-500'
                        : 'bg-primary-50 text-primary-700 hover:bg-primary-100 dark:bg-primary-500/10 dark:text-primary-200 dark:hover:bg-primary-500/20'
                    ].join(' ')
                  }
                >
                  {t('favorites')}
                </NavLink>
                <button
                  onClick={logout}
                  className="flex w-full items-center justify-center rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-red-600 transition-colors hover:bg-red-100 dark:border-red-500/40 dark:bg-red-500/10 dark:text-red-200 dark:hover:bg-red-500/20"
                >
                  {t('logout')}
                </button>
              </>
            ) : (
              <div className="space-y-2">
                <Link
                  to="/login"
                  className="flex w-full items-center justify-center rounded-2xl border border-gray-200 bg-white px-4 py-3 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-100 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700"
                >
                  {t('login')}
                </Link>
                <Link
                  to="/register"
                  className="flex w-full items-center justify-center rounded-2xl bg-primary-600 px-4 py-3 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-primary-700"
                >
                  Créer un compte
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </nav>
  )
}
