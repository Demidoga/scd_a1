import { useEffect, useState } from 'react'
import { api, ApiError } from '../api/client'
import type { StatsResponse } from '../api/types'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { ErrorMessage } from '../components/ErrorMessage'

function BreakdownList({ title, data }: { title: string; data: Record<string, number> }) {
  const entries = Object.entries(data).sort((a, b) => b[1] - a[1])
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4">
      <h3 className="text-sm font-semibold text-slate-700">{title}</h3>
      {entries.length === 0 ? (
        <p className="mt-2 text-sm text-slate-400">No data yet.</p>
      ) : (
        <ul className="mt-3 space-y-1.5">
          {entries.map(([key, value]) => (
            <li key={key} className="flex items-center justify-between text-sm">
              <span className="capitalize text-slate-600">{key.replace('_', ' ')}</span>
              <span className="font-medium text-slate-900">{value}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

export function StatsPage() {
  const [stats, setStats] = useState<StatsResponse | null>(null)
  const [cacheStatus, setCacheStatus] = useState<'HIT' | 'MISS' | 'UNKNOWN' | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const result = await api.getStats()
      setStats(result.stats)
      setCacheStatus(result.cacheStatus)
    } catch (err) {
      setError(err instanceof ApiError ? err.body?.detail ?? err.message : 'Failed to load statistics.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-slate-900">Statistics</h1>
        <button
          type="button"
          onClick={load}
          className="rounded-md border border-slate-300 px-3 py-1.5 text-sm font-medium text-slate-700 hover:bg-slate-50"
        >
          Refresh
        </button>
      </div>

      {loading && <LoadingSpinner label="Loading statistics…" />}
      {error && (
        <div className="mt-4">
          <ErrorMessage message={error} />
        </div>
      )}

      {stats && !loading && (
        <>
          <div className="mt-4 flex items-center gap-3">
            <p className="text-3xl font-semibold text-slate-900">{stats.total}</p>
            <p className="text-sm text-slate-500">total complaints</p>
            {cacheStatus && (
              <span
                data-testid="cache-status"
                className={`ml-auto rounded-full px-2.5 py-0.5 text-xs font-medium ${
                  cacheStatus === 'HIT'
                    ? 'bg-green-100 text-green-800'
                    : cacheStatus === 'MISS'
                      ? 'bg-slate-100 text-slate-600'
                      : 'bg-slate-100 text-slate-400'
                }`}
              >
                X-Cache: {cacheStatus}
              </span>
            )}
          </div>

          <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
            <BreakdownList title="By status" data={stats.by_status} />
            <BreakdownList title="By category" data={stats.by_category} />
            <BreakdownList title="By priority" data={stats.by_priority} />
          </div>
        </>
      )}
    </div>
  )
}
