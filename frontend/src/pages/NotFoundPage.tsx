import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return (
    <div className="text-center py-16">
      <h1 className="text-6xl font-bold text-gray-900 dark:text-white mb-4">404</h1>
      <p className="text-xl text-gray-600 dark:text-gray-300 mb-8">Page non trouvée</p>
      <Link to="/" className="bg-primary-600 text-white px-6 py-3 rounded-md hover:bg-primary-700">
        Retour à l'accueil
      </Link>
    </div>
  )
}
