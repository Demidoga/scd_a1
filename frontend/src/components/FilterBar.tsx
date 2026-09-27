import { CATEGORIES, PRIORITIES, STATUSES } from '../api/types'
import type { Category, Priority, Status } from '../api/types'

export interface Filters {
  category?: Category
  priority?: Priority
  status?: Status
}

interface Props {
  filters: Filters
  onChange: (filters: Filters) => void
}

const selectClass =
  'mt-1 rounded-lg border border-zinc-700 bg-zinc-950 px-2.5 py-1.5 text-sm text-zinc-300 transition-colors hover:border-zinc-600 focus:border-blue-500 focus:outline-none'

export function FilterBar({ filters, onChange }: Props) {
  const hasFilters = Boolean(filters.category || filters.priority || filters.status)

  return (
    <div className="flex flex-wrap items-end gap-x-5 gap-y-3 rounded-xl border border-zinc-800 bg-zinc-900 px-4 py-3.5">
      <label className="flex flex-col text-xs font-medium text-zinc-400">
        Category
        <select
          aria-label="Filter by category"
          className={selectClass}
          value={filters.category ?? ''}
          onChange={(e) =>
            onChange({ ...filters, category: (e.target.value || undefined) as Category | undefined })
          }
        >
          <option value="">All</option>
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col text-xs font-medium text-zinc-400">
        Priority
        <select
          aria-label="Filter by priority"
          className={selectClass}
          value={filters.priority ?? ''}
          onChange={(e) =>
            onChange({ ...filters, priority: (e.target.value || undefined) as Priority | undefined })
          }
        >
          <option value="">All</option>
          {PRIORITIES.map((p) => (
            <option key={p} value={p}>
              {p}
            </option>
          ))}
        </select>
      </label>

      <label className="flex flex-col text-xs font-medium text-zinc-400">
        Status
        <select
          aria-label="Filter by status"
          className={selectClass}
          value={filters.status ?? ''}
          onChange={(e) =>
            onChange({ ...filters, status: (e.target.value || undefined) as Status | undefined })
          }
        >
          <option value="">All</option>
          {STATUSES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </label>

      {hasFilters && (
        <button
          type="button"
          onClick={() => onChange({})}
          className="text-xs font-medium text-zinc-500 underline decoration-zinc-700 underline-offset-4 transition-colors hover:text-zinc-200 hover:decoration-zinc-500"
        >
          Clear filters
        </button>
      )}
    </div>
  )
}
