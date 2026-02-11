const DEVELOPER_WEBSITE = import.meta.env.VITE_DEVELOPER_WEBSITE || '#'

export default function Footer() {
  return (
    <footer className="border-t border-gray-200 dark:border-gray-800 py-6 px-4 mt-auto">
      <div className="max-w-2xl mx-auto flex items-center justify-center">
        <p className="text-sm text-gray-600 dark:text-gray-400 text-center">
          Built by{' '}
          <a
            href={DEVELOPER_WEBSITE}
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-teal-600 dark:text-teal-400 hover:underline"
          >
            Apresh Agarwal
          </a>
        </p>
      </div>
    </footer>
  )
}
