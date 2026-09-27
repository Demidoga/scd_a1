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
      <h1 className="text-2xl font-semibold text-slate-900">Operations dashboard</h1>

      <div className="mt-4">
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
        <p className="mt-8 text-sm text-slate-500">No complaints match these filters.</p>
      ) : (
        <div className="mt-4 overflow-x-auto rounded-lg border border-slate-200">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-3 py-2 text-left font-medium text-slate-500">Complaint</th>
                <th className="px-3 py-2 text-left font-medium text-slate-500">Location</th>
                <th className="px-3 py-2 text-left font-medium text-slate-500">Category</th>
                <th className="px-3 py-2 text-left font-medium text-slate-500">Priority</th>
                <th className="px-3 py-2 text-left font-medium text-slate-500">Status</th>
                <th className="px-3 py-2 text-left font-medium text-slate-500">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {items.map((c) => (
                <tr key={c.id}>
                  <td className="max-w-xs px-3 py-2 text-slate-700">
                    <p className="truncate" title={c.text}>
                      {c.text}
                    </p>
                  </td>
                  <td className="px-3 py-2 text-slate-500">{c.location}</td>
                  <td className="px-3 py-2 capitalize text-slate-700">{c.category}</td>
                  <td className="px-3 py-2">
                    <PriorityBadge priority={c.priority} />
                  </td>
                  <td className="px-3 py-2">
                    <StatusBadge status={c.status} />
                  </td>
                  <td className="px-3 py-2">
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
      )}

      <Pagination page={page} pageSize={PAGE_SIZE} total={total} onPageChange={setPage} />
    </div>
  )
}
