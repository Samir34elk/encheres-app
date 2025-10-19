import { Link } from 'react-router-dom'
import { useAuthStore } from '../stores/authStore'
import { useThemeStore } from '../stores/themeStore'
import { useTranslation } from 'react-i18next'
import { Moon, Sun, LogOut } from 'lucide-react'

export default function Navbar() {
  const { user, isAuthenticated, logout } = useAuthStore()
  const { theme, toggleTheme } = useThemeStore()
  const { t } = useTranslation()

  return (
    <nav className="bg-white dark:bg-gray-800 shadow-md">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          <Link to="/" className="text-xl font-bold text-primary-600 dark:text-primary-400">
            Enchères du Domaine
          </Link>

          <div className="flex items-center gap-4">
            <Link to="/sales" className="hover:text-primary-600 dark:hover:text-primary-400">
              Ventes
            </Link>
            <Link to="/lots" className="hover:text-primary-600 dark:hover:text-primary-400">
              {t('lots')}
            </Link>

            {isAuthenticated ? (
              <>
                <Link to="/dashboard" className="hover:text-primary-600 dark:hover:text-primary-400">
                  {t('dashboard')}
                </Link>
                <Link to="/favorites" className="hover:text-primary-600 dark:hover:text-primary-400">
                  {t('favorites')}
                </Link>
                {user?.is_admin && (
                  <Link to="/admin" className="hover:text-primary-600 dark:hover:text-primary-400">
                    Admin
                  </Link>
                )}
                <button onClick={logout} className="hover:text-primary-600 dark:hover:text-primary-400">
                  <LogOut size={20} />
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="hover:text-primary-600 dark:hover:text-primary-400">
                  {t('login')}
                </Link>
                <Link
                  to="/register"
                  className="bg-primary-600 text-white px-4 py-2 rounded-md hover:bg-primary-700"
                >
                  {t('register')}
                </Link>
              </>
            )}

            <button onClick={toggleTheme} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
              {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
            </button>
          </div>
        </div>
      </div>
    </nav>
  )
}
