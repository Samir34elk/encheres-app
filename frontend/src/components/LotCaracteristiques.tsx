import { Info, Car, Calendar, Gauge } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

interface LotCaracteristiquesProps {
  caracteristiques: Record<string, any> | null
  professionnel?: boolean
  priceReserve?: number | null
}

type VehicleFieldConfig = {
  label: string
  icon: LucideIcon | null
  format?: (v: any) => string
}

// Champs importants pour les véhicules
const vehicleFields: Record<string, VehicleFieldConfig> = {
  vehicle_brand: { label: 'Marque', icon: Car },
  vehicle_model: { label: 'Modèle', icon: Car },
  vehicle_mileage: {
    label: 'Kilométrage',
    icon: Gauge,
    format: (v: any) => `${parseInt(v).toLocaleString()} km`
  },
  vehicle_energy_type: { label: 'Énergie', icon: null },
  date_first_registration: {
    label: 'Mise en circulation',
    icon: Calendar,
    format: (v: any) => new Date(v).toLocaleDateString('fr-FR')
  },
  vehicle_numberplate: { label: 'Immatriculation', icon: null },
  vehicle_has_a_key: {
    label: 'Clé disponible',
    icon: null,
    format: (v: any) => (v === 'Oui' ? '✅ Oui' : '❌ Non')
  },
  technical_control: {
    label: 'Contrôle technique',
    icon: null,
    format: (v: any) => (v ? '✅ Oui' : '❌ Non')
  },
  registration_certificate: {
    label: 'Carte grise',
    icon: null,
    format: (v: any) => (v === 'Oui' ? '✅ Oui' : '❌ Non')
  }
}

export default function LotCaracteristiques({
  caracteristiques,
  professionnel,
  priceReserve
}: LotCaracteristiquesProps) {
  if (!caracteristiques && !professionnel && !priceReserve) {
    return null
  }

  const displayedFields: Array<{ label: string; value: string; icon?: LucideIcon | null }> = []

  // Ajout des champs véhicules s'ils existent
  if (caracteristiques) {
    Object.entries(vehicleFields).forEach(([key, config]) => {
      const raw = caracteristiques[key]

      if (raw !== undefined && raw !== null) {
        const value = config.format ? config.format(raw) : raw
        displayedFields.push({
          label: config.label,
          value: String(value),
          icon: config.icon
        })
      }
    })
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-4">
      <div className="flex items-center gap-2 mb-3">
        <Info className="w-5 h-5 text-gray-600" />
        <h3 className="text-lg font-semibold">Caractéristiques</h3>
      </div>

      {/* Informations générales */}
      <div className="space-y-2 mb-4">
        {professionnel !== undefined && (
          <div className="flex justify-between items-center py-2 border-b">
            <span className="text-gray-600">Type d'acheteur</span>
            <span
              className={`font-medium ${
                professionnel ? 'text-orange-600' : 'text-green-600'
              }`}
            >
              {professionnel
                ? '🏢 Professionnels uniquement'
                : '👤 Particuliers autorisés'}
            </span>
          </div>
        )}

        {priceReserve != null && (
          <div className="flex justify-between items-center py-2 border-b">
            <span className="text-gray-600">Prix de réserve</span>
            <span className="font-medium text-blue-600">
              {priceReserve.toLocaleString()} €
            </span>
          </div>
        )}
      </div>

      {/* Caractéristiques techniques */}
      {displayedFields.length > 0 && (
        <div className="space-y-2">
          <h4 className="font-medium text-gray-700 mb-2">Détails techniques</h4>
          {displayedFields.map((field, index) => (
            <div
              key={index}
              className="flex justify-between items-center py-2 border-b last:border-b-0"
            >
              <div className="flex items-center gap-2">
                {field.icon && (
                  <field.icon className="w-4 h-4 text-gray-400" />
                )}
                <span className="text-gray-600">{field.label}</span>
              </div>
              <span className="font-medium text-gray-900">
                {field.value}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Autres caractéristiques */}
      {caracteristiques &&
        Object.keys(caracteristiques).length > displayedFields.length && (
          <details className="mt-4">
            <summary className="cursor-pointer text-blue-600 hover:text-blue-700 font-medium">
              Voir toutes les caractéristiques (
              {Object.keys(caracteristiques).length})
            </summary>
            <div className="mt-3 space-y-1 max-h-60 overflow-y-auto">
              {Object.entries(caracteristiques).map(([key, value], index) => (
                <div
                  key={index}
                  className="text-sm py-1 border-b last:border-b-0"
                >
                  <span className="text-gray-500">{key}:</span>
                  <span className="ml-2 text-gray-700">
                    {String(value)}
                  </span>
                </div>
              ))}
            </div>
          </details>
        )}
    </div>
  )
}
