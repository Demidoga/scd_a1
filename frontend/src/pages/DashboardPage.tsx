import { useCallback, useEffect, useState } from 'react'
import { api, ApiError } from '../api/client'
import type { ComplaintResponse, Status } from '../api/types'
import { FilterBar, type Filters } from '../components/FilterBar'
import { Pagination } from '../components/Pagination'
import { LoadingSpinner } from '../components/LoadingSpinner'
import { ErrorMessage } from '../components/ErrorMessage'
import { StatusBadge } from '../components/StatusBadge'
import { PriorityBadge } from '../components/PriorityBadge'
import { StatusTransitionActions } from '../components/StatusTransitionActions'

const PAGE_SIZE = 20

export function DashboardPage() {
  const [filters, setFilters] = useState<Filters>({})
  const [page, setPage] = useState(1)
  const [items, setItems] = useState<ComplaintResponse[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [transitionError, setTransitionError] = useState<string | null>(null)
  const [pendingId, setPendingId] = useState<string | null>(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await api.listComplaints({ ...filters, page, page_size: PAGE_SIZE })
      setItems(result.items)
      setTotal(result.total)
    } catch (err) {
      setError(err instanceof ApiError ? err.body?.detail ?? err.message : 'Failed to load complaints.')
    } finally {
      setLoading(false)
    }
  }, [filters, page])

  useEffect(() => {
    load()
  }, [load])

  function handleFiltersChange(next: Filters) {
    setFilters(next)
    setPage(1)
  }

  async function handleTransition(id: string, target: Status) {
    setPendingId(id)
    setTransitionError(null)
    try {
      const updated = await api.updateComplaintStatus(id, { status: target })
      setItems((prev) => prev.map((c) => (c.id === id ? updated : c)))
    } catch (err) {
      if (err instanceof ApiError) {
        // Render the backend's message verbatim (docs/architecture/backend.md §3.3) —
        // never replace a 409 with a generic client-side string.
        setTransitionError(err.body?.detail ?? err.message)
      } else {
        setTransitionError('Failed to update status.')
      }
    } finally {
      setPendingId(null)
    }
  }

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-zinc-50">
            Operations dashboard
          </h1>
          <p className="mt-1.5 text-sm text-zinc-400">
            <span className="font-medium text-zinc-200 tabular-nums">{total}</span> complaint
            {total === 1 ? '' : 's'} matching current filters
          </p>
        </div>
      </div>

      <div className="mt-5">
        <FilterBar filters={filters} onChange={handleFiltersChange} />
      </div>

      {transitionError && (
        <div className="mt-4">
          <ErrorMessage message={transitionError} />
        </div>
      )}

      {error && (
        <div className="mt-4">
          <ErrorMessage message={error} />
        </div>
      )}

      {loading ? (
        <LoadingSpinner label="Loading complaints…" />
      ) : items.length === 0 ? (
        <div className="mt-4 flex flex-col items-center gap-1.5 rounded-xl border border-dashed border-zinc-700 py-16 text-center">
          <p className="text-sm font-medium text-zinc-300">No complaints match these filters</p>
          <p className="text-sm text-zinc-500">Try adjusting or clearing the filters above.</p>
        </div>
      ) : (
        <div className="mt-4 overflow-hidden rounded-xl border border-zinc-800 bg-zinc-900">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-zinc-800 text-sm">
              <thead className="bg-zinc-800/40">
                <tr>
                  <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-zinc-400">
                    Complaint
                  </th>
                  <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-zinc-400">
                    Location
                  </th>
                  <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-zinc-400">
                    Category
                  </th>
                  <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-zinc-400">
                    Priority
                  </th>
                  <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-zinc-400">
                    Status
                  </th>
                  <th className="px-4 py-2.5 text-left text-xs font-semibold uppercase tracking-wide text-zinc-400">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/60">
                {items.map((c) => (
                  <tr key={c.id} className="transition-colors hover:bg-zinc-800/40">
                    <td className="max-w-xs px-4 py-3 text-zinc-300">
                      <p className="truncate" title={c.text}>
                        {c.text}
                      </p>
                    </td>
                    <td className="px-4 py-3 text-zinc-500">{c.location}</td>
                    <td className="px-4 py-3 capitalize text-zinc-300">{c.category}</td>
                    <td className="px-4 py-3">
                      <PriorityBadge priority={c.priority} />
                    </td>
                    <td className="px-4 py-3">
                      <StatusBadge status={c.status} />
                    </td>
                    <td className="px-4 py-3">
                      <StatusTransitionActions
                        status={c.status}
                        disabled={pendingId === c.id}
                        onTransition={(target) => handleTransition(c.id, target)}
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <Pagination page={page} pageSize={PAGE_SIZE} total={total} onPageChange={setPage} />
    </div>
  )
}
