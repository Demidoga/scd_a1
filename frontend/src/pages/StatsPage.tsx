import { useEffect, useState } from 'react'
import { api, ApiError } from '../api/client'
import type { StatsResponse } from '../api/types'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { ErrorMessage } from '../components/ErrorMessage'

function BreakdownList({ title, data }: { title: string; data: Record<string, number> }) {
  const entries = Object.entries(data).sort((a, b) => b[1] - a[1])
  const max = entries.length > 0 ? entries[0][1] : 0

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-900 p-5">
      <h3 className="text-sm font-semibold text-zinc-200">{title}</h3>
      {entries.length === 0 ? (
        <p className="mt-3 text-sm text-zinc-500">No data yet.</p>
      ) : (
        <ul className="mt-4 space-y-3">
          {entries.map(([key, value]) => (
            <li key={key}>
              <div className="flex items-center justify-between text-sm">
                <span className="capitalize text-zinc-400">{key.replace(/_/g, ' ')}</span>
                <span className="font-medium tabular-nums text-zinc-50">{value}</span>
              </div>
              <div className="mt-1.5 h-1 overflow-hidden rounded-full bg-zinc-800">
                <div
                  className="h-full rounded-full bg-blue-500/80"
                  style={{ width: max > 0 ? `${(value / max) * 100}%` : '0%' }}
                />
              </div>
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
        <h1 className="text-2xl font-semibold tracking-tight text-zinc-50">Statistics</h1>
        <button
          type="button"
          onClick={load}
          className="rounded-lg border border-zinc-700 bg-zinc-900 px-3.5 py-1.5 text-sm font-medium text-zinc-300 transition-colors hover:bg-zinc-800"
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
          <div className="mt-5 flex items-center gap-4 rounded-xl border border-zinc-800 bg-zinc-900 px-5 py-4">
            <p className="text-3xl font-semibold tracking-tight tabular-nums text-zinc-50">
              {stats.total}
            </p>
            <p className="text-sm text-zinc-400">total complaints</p>
            {cacheStatus && (
              <span
                data-testid="cache-status"
                className={`ml-auto inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset ${
                  cacheStatus === 'HIT'
                    ? 'bg-emerald-500/10 text-emerald-300 ring-emerald-500/25'
                    : cacheStatus === 'MISS'
                      ? 'bg-zinc-800 text-zinc-400 ring-zinc-600/20'
                      : 'bg-zinc-900 text-zinc-600 ring-zinc-700/30'
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
