import { Tag } from 'lucide-react'

interface LotCategoriesProps {
  categories: string[] | null
}

export default function LotCategories({ categories }: LotCategoriesProps) {
  if (!categories || categories.length === 0) {
    return null
  }

  return (
    <div className="bg-white rounded-lg shadow-sm p-4">
      <div className="flex items-center gap-2 mb-3">
        <Tag className="w-5 h-5 text-blue-600" />
        <h3 className="text-lg font-semibold">Catégories</h3>
      </div>
      <div className="flex flex-wrap gap-2">
        {categories.map((category, index) => (
          <span
            key={index}
            className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm font-medium"
          >
            {category}
          </span>
        ))}
      </div>
    </div>
  )
}
