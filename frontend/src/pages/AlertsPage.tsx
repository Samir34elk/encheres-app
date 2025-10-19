import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Bell, Trash2, Edit2, Check, X, Plus } from 'lucide-react'
import api from '../services/api'
import toast from 'react-hot-toast'

interface Alert {
  id: number
  lot_id: number
  lot_number: number
  lot_title: string
  lot_price: number | null
  alert_type: 'price_drop' | 'price_below' | 'any_change' | 'price_change'
  target_price: number | null
  is_active: boolean
  created_at: string
  last_triggered: string | null
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [loading, setLoading] = useState(true)
  const [editingAlert, setEditingAlert] = useState<number | null>(null)
  const [editAlertType, setEditAlertType] = useState<Alert['alert_type']>('any_change')
  const [editTargetPrice, setEditTargetPrice] = useState<string>('')

  const alertTypeOptions: Array<{
    value: Alert['alert_type']
    label: string
    helper: string
    disabled?: boolean
  }> = [
    {
      value: 'any_change',
      label: 'Nouvelle enchère ou mise à jour',
      helper: 'Recevez un message dès qu\'une enchère bouge ou qu\'un détail change.'
    },
    {
      value: 'price_below',
      label: 'Prix sous mon budget cible',
      helper: 'Soyez alerté tant que le lot reste sous le seuil que vous fixez.'
    },
    {
      value: 'price_drop',
      label: 'Prix revu à la baisse',
      helper: 'Idéal pour les ventes dégressives ou les rabais de dernière minute.'
    },
    {
      value: 'price_change',
      label: 'Variation de prix (héritage)',
      helper: 'Préférence conservée depuis l\'ancienne version de vos alertes.',
      disabled: true
    }
  ]

  useEffect(() => {
    fetchAlerts()
  }, [])

  const fetchAlerts = async () => {
    try {
      setLoading(true)
      const { data } = await api.get('/alerts')
      setAlerts(data?.items || [])
    } catch (error) {
      console.error('Failed to fetch alerts:', error)
      toast.error('Erreur lors du chargement des alertes')
    } finally {
      setLoading(false)
    }
  }

  const deleteAlert = async (alertId: number) => {
    try {
      await api.delete(`/alerts/${alertId}`)
      setAlerts(alerts.filter(a => a.id !== alertId))
      toast.success('Alerte supprimée')
    } catch (error) {
      console.error('Failed to delete alert:', error)
      toast.error('Erreur lors de la suppression')
    }
  }

  const toggleAlert = async (alert: Alert) => {
    try {
      await api.patch(`/alerts/${alert.id}`, { is_active: !alert.is_active })
      setAlerts(alerts.map(a =>
        a.id === alert.id ? { ...a, is_active: !a.is_active } : a
      ))
      toast.success(alert.is_active ? 'Alerte désactivée' : 'Alerte activée')
    } catch (error) {
      console.error('Failed to toggle alert:', error)
      toast.error('Erreur lors de la modification')
    }
  }

  const startEditAlert = (alert: Alert) => {
    setEditingAlert(alert.id)
    setEditAlertType(alert.alert_type)
    setEditTargetPrice(alert.target_price?.toString() || '')
  }

  const saveAlert = async (alertId: number) => {
    try {
      const updateData: any = { alert_type: editAlertType }
      if (editAlertType === 'price_below' && editTargetPrice) {
        updateData.target_price = Number(editTargetPrice)
      } else {
        updateData.target_price = null
      }

      await api.patch(`/alerts/${alertId}`, updateData)
      setAlerts(alerts.map(a =>
        a.id === alertId
          ? { ...a, alert_type: editAlertType, target_price: updateData.target_price }
          : a
      ))
      setEditingAlert(null)
      toast.success('Alerte mise à jour')
    } catch (error) {
      console.error('Failed to update alert:', error)
      toast.error('Erreur lors de la mise à jour')
    }
  }

  const getAlertTypeLabel = (type: string) => {
    switch (type) {
      case 'price_below':
        return 'Prix sous mon budget'
      case 'price_drop':
        return 'Prix revu à la baisse'
      case 'any_change':
        return 'Nouvelle enchère ou mise à jour'
      case 'price_change':
        return 'Variation de prix'
      default:
        return type
    }
  }

  const getAlertTypeBadge = (type: string) => {
    switch (type) {
      case 'price_below':
        return 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
      case 'price_drop':
        return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300'
      case 'any_change':
        return 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400'
      case 'price_change':
        return 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-300'
      default:
        return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-400'
    }
  }

  const activeAlerts = alerts.filter(a => a.is_active)
  const inactiveAlerts = alerts.filter(a => !a.is_active)

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Mes Alertes
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            {activeAlerts.length} alerte{activeAlerts.length > 1 ? 's' : ''} active{activeAlerts.length > 1 ? 's' : ''}
          </p>
        </div>

        <Link
          to="/lots"
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Créer une alerte
        </Link>
      </div>

