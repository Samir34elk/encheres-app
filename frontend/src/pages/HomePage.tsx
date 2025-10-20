import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Search, Bell, Heart, BarChart3, LogIn, UserPlus } from 'lucide-react'
import toast from 'react-hot-toast'
import DashboardPage from './DashboardPage'
import { useAuthStore } from '../stores/authStore'

export default function HomePage() {
  const { t } = useTranslation()
  const {
    isAuthenticated,
    login: loginAction,
    register: registerAction
  } = useAuthStore()

  const [authMode, setAuthMode] = useState<'login' | 'register'>('login')

  const [loginEmail, setLoginEmail] = useState('')
  const [loginPassword, setLoginPassword] = useState('')
  const [loginLoading, setLoginLoading] = useState(false)

  const [registerEmail, setRegisterEmail] = useState('')
  const [registerUsername, setRegisterUsername] = useState('')
  const [registerPassword, setRegisterPassword] = useState('')
  const [registerLoading, setRegisterLoading] = useState(false)

  if (isAuthenticated) {
    return <DashboardPage />
  }

  const leftFeatures = [
    {
      icon: <Search className="h-5 w-5" />,
      title: 'Panorama complet',
      description: 'Ventes du domaine centralisées avec recherche textuelle et filtres avancés.'
    },
    {
      icon: <Bell className="h-5 w-5" />,
      title: 'Alertes en temps réel',
      description: 'Notifications instantanées à la moindre évolution sur vos lots suivis.'
    },
    {
      icon: <Heart className="h-5 w-5" />,
      title: 'Suivi intelligent',
      description: 'Favoris synchronisés, notes privées et historique de consultation conservé.'
    },
    {
      icon: <BarChart3 className="h-5 w-5" />,
      title: 'Pilotage simplifié',
      description: 'Tableau de bord clair pour visualiser ventes, alertes et activité en un clin d’œil.'
    }
  ]

  const handleLogin = async (event: React.FormEvent) => {
    event.preventDefault()
    setLoginLoading(true)

    try {
      await loginAction(loginEmail, loginPassword)
      toast.success('Connexion réussie !')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Erreur de connexion')
    } finally {
      setLoginLoading(false)
    }
  }

  const handleRegister = async (event: React.FormEvent) => {
    event.preventDefault()
    setRegisterLoading(true)

    try {
      await registerAction(registerEmail, registerUsername, registerPassword)
      toast.success('Inscription réussie ! Connectez-vous pour continuer.')
      setAuthMode('login')
      setLoginEmail(registerEmail)
      setRegisterEmail('')
      setRegisterUsername('')
      setRegisterPassword('')
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Erreur lors de l'inscription")
    } finally {
      setRegisterLoading(false)
    }
  }

  return (
    <div>
      <section className="py-16">
        <div className="mx-auto flex max-w-6xl flex-col gap-12 px-4 lg:flex-row lg:items-start">
          <div className="flex-1 space-y-6 text-center lg:text-left">
            <h1 className="text-4xl font-bold text-gray-900 transition-opacity duration-700 ease-in-out dark:text-white sm:text-5xl">
              {t('welcome')} - Suivi Enchères
            </h1>
            <p className="text-lg text-gray-600 transition-opacity duration-700 ease-in-out dark:text-gray-300">
              Surveillez les ventes publiques, préparez vos enchères et recevez les informations clés au moment opportun.
            </p>
            <ul className="mx-auto grid max-w-xl gap-3 text-left sm:grid-cols-2">
              {leftFeatures.map((feature, index) => (
                <HeroBullet key={index} {...feature} />
              ))}
            </ul>
          </div>

          <div className="w-full max-w-lg self-center rounded-3xl border border-gray-200 bg-white/90 p-6 shadow-xl backdrop-blur transition-shadow duration-700 ease-in-out dark:border-gray-700 dark:bg-gray-900/80">
            <div className="inline-flex rounded-full border border-gray-200 bg-gray-100 p-1 text-sm font-medium shadow-inner transition-all duration-700 ease-in-out dark:border-gray-700 dark:bg-gray-800">
              <button
                type="button"
                onClick={() => setAuthMode('login')}
                className={`inline-flex items-center gap-2 rounded-full px-4 py-1.5 transition-[color,background-color,transform] duration-700 ease-in-out ${
                  authMode === 'login'
                    ? 'bg-white text-primary-600 shadow-sm dark:bg-gray-900 dark:text-primary-300'
                    : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
                }`}
              >
                <LogIn className="h-4 w-4" />
                Connexion
              </button>
              <button
                type="button"
                onClick={() => setAuthMode('register')}
                className={`inline-flex items-center gap-2 rounded-full px-4 py-1.5 transition-[color,background-color,transform] duration-700 ease-in-out ${
                  authMode === 'register'
                    ? 'bg-white text-primary-600 shadow-sm dark:bg-gray-900 dark:text-primary-300'
                    : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
                }`}
              >
                <UserPlus className="h-4 w-4" />
                Inscription
              </button>
            </div>

            <div className="relative mt-8 h-[320px] overflow-hidden">
              <div
                className={`transition-[opacity,transform] duration-500 ease-in ${
                  authMode === 'login'
                    ? 'relative opacity-100 translate-y-0'
                    : 'absolute inset-0 opacity-0 -translate-y-6 scale-95 pointer-events-none'
                }`}
              >
                <form onSubmit={handleLogin} className="flex h-full flex-col justify-between gap-6">
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        Email
                      </label>
                      <input
                        type="email"
                        value={loginEmail}
                        onChange={(e) => setLoginEmail(e.target.value)}
                        required
                        placeholder="mon.email@exemple.fr"
                        className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200 dark:border-gray-600 dark:bg-gray-800 dark:text-white dark:focus:border-primary-400 dark:focus:ring-primary-700/30"
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        Mot de passe
                      </label>
                      <input
                        type="password"
                        value={loginPassword}
                        onChange={(e) => setLoginPassword(e.target.value)}
                        required
                        placeholder="••••••••"
                        className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200 dark:border-gray-600 dark:bg-gray-800 dark:text-white dark:focus:border-primary-400 dark:focus:ring-primary-700/30"
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={loginLoading}
                    className="w-full rounded-lg bg-primary-600 py-2 font-semibold text-white shadow-sm transition-colors duration-300 hover:bg-primary-700 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {loginLoading ? 'Connexion…' : 'Se connecter'}
                  </button>
                </form>
              </div>

              <div
                className={`transition-[opacity,transform] duration-700 ease-out ${
                  authMode === 'register'
                    ? 'relative opacity-100 translate-y-0'
                    : 'absolute inset-0 opacity-0 translate-y-6 scale-95 pointer-events-none'
                }`}
              >
                <form onSubmit={handleRegister} className="flex h-full flex-col justify-between gap-6">
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        Email
                      </label>
                      <input
                        type="email"
                        value={registerEmail}
                        onChange={(e) => setRegisterEmail(e.target.value)}
                        required
                        placeholder="mon.email@exemple.fr"
                        className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200 dark:border-gray-600 dark:bg-gray-800 dark:text-white dark:focus:border-primary-400 dark:focus:ring-primary-700/30"
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        Nom d'utilisateur
                      </label>
                      <input
                        type="text"
                        value={registerUsername}
                        onChange={(e) => setRegisterUsername(e.target.value)}
                        required
                        minLength={3}
                        placeholder="Votre pseudo"
                        className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200 dark:border-gray-600 dark:bg-gray-800 dark:text-white dark:focus:border-primary-400 dark:focus:ring-primary-700/30"
                      />
                    </div>

                    <div className="space-y-2">
                      <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                        Mot de passe
                      </label>
                      <input
                        type="password"
                        value={registerPassword}
                        onChange={(e) => setRegisterPassword(e.target.value)}
                        required
                        minLength={6}
                        placeholder="••••••••"
                        className="w-full rounded-lg border border-gray-300 bg-white px-4 py-2 text-gray-900 shadow-sm focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-200 dark:border-gray-600 dark:bg-gray-800 dark:text-white dark:focus:border-primary-400 dark:focus:ring-primary-700/30"
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={registerLoading}
                    className="w-full rounded-lg bg-primary-600 py-2 font-semibold text-white shadow-sm transition-colors duration-300 hover:bg-primary-700 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {registerLoading ? 'Inscription…' : "S'inscrire"}
                  </button>
                </form>
              </div>
            </div>

            <p className="mt-6 text-center text-xs text-gray-500 transition-opacity duration-700 ease-in-out dark:text-gray-400">
              La création de compte est gratuite et vos informations restent confidentielles.
            </p>
          </div>
        </div>
      </section>

      <section className="rounded-lg bg-primary-600 py-16 text-white dark:bg-primary-800">
        <div className="mx-auto grid max-w-5xl gap-8 px-4 text-center md:grid-cols-3">
          <div>
            <div className="text-4xl font-bold">15min</div>
            <div className="text-primary-100">Mise à jour automatique</div>
          </div>
          <div>
            <div className="text-4xl font-bold">24/7</div>
            <div className="text-primary-100">Surveillance continue</div>
          </div>
          <div>
            <div className="text-4xl font-bold">100%</div>
            <div className="text-primary-100">Gratuit et open source</div>
          </div>
        </div>
      </section>
    </div>
  )
}

function HeroBullet({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <li className="flex items-start gap-3 rounded-xl bg-white/70 p-3 shadow-sm ring-1 ring-gray-200/50 backdrop-blur transition-all duration-500 ease-in-out hover:-translate-y-0.5 hover:shadow-lg dark:bg-gray-900/70 dark:ring-gray-700/50">
      <span className="mt-1 inline-flex h-7 w-7 items-center justify-center rounded-full bg-primary-100 text-primary-600 dark:bg-primary-500/20 dark:text-primary-200">
        {icon}
      </span>
      <div>
        <p className="text-sm font-semibold text-gray-900 dark:text-white">{title}</p>
        <p className="text-sm text-gray-600 dark:text-gray-300">{description}</p>
      </div>
    </li>
  )
}
