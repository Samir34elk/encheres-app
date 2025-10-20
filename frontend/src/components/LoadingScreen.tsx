export default function LoadingScreen() {
  return (
    <div className="flex h-screen w-full items-center justify-center bg-gray-50 dark:bg-gray-900">
      <div className="flex items-center gap-3 rounded-full border border-gray-200 bg-white px-5 py-3 shadow-sm dark:border-gray-700 dark:bg-gray-800">
        <span className="h-3 w-3 animate-ping rounded-full bg-primary-500" />
        <span className="text-sm font-medium text-gray-700 dark:text-gray-200">
          Chargement de vos informations…
        </span>
      </div>
    </div>
  )
}