      {/* Info Card */}
      <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-6 border border-blue-200 dark:border-blue-800">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
            <Bell className="w-6 h-6 text-blue-600 dark:text-blue-400" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
              Comment fonctionnent les alertes ?
            </h3>
            <ul className="space-y-1 text-sm text-gray-700 dark:text-gray-300">
              <li>• <strong>Nouvelle enchère</strong> : nous vous prévenons dès qu&apos;une mise bouge ou qu&apos;un détail évolue.</li>
              <li>• <strong>Prix sous mon budget</strong> : définissez un plafond et gardez un œil sur les opportunités accessibles.</li>
              <li>• <strong>Prix revu à la baisse</strong> : utile pour les ventes dégressives ou les rabais de dernière minute.</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Active Alerts */}
      {activeAlerts.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
            Alertes actives
          </h2>

          <div className="space-y-4">
            {activeAlerts.map((alert) => (
              <div
                key={alert.id}
                className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4 border border-gray-200 dark:border-gray-600"
              >
                {editingAlert === alert.id ? (
                  // Edit Mode
                  <div className="space-y-4">
                    <div className="flex items-center gap-4">
                      <div className="flex-1">
                        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                          Type d'alerte
                        </label>
                        <select
                          value={editAlertType}
                          onChange={(e) => setEditAlertType(e.target.value as Alert['alert_type'])}
                          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                        >
                          {alertTypeOptions.map(option => (
                            <option
                              key={option.value}
                              value={option.value}
                              disabled={option.disabled && option.value !== editAlertType}
                            >
                              {option.label}
                            </option>
                          ))}
                        </select>
                        <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                          {alertTypeOptions.find(option => option.value === editAlertType)?.helper}
                        </p>
                      </div>

                      {editAlertType === 'price_below' && (
                        <div className="flex-1">
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                            Prix cible (€)
                          </label>
                          <input
                            type="number"
                            value={editTargetPrice}
                            onChange={(e) => setEditTargetPrice(e.target.value)}
                            placeholder="Ex: 5000"
                            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                          />
                        </div>
                      )}
                    </div>

                    <div className="flex gap-2">
                      <button
                        onClick={() => saveAlert(alert.id)}
                        className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                      >
                        <Check className="w-4 h-4" />
                        Sauvegarder
                      </button>
                      <button
                        onClick={() => setEditingAlert(null)}
                        className="flex items-center gap-2 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
                      >
                        <X className="w-4 h-4" />
                        Annuler
                      </button>
                    </div>
                  </div>
                ) : (
                  // View Mode
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <Link
                          to={`/lots/${alert.lot_id}`}
                          className="text-lg font-semibold text-gray-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                        >
                          {alert.lot_title}
                        </Link>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getAlertTypeBadge(alert.alert_type)}`}>
                          {getAlertTypeLabel(alert.alert_type)}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mb-2">
                        {alertTypeOptions.find(option => option.value === alert.alert_type)?.helper}
                      </p>

                      <div className="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400">
                        <span>Lot #{alert.lot_number}</span>
                        {alert.lot_price !== null && (
                          <>
                            <span>•</span>
                            <span className="font-medium text-gray-900 dark:text-white">
                              Enchère actuelle&nbsp;: {alert.lot_price.toLocaleString()} €
                            </span>
                          </>
                        )}
                        {alert.target_price && (
                          <>
                            <span>•</span>
                            <span>Seuil: {alert.target_price.toLocaleString()} €</span>
                          </>
                        )}
                      </div>

                      {alert.last_triggered && (
                        <p className="text-xs text-green-600 dark:text-green-400 mt-2">
                          Dernière notification: {new Date(alert.last_triggered).toLocaleDateString('fr-FR')}
                        </p>
                      )}
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => startEditAlert(alert)}
                        className="p-2 text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded-lg transition-colors"
                        title="Modifier"
                      >
                        <Edit2 className="w-4 h-4" />
                      </button>

                      <button
                        onClick={() => toggleAlert(alert)}
                        className="p-2 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                        title="Désactiver"
                      >
                        <Bell className="w-4 h-4" />
                      </button>

                      <button
                        onClick={() => deleteAlert(alert.id)}
                        className="p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg transition-colors"
                        title="Supprimer"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Inactive Alerts */}
      {inactiveAlerts.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-6">
            Alertes désactivées
          </h2>

          <div className="space-y-3">
            {inactiveAlerts.map((alert) => (
              <div
                key={alert.id}
                className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-600 opacity-60"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <Link
                      to={`/lots/${alert.lot_id}`}
                      className="font-medium text-gray-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400"
                    >
                      {alert.lot_title}
                    </Link>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getAlertTypeBadge(alert.alert_type)}`}>
                      {getAlertTypeLabel(alert.alert_type)}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {alertTypeOptions.find(option => option.value === alert.alert_type)?.helper}
                  </p>
                  <div className="flex items-center gap-3 text-sm text-gray-500 dark:text-gray-400 mt-2">
                    {alert.target_price && (
                      <span>Seuil: {alert.target_price.toLocaleString()} €</span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => toggleAlert(alert)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
                  >
                    Réactiver
                  </button>

                  <button
                    onClick={() => deleteAlert(alert.id)}
                    className="p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/30 rounded-lg transition-colors"
                    title="Supprimer"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {alerts.length === 0 && (
        <div className="text-center py-16 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <Bell className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            Aucune alerte configurée
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            Créez des alertes pour suivre les nouvelles enchères et garder l&apos;avantage.
          </p>
          <Link
            to="/lots"
            className="inline-block px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Parcourir les lots
          </Link>
        </div>
      )}
    </div>
  )
}
