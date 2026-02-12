import { useState } from 'react'
import CopyButton from './CopyButton.jsx'

const CUSTOM_DOMAIN = import.meta.env.VITE_CUSTOM_DOMAIN
const API_URL = CUSTOM_DOMAIN || import.meta.env.VITE_API_URL

export default function ShortenForm() {
  const [longUrl, setLongUrl] = useState('')
  const [wantCustomAlias, setWantCustomAlias] = useState(false)
  const [customAlias, setCustomAlias] = useState('')
  const [wantExpiry, setWantExpiry] = useState(false)
  const [expiryDate, setExpiryDate] = useState('')
  const [shortUrl, setShortUrl] = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  const toExpiryISO = (dateStr) => {
    if (!dateStr) return null
    const d = new Date(dateStr)
    d.setHours(23, 59, 59, 0)
    return d.toISOString().replace(/\.\d{3}Z$/, 'Z')
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)
    setShortUrl(null)

    try {
      const parsed = new URL(longUrl.trim())
      if (!['http:', 'https:'].includes(parsed.protocol)) {
        setError('Invalid URL. Must start with http:// or https://')
        return
      }
    } catch {
      setError('Invalid URL. Please enter a valid URL.')
      return
    }

    if (wantCustomAlias && !customAlias.trim()) {
      setError('Please enter a custom alias')
      return
    }

    if (wantExpiry && !expiryDate) {
      setError('Please select an expiry date')
      return
    }

    setLoading(true)
    try {
      const body = {
        long_url: longUrl.trim(),
        ...(wantCustomAlias && customAlias.trim() && { custom_alias: customAlias.trim() }),
        ...(wantExpiry && expiryDate && { expiration_date: toExpiryISO(expiryDate) }),
      }

      const res = await fetch(`${API_URL}/urls`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })

      const data = await res.json()

      if (!res.ok) {
        setError(data.error || 'Something went wrong')
        return
      }

      if (CUSTOM_DOMAIN) {
        const code = data.custom_alias ?? data.short_code
        setShortUrl(`${CUSTOM_DOMAIN}/r/${code}`)
      } else {
        setShortUrl(data.short_url)
      }
    } catch (err) {
      setError(err.message || 'Failed to shorten URL. Check your API URL and network.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="w-full max-w-xl">
      <h1 className="text-2xl font-semibold text-center mb-8 text-gray-800 dark:text-gray-100">
        Shorten your URL
      </h1>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="longUrl" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Long URL
          </label>
          <input
            id="longUrl"
            type="url"
            value={longUrl}
            onChange={(e) => setLongUrl(e.target.value)}
            placeholder="https://example.com/very-long-url"
            required
            className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-500 focus:ring-2 focus:ring-teal-500 focus:border-transparent outline-none"
          />
        </div>

        <div className="flex items-center gap-2">
          <input
            id="wantAlias"
            type="checkbox"
            checked={wantCustomAlias}
            onChange={(e) => setWantCustomAlias(e.target.checked)}
            className="rounded border-gray-300 dark:border-gray-600 text-teal-600 focus:ring-teal-500"
          />
          <label htmlFor="wantAlias" className="text-sm text-gray-700 dark:text-gray-300">
            Use a custom alias
          </label>
        </div>
        {wantCustomAlias && (
          <div>
            <input
              type="text"
              value={customAlias}
              onChange={(e) => setCustomAlias(e.target.value)}
              placeholder="my-custom-link"
              className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-500 focus:ring-2 focus:ring-teal-500 focus:border-transparent outline-none"
            />
          </div>
        )}

        <div className="flex items-center gap-2">
          <input
            id="wantExpiry"
            type="checkbox"
            checked={wantExpiry}
            onChange={(e) => setWantExpiry(e.target.checked)}
            className="rounded border-gray-300 dark:border-gray-600 text-teal-600 focus:ring-teal-500"
          />
          <label htmlFor="wantExpiry" className="text-sm text-gray-700 dark:text-gray-300">
            Set expiry date
          </label>
        </div>
        {wantExpiry && (
          <div>
            <input
              type="date"
              value={expiryDate}
              onChange={(e) => setExpiryDate(e.target.value)}
              min={new Date().toISOString().slice(0, 10)}
              className="w-full px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-teal-500 focus:border-transparent outline-none"
            />
          </div>
        )}

        {error && (
          <p className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/20 px-4 py-2 rounded-lg">
            {error}
          </p>
        )}

        <button
          type="submit"
          disabled={loading}
          className="w-full py-2.5 rounded-lg bg-teal-600 hover:bg-teal-700 dark:bg-teal-500 dark:hover:bg-teal-600 text-white font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? 'Shortening...' : 'Shorten URL'}
        </button>
      </form>

      {shortUrl && (
        <div className="mt-6 p-4 rounded-lg bg-gray-100 dark:bg-gray-800 border border-gray-200 dark:border-gray-700">
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400 mb-2">Your short URL</p>
          <div className="flex flex-col sm:flex-row gap-2 items-stretch sm:items-center">
            <input
              type="text"
              value={shortUrl}
              readOnly
              className="flex-1 px-4 py-2 rounded-lg bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 text-sm"
            />
            <CopyButton text={shortUrl} />
          </div>
        </div>
      )}
    </div>
  )
}
